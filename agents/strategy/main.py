"""
VolexSwarm Strategy Agent - Strategy Development and Management
Handles strategy creation, management, optimization, and performance tracking.
"""

import sys
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel, Field
import json
import time
from dataclasses import dataclass
from enum import Enum

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Strategy, Trade, PerformanceMetrics

# Initialize structured logger
logger = get_logger("strategy")

app = FastAPI(title="VolexSwarm Strategy Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients
vault_client = None
db_client = None

# Strategy status enum
class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    TESTING = "testing"

# Pydantic models
class StrategyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    strategy_type: str = Field(..., description="Type of strategy template")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    symbols: List[str] = Field(default_factory=list)
    timeframe: str = Field(default="1h")
    risk_per_trade: float = Field(default=0.01, ge=0.001, le=0.1)
    max_positions: int = Field(default=5, ge=1, le=20)
    enabled: bool = Field(default=False)

class StrategyUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    symbols: Optional[List[str]] = None
    timeframe: Optional[str] = None
    risk_per_trade: Optional[float] = Field(None, ge=0.001, le=0.1)
    max_positions: Optional[int] = Field(None, ge=1, le=20)
    enabled: Optional[bool] = None

class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    strategy_type: str
    parameters: Dict[str, Any]
    symbols: List[str]
    timeframe: str
    risk_per_trade: float
    max_positions: int
    enabled: bool
    status: StrategyStatus
    created_at: datetime
    updated_at: datetime

class PerformanceResponse(BaseModel):
    strategy_id: int
    performance: Dict[str, Any]
    last_updated: datetime

class TemplateResponse(BaseModel):
    type: str
    name: str
    description: str
    parameters: Dict[str, Any]

# Strategy templates
STRATEGY_TEMPLATES = {
    "moving_average": {
        "name": "Moving Average Crossover",
        "description": "Buy when fast moving average crosses above slow moving average, sell when it crosses below",
        "parameters": {
            "fast_period": {"type": "int", "default": 10, "min": 2, "max": 50, "description": "Fast moving average period"},
            "slow_period": {"type": "int", "default": 30, "min": 5, "max": 200, "description": "Slow moving average period"},
            "ma_type": {"type": "str", "default": "sma", "options": ["sma", "ema"], "description": "Moving average type"}
        }
    },
    "rsi": {
        "name": "RSI Strategy",
        "description": "Buy on oversold (RSI < 30), sell on overbought (RSI > 70)",
        "parameters": {
            "period": {"type": "int", "default": 14, "min": 5, "max": 50, "description": "RSI calculation period"},
            "oversold_threshold": {"type": "float", "default": 30.0, "min": 10.0, "max": 40.0, "description": "Oversold threshold"},
            "overbought_threshold": {"type": "float", "default": 70.0, "min": 60.0, "max": 90.0, "description": "Overbought threshold"}
        }
    },
    "mean_reversion": {
        "name": "Mean Reversion Strategy",
        "description": "Trade against extreme price movements expecting reversion to mean",
        "parameters": {
            "lookback_period": {"type": "int", "default": 20, "min": 10, "max": 100, "description": "Period for mean calculation"},
            "std_dev_threshold": {"type": "float", "default": 2.0, "min": 1.0, "max": 4.0, "description": "Standard deviation threshold"},
            "entry_threshold": {"type": "float", "default": 1.5, "min": 1.0, "max": 3.0, "description": "Entry threshold"}
        }
    },
    "momentum": {
        "name": "Momentum Strategy",
        "description": "Follow strong price momentum with trend-following signals",
        "parameters": {
            "momentum_period": {"type": "int", "default": 10, "min": 5, "max": 50, "description": "Momentum calculation period"},
            "strength_threshold": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.10, "description": "Momentum strength threshold"},
            "confirmation_period": {"type": "int", "default": 3, "min": 1, "max": 10, "description": "Confirmation period"}
        }
    },
    "bollinger_bands": {
        "name": "Bollinger Bands Strategy",
        "description": "Trade based on price position relative to Bollinger Bands",
        "parameters": {
            "period": {"type": "int", "default": 20, "min": 10, "max": 50, "description": "Bollinger Bands period"},
            "std_dev": {"type": "float", "default": 2.0, "min": 1.5, "max": 3.0, "description": "Standard deviation multiplier"},
            "entry_threshold": {"type": "float", "default": 0.1, "min": 0.05, "max": 0.2, "description": "Entry threshold from bands"}
        }
    }
}

class StrategyManager:
    """Manages strategy creation, validation, and lifecycle."""
    
    def __init__(self):
        self.templates = STRATEGY_TEMPLATES
    
    def validate_parameters(self, strategy_type: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate strategy parameters against template."""
        if strategy_type not in self.templates:
            return False, f"Unknown strategy type: {strategy_type}"
        
        template = self.templates[strategy_type]
        template_params = template["parameters"]
        
        for param_name, param_config in template_params.items():
            if param_name not in parameters:
                # Use default value if not provided
                parameters[param_name] = param_config["default"]
                continue
            
            value = parameters[param_name]
            param_type = param_config["type"]
            
            # Type validation
            if param_type == "int" and not isinstance(value, int):
                return False, f"Parameter {param_name} must be an integer"
            elif param_type == "float" and not isinstance(value, (int, float)):
                return False, f"Parameter {param_name} must be a number"
            elif param_type == "str" and not isinstance(value, str):
                return False, f"Parameter {param_name} must be a string"
            
            # Range validation
            if "min" in param_config and value < param_config["min"]:
                return False, f"Parameter {param_name} must be >= {param_config['min']}"
            if "max" in param_config and value > param_config["max"]:
                return False, f"Parameter {param_name} must be <= {param_config['max']}"
            
            # Options validation
            if "options" in param_config and value not in param_config["options"]:
                return False, f"Parameter {param_name} must be one of {param_config['options']}"
        
        return True, "Parameters valid"
    
    def generate_strategy_code(self, strategy_type: str, parameters: Dict[str, Any]) -> str:
        """Generate strategy code based on template and parameters."""
        if strategy_type == "moving_average":
            return self._generate_moving_average_code(parameters)
        elif strategy_type == "rsi":
            return self._generate_rsi_code(parameters)
        elif strategy_type == "mean_reversion":
            return self._generate_mean_reversion_code(parameters)
        elif strategy_type == "momentum":
            return self._generate_momentum_code(parameters)
        elif strategy_type == "bollinger_bands":
            return self._generate_bollinger_bands_code(parameters)
        else:
            return "# Strategy code generation not implemented for this type"
    
    def _generate_moving_average_code(self, params: Dict[str, Any]) -> str:
        """Generate moving average strategy code."""
        fast_period = params.get("fast_period", 10)
        slow_period = params.get("slow_period", 30)
        ma_type = params.get("ma_type", "sma")
        
        return f'''
def generate_signals(timestamp, current_prices, positions, balance):
    """Moving Average Crossover Strategy"""
    signals = []
    
    for symbol in current_prices:
        # Get historical data for symbol
        historical_data = get_historical_data(symbol, timeframe, lookback_period)
        
        if len(historical_data) < {slow_period}:
            continue
        
        # Calculate moving averages
        if "{ma_type}" == "sma":
            fast_ma = calculate_sma(historical_data['close'], {fast_period})
            slow_ma = calculate_sma(historical_data['close'], {slow_period})
        else:
            fast_ma = calculate_ema(historical_data['close'], {fast_period})
            slow_ma = calculate_ema(historical_data['close'], {slow_period})
        
        # Generate signals
        if fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]:
            # Golden cross - buy signal
            signals.append({{
                'symbol': symbol,
                'action': 'buy',
                'strength': 0.8,
                'reason': f'Golden cross: {{fast_ma[-1]:.2f}} > {{slow_ma[-1]:.2f}}'
            }})
        elif fast_ma[-1] < slow_ma[-1] and fast_ma[-2] >= slow_ma[-2]:
            # Death cross - sell signal
            signals.append({{
                'symbol': symbol,
                'action': 'sell',
                'strength': 0.8,
                'reason': f'Death cross: {{fast_ma[-1]:.2f}} < {{slow_ma[-1]:.2f}}'
            }})
    
    return signals
'''
    
    def _generate_rsi_code(self, params: Dict[str, Any]) -> str:
        """Generate RSI strategy code."""
        period = params.get("period", 14)
        oversold = params.get("oversold_threshold", 30.0)
        overbought = params.get("overbought_threshold", 70.0)
        
        return f'''
def generate_signals(timestamp, current_prices, positions, balance):
    """RSI Strategy"""
    signals = []
    
    for symbol in current_prices:
        # Get historical data for symbol
        historical_data = get_historical_data(symbol, timeframe, lookback_period)
        
        if len(historical_data) < {period}:
            continue
        
        # Calculate RSI
        rsi = calculate_rsi(historical_data['close'], {period})
        current_rsi = rsi[-1]
        
        # Generate signals
        if current_rsi < {oversold}:
            signals.append({{
                'symbol': symbol,
                'action': 'buy',
                'strength': 0.7,
                'reason': f'RSI oversold: {{current_rsi:.2f}} < {oversold}'
            }})
        elif current_rsi > {overbought}:
            signals.append({{
                'symbol': symbol,
                'action': 'sell',
                'strength': 0.7,
                'reason': f'RSI overbought: {{current_rsi:.2f}} > {overbought}'
            }})
    
    return signals
'''
    
    def _generate_mean_reversion_code(self, params: Dict[str, Any]) -> str:
        """Generate mean reversion strategy code."""
        lookback = params.get("lookback_period", 20)
        std_threshold = params.get("std_dev_threshold", 2.0)
        entry_threshold = params.get("entry_threshold", 1.5)
        
        return f'''
def generate_signals(timestamp, current_prices, positions, balance):
    """Mean Reversion Strategy"""
    signals = []
    
    for symbol in current_prices:
        # Get historical data for symbol
        historical_data = get_historical_data(symbol, timeframe, lookback_period)
        
        if len(historical_data) < {lookback}:
            continue
        
        # Calculate mean and standard deviation
        prices = historical_data['close'][-{lookback}:]
        mean_price = np.mean(prices)
        std_price = np.std(prices)
        current_price = prices[-1]
        
        # Calculate z-score
        z_score = (current_price - mean_price) / (std_price + 1e-10)
        
        # Generate signals
        if z_score < -{entry_threshold}:
            signals.append({{
                'symbol': symbol,
                'action': 'buy',
                'strength': 0.6,
                'reason': f'Mean reversion buy: z-score {{z_score:.2f}} < -{entry_threshold}'
            }})
        elif z_score > {entry_threshold}:
            signals.append({{
                'symbol': symbol,
                'action': 'sell',
                'strength': 0.6,
                'reason': f'Mean reversion sell: z-score {{z_score:.2f}} > {entry_threshold}'
            }})
    
    return signals
'''
    
    def _generate_momentum_code(self, params: Dict[str, Any]) -> str:
        """Generate momentum strategy code."""
        momentum_period = params.get("momentum_period", 10)
        strength_threshold = params.get("strength_threshold", 0.02)
        confirmation_period = params.get("confirmation_period", 3)
        
        return f'''
def generate_signals(timestamp, current_prices, positions, balance):
    """Momentum Strategy"""
    signals = []
    
    for symbol in current_prices:
        # Get historical data for symbol
        historical_data = get_historical_data(symbol, timeframe, lookback_period)
        
        if len(historical_data) < {momentum_period + confirmation_period}:
            continue
        
        # Calculate momentum
        prices = historical_data['close']
        momentum = (prices[-1] / prices[-{momentum_period}] - 1)
        
        # Check for confirmation
        recent_momentum = (prices[-1] / prices[-{confirmation_period}] - 1)
        
        # Generate signals
        if momentum > {strength_threshold} and recent_momentum > 0:
            signals.append({{
                'symbol': symbol,
                'action': 'buy',
                'strength': 0.7,
                'reason': f'Momentum buy: {{momentum:.3f}} > {strength_threshold}'
            }})
        elif momentum < -{strength_threshold} and recent_momentum < 0:
            signals.append({{
                'symbol': symbol,
                'action': 'sell',
                'strength': 0.7,
                'reason': f'Momentum sell: {{momentum:.3f}} < -{strength_threshold}'
            }})
    
    return signals
'''
    
    def _generate_bollinger_bands_code(self, params: Dict[str, Any]) -> str:
        """Generate Bollinger Bands strategy code."""
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2.0)
        entry_threshold = params.get("entry_threshold", 0.1)
        
        return f'''
def generate_signals(timestamp, current_prices, positions, balance):
    """Bollinger Bands Strategy"""
    signals = []
    
    for symbol in current_prices:
        # Get historical data for symbol
        historical_data = get_historical_data(symbol, timeframe, lookback_period)
        
        if len(historical_data) < {period}:
            continue
        
        # Calculate Bollinger Bands
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(
            historical_data['close'], {period}, {std_dev}
        )
        
        current_price = historical_data['close'][-1]
        band_width = bb_upper[-1] - bb_lower[-1]
        
        # Calculate position within bands
        if band_width > 0:
            position = (current_price - bb_lower[-1]) / band_width
        else:
            position = 0.5
        
        # Generate signals
        if position < {entry_threshold}:
            signals.append({{
                'symbol': symbol,
                'action': 'buy',
                'strength': 0.6,
                'reason': f'BB buy: position {{position:.3f}} < {entry_threshold}'
            }})
        elif position > (1 - {entry_threshold}):
            signals.append({{
                'symbol': symbol,
                'action': 'sell',
                'strength': 0.6,
                'reason': f'BB sell: position {{position:.3f}} > {1 - entry_threshold}'
            }})
    
    return signals
'''

# Initialize strategy manager
strategy_manager = StrategyManager()

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    global vault_client, db_client
    
    try:
        vault_client = get_vault_client()
        db_client = get_db_client()
        logger.info("Strategy Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Strategy Agent: {e}")

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"agent": "strategy", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "agent": "strategy",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Database health check
    try:
        if db_client:
            db_health = db_health_check()
            health_status["checks"]["database"] = db_health
        else:
            health_status["checks"]["database"] = {"status": "unavailable"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "error", "error": str(e)}
    
    # Vault health check
    try:
        if vault_client:
            vault_health = vault_client.sys.read_health_status()
            health_status["checks"]["vault"] = {"status": "healthy"}
        else:
            health_status["checks"]["vault"] = {"status": "unavailable"}
    except Exception as e:
        health_status["checks"]["vault"] = {"status": "error", "error": str(e)}
    
    # Check if any critical services are down
    critical_errors = [check for check in health_status["checks"].values() 
                      if check.get("status") == "error"]
    
    if critical_errors:
        health_status["status"] = "unhealthy"
    
    return health_status

@app.get("/templates", response_model=List[TemplateResponse])
async def get_strategy_templates():
    """Get available strategy templates."""
    templates = []
    for template_type, template_data in STRATEGY_TEMPLATES.items():
        templates.append(TemplateResponse(
            type=template_type,
            name=template_data["name"],
            description=template_data["description"],
            parameters=template_data["parameters"]
        ))
    return templates

@app.get("/templates/{template_type}", response_model=TemplateResponse)
async def get_template_details(template_type: str):
    """Get details for a specific strategy template."""
    if template_type not in STRATEGY_TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template {template_type} not found")
    
    template_data = STRATEGY_TEMPLATES[template_type]
    return TemplateResponse(
        type=template_type,
        name=template_data["name"],
        description=template_data["description"],
        parameters=template_data["parameters"]
    )

@app.post("/strategies/create", response_model=Dict[str, Any])
async def create_strategy(request: StrategyCreateRequest):
    """Create a new trading strategy."""
    try:
        # Validate parameters
        is_valid, error_message = strategy_manager.validate_parameters(
            request.strategy_type, request.parameters
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Generate strategy code
        strategy_code = strategy_manager.generate_strategy_code(
            request.strategy_type, request.parameters
        )
        
        # Create strategy in database
        if db_client:
            strategy = Strategy(
                name=request.name,
                description=request.description,
                agent_name="strategy",
                parameters={
                    "strategy_type": request.strategy_type,
                    "parameters": request.parameters,
                    "symbols": request.symbols,
                    "timeframe": request.timeframe,
                    "risk_per_trade": request.risk_per_trade,
                    "max_positions": request.max_positions,
                    "enabled": request.enabled,
                    "code": strategy_code
                },
                is_active=request.enabled
            )
            
            db_client.add(strategy)
            db_client.commit()
            db_client.refresh(strategy)
            
            logger.info(f"Created strategy: {request.name} (ID: {strategy.id})")
            
            return {
                "strategy_id": strategy.id,
                "name": request.name,
                "status": "created",
                "message": "Strategy created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Database not available")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create strategy: {str(e)}")

@app.get("/strategies", response_model=Dict[str, Any])
async def list_strategies(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of strategies to return")
):
    """List all strategies with optional filtering."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        query = db_client.query(Strategy)
        
        if status:
            if status == "active":
                query = query.filter(Strategy.is_active == True)
            elif status == "inactive":
                query = query.filter(Strategy.is_active == False)
        
        strategies = query.limit(limit).all()
        
        strategy_list = []
        for strategy in strategies:
            params = strategy.parameters or {}
            strategy_list.append({
                "id": strategy.id,
                "name": strategy.name,
                "description": strategy.description,
                "strategy_type": params.get("strategy_type", "unknown"),
                "symbols": params.get("symbols", []),
                "timeframe": params.get("timeframe", "1h"),
                "enabled": params.get("enabled", False),
                "status": StrategyStatus.ACTIVE if strategy.is_active else StrategyStatus.PAUSED,
                "created_at": strategy.created_at,
                "updated_at": strategy.updated_at
            })
        
        return {"strategies": strategy_list, "count": len(strategy_list)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list strategies: {str(e)}")

@app.get("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def get_strategy_details(strategy_id: int):
    """Get detailed information about a specific strategy."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        strategy = db_client.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        params = strategy.parameters or {}
        
        return {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": params.get("strategy_type", "unknown"),
            "parameters": params.get("parameters", {}),
            "symbols": params.get("symbols", []),
            "timeframe": params.get("timeframe", "1h"),
            "risk_per_trade": params.get("risk_per_trade", 0.01),
            "max_positions": params.get("max_positions", 5),
            "enabled": params.get("enabled", False),
            "status": StrategyStatus.ACTIVE if strategy.is_active else StrategyStatus.PAUSED,
            "code": params.get("code", ""),
            "created_at": strategy.created_at,
            "updated_at": strategy.updated_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy details: {str(e)}")

@app.put("/strategies/{strategy_id}", response_model=Dict[str, Any])
async def update_strategy(strategy_id: int, request: StrategyUpdateRequest):
    """Update an existing strategy."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        strategy = db_client.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Update fields
        if request.name is not None:
            strategy.name = request.name
        if request.description is not None:
            strategy.description = request.description
        
        # Update parameters
        current_params = strategy.parameters or {}
        if request.parameters is not None:
            current_params["parameters"] = request.parameters
        if request.symbols is not None:
            current_params["symbols"] = request.symbols
        if request.timeframe is not None:
            current_params["timeframe"] = request.timeframe
        if request.risk_per_trade is not None:
            current_params["risk_per_trade"] = request.risk_per_trade
        if request.max_positions is not None:
            current_params["max_positions"] = request.max_positions
        if request.enabled is not None:
            current_params["enabled"] = request.enabled
            strategy.is_active = request.enabled
        
        strategy.parameters = current_params
        strategy.updated_at = datetime.utcnow()
        
        db_client.commit()
        
        logger.info(f"Updated strategy: {strategy.name} (ID: {strategy_id})")
        
        return {
            "strategy_id": strategy_id,
            "status": "updated",
            "message": "Strategy updated successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update strategy: {str(e)}")

@app.get("/strategies/{strategy_id}/performance", response_model=PerformanceResponse)
async def get_strategy_performance(strategy_id: int):
    """Get performance metrics for a strategy."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        strategy = db_client.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Calculate performance metrics (placeholder implementation)
        # In a real implementation, this would query actual trade data
        performance = {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_trades": 0,
            "avg_trade_duration": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return PerformanceResponse(
            strategy_id=strategy_id,
            performance=performance,
            last_updated=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get strategy performance: {str(e)}")

@app.post("/strategies/{strategy_id}/enable")
async def enable_strategy(strategy_id: int):
    """Enable a strategy."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        strategy = db_client.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        strategy.is_active = True
        current_params = strategy.parameters or {}
        current_params["enabled"] = True
        strategy.parameters = current_params
        strategy.updated_at = datetime.utcnow()
        
        db_client.commit()
        
        logger.info(f"Enabled strategy: {strategy.name} (ID: {strategy_id})")
        
        return {"status": "enabled", "message": "Strategy enabled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to enable strategy: {str(e)}")

@app.post("/strategies/{strategy_id}/disable")
async def disable_strategy(strategy_id: int):
    """Disable a strategy."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        strategy = db_client.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        strategy.is_active = False
        current_params = strategy.parameters or {}
        current_params["enabled"] = False
        strategy.parameters = current_params
        strategy.updated_at = datetime.utcnow()
        
        db_client.commit()
        
        logger.info(f"Disabled strategy: {strategy.name} (ID: {strategy_id})")
        
        return {"status": "disabled", "message": "Strategy disabled successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable strategy: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
