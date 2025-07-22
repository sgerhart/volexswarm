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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    global vault_client, db_client
    
    # Startup
    try:
        vault_client = get_vault_client()
        logger.info("Vault client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Vault client: {e}")
        vault_client = None
    
    try:
        db_client = get_db_client()
        logger.info("Database client initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize database client: {e}")
        db_client = None
    
    if vault_client or db_client:
        logger.info("Strategy Agent initialized with available services")
    else:
        logger.warning("Strategy Agent initialized without external services")
    
    yield
    
    # Shutdown
    logger.info("Strategy Agent shutting down")

app = FastAPI(title="VolexSwarm Strategy Agent", version="1.0.0", lifespan=lifespan)

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
            "strength_threshold": {"type": "float", "default": 0.02, "min": 0.01, "max": 0.1, "description": "Momentum strength threshold"},
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
    },
    "composite": {
        "name": "Composite Strategy",
        "description": "Combine multiple strategies with different weights and logic",
        "parameters": {
            "strategies": {"type": "list", "description": "List of strategies to combine"},
            "combination_logic": {"type": "str", "default": "weighted", "options": ["weighted", "voting", "sequential"], "description": "How to combine strategies"},
            "weights": {"type": "dict", "description": "Weights for each strategy (for weighted combination)"},
            "voting_threshold": {"type": "float", "default": 0.5, "min": 0.1, "max": 0.9, "description": "Threshold for voting combination"}
        }
    }
}

# Strategy performance comparison
class StrategyComparisonRequest(BaseModel):
    """Request model for strategy comparison."""
    strategy_ids: List[int] = Field(..., min_items=2, max_items=10, description="List of strategy IDs to compare")
    metrics: List[str] = Field(default=["total_return", "sharpe_ratio", "max_drawdown", "win_rate"], 
                              description="Metrics to compare")
    timeframe: str = Field(default="30d", description="Timeframe for comparison")

class StrategyComparisonResponse(BaseModel):
    """Response model for strategy comparison."""
    comparison_id: str
    strategies: List[Dict[str, Any]]
    metrics: Dict[str, List[float]]
    rankings: Dict[str, List[int]]
    created_at: datetime

# Strategy risk metrics
class RiskMetricsRequest(BaseModel):
    """Request model for risk metrics calculation."""
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99, description="Confidence level for VaR/CVaR")
    timeframe: str = Field(default="30d", description="Timeframe for risk calculation")

class RiskMetricsResponse(BaseModel):
    """Response model for risk metrics."""
    strategy_id: int
    risk_metrics: Dict[str, float]
    calculated_at: datetime

# Parameter optimization
class OptimizationRequest(BaseModel):
    """Request model for parameter optimization."""
    optimization_type: str = Field(..., description="Type: genetic, walk_forward, sensitivity, adaptive")
    target_metric: str = Field(default="sharpe_ratio", description="Metric to optimize")
    max_iterations: int = Field(default=100, ge=10, le=1000, description="Maximum optimization iterations")
    population_size: int = Field(default=50, ge=10, le=200, description="Population size for genetic algorithm")

class OptimizationResponse(BaseModel):
    """Response model for parameter optimization."""
    optimization_id: str
    strategy_id: int
    optimization_type: str
    best_parameters: Dict[str, Any]
    best_score: float
    optimization_history: List[Dict[str, Any]]
    completed_at: datetime

# Add optimization methods to StrategyManager
class StrategyManager:
    def __init__(self):
        self.strategy_templates = STRATEGY_TEMPLATES

    def validate_parameters(self, strategy_type: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate strategy parameters against template requirements."""
        if strategy_type not in self.strategy_templates:
            return False, f"Unknown strategy type: {strategy_type}"
        
        template = self.strategy_templates[strategy_type]
        template_params = template.get("parameters", {})
        
        for param_name, param_config in template_params.items():
            if param_name in parameters:
                param_value = parameters[param_name]
                param_type = param_config.get("type")
                
                # Type validation
                if param_type == "int" and not isinstance(param_value, int):
                    return False, f"Parameter {param_name} must be an integer"
                elif param_type == "float" and not isinstance(param_value, (int, float)):
                    return False, f"Parameter {param_name} must be a number"
                elif param_type == "str" and not isinstance(param_value, str):
                    return False, f"Parameter {param_name} must be a string"
                
                # Range validation
                if "min" in param_config and param_value < param_config["min"]:
                    return False, f"Parameter {param_name} must be >= {param_config['min']}"
                if "max" in param_config and param_value > param_config["max"]:
                    return False, f"Parameter {param_name} must be <= {param_config['max']}"
                
                # Options validation
                if "options" in param_config and param_value not in param_config["options"]:
                    return False, f"Parameter {param_name} must be one of {param_config['options']}"
        
        return True, "Parameters are valid"

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
        elif strategy_type == "composite":
            return self._generate_composite_code(parameters)
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

    def _generate_composite_code(self, params: Dict[str, Any]) -> str:
        """Generate composite strategy code that combines multiple strategies."""
        strategies = params.get("strategies", [])
        combination_logic = params.get("combination_logic", "weighted")
        weights = params.get("weights", {})
        voting_threshold = params.get("voting_threshold", 0.5)
        
        strategy_calls = []
        for strategy in strategies:
            strategy_id = strategy.get("id")
            strategy_type = strategy.get("type")
            strategy_params = strategy.get("parameters", {})
            
            if strategy_type and strategy_type != "composite":
                strategy_calls.append(f"""
        # Strategy {strategy_id} ({strategy_type})
        try:
            strategy_{strategy_id}_signals = execute_strategy_{strategy_type}(timestamp, current_prices, positions, balance, {strategy_params})
            all_signals.extend(strategy_{strategy_id}_signals)
        except Exception as e:
            logger.warning(f"Strategy {strategy_id} failed: {{e}}")
""")
        
        if combination_logic == "weighted":
            combination_code = f"""
        # Weighted combination
        weighted_signals = {{}}
        for signal in all_signals:
            symbol = signal['symbol']
            if symbol not in weighted_signals:
                weighted_signals[symbol] = {{'buy': 0.0, 'sell': 0.0, 'reasons': []}}
            
            weight = {weights}.get(signal.get('strategy_id', 'default'), 1.0)
            weighted_signals[symbol][signal['action']] += signal['strength'] * weight
            weighted_signals[symbol]['reasons'].append(signal['reason'])
        
        # Generate final signals
        for symbol, signals in weighted_signals.items():
            if signals['buy'] > signals['sell'] and signals['buy'] > 0.5:
                final_signals.append({{
                    'symbol': symbol,
                    'action': 'buy',
                    'strength': min(signals['buy'], 1.0),
                    'reason': ' | '.join(signals['reasons'])
                }})
            elif signals['sell'] > signals['buy'] and signals['sell'] > 0.5:
                final_signals.append({{
                    'symbol': symbol,
                    'action': 'sell',
                    'strength': min(signals['sell'], 1.0),
                    'reason': ' | '.join(signals['reasons'])
                }})
"""
        elif combination_logic == "voting":
            combination_code = f"""
        # Voting combination
        symbol_votes = {{}}
        for signal in all_signals:
            symbol = signal['symbol']
            if symbol not in symbol_votes:
                symbol_votes[symbol] = {{'buy': 0, 'sell': 0, 'reasons': []}}
            
            symbol_votes[symbol][signal['action']] += 1
            symbol_votes[symbol]['reasons'].append(signal['reason'])
        
        # Generate final signals based on voting threshold
        total_strategies = len(all_signals)
        for symbol, votes in symbol_votes.items():
            buy_ratio = votes['buy'] / total_strategies if total_strategies > 0 else 0
            sell_ratio = votes['sell'] / total_strategies if total_strategies > 0 else 0
            
            if buy_ratio > {voting_threshold}:
                final_signals.append({{
                    'symbol': symbol,
                    'action': 'buy',
                    'strength': buy_ratio,
                    'reason': ' | '.join(votes['reasons'])
                }})
            elif sell_ratio > {voting_threshold}:
                final_signals.append({{
                    'symbol': symbol,
                    'action': 'sell',
                    'strength': sell_ratio,
                    'reason': ' | '.join(votes['reasons'])
                }})
"""
        else:  # sequential
            combination_code = """
        # Sequential combination (first strategy that generates a signal wins)
        for signal in all_signals:
            final_signals.append(signal)
            break  # Only take the first signal
"""
        
        return f"""
def generate_signals(timestamp, current_prices, positions, balance):
    \"\"\"Composite Strategy - Combining Multiple Strategies\"\"\"
    final_signals = []
    all_signals = []
    
    # Execute all component strategies
{''.join(strategy_calls)}
    
    # Combine signals based on logic
{combination_code}
    
    return final_signals
"""

    def compare_strategies(self, strategy_ids: List[int], metrics: List[str], timeframe: str = "30d") -> Dict[str, Any]:
        """Compare multiple strategies based on specified metrics."""
        if not db_client:
            raise ValueError("Database client not available")
        
        session = db_client.get_session()
        try:
            # Get strategies
            strategies = session.query(Strategy).filter(Strategy.id.in_(strategy_ids)).all()
            if len(strategies) != len(strategy_ids):
                missing_ids = set(strategy_ids) - {s.id for s in strategies}
                raise ValueError(f"Strategies not found: {missing_ids}")
            
            # Get performance data for each strategy
            comparison_data = {
                "strategies": [],
                "metrics": {},
                "rankings": {}
            }
            
            for strategy in strategies:
                strategy_data = {
                    "id": strategy.id,
                    "name": strategy.name,
                    "type": strategy.parameters.get("strategy_type", "unknown"),
                    "enabled": strategy.is_active,
                    "created_at": strategy.created_at
                }
                comparison_data["strategies"].append(strategy_data)
            
            # Calculate metrics for each strategy
            for metric in metrics:
                metric_values = []
                for strategy in strategies:
                    # Get performance data from database or calculate
                    performance = self._get_strategy_performance(strategy.id, timeframe)
                    metric_values.append(performance.get(metric, 0.0))
                
                comparison_data["metrics"][metric] = metric_values
                
                # Calculate rankings (higher is better for most metrics)
                if metric in ["total_return", "sharpe_ratio", "win_rate", "profit_factor"]:
                    # Higher is better
                    rankings = [i[0] for i in sorted(enumerate(metric_values), key=lambda x: x[1], reverse=True)]
                else:
                    # Lower is better (e.g., max_drawdown)
                    rankings = [i[0] for i in sorted(enumerate(metric_values), key=lambda x: x[1])]
                
                comparison_data["rankings"][metric] = rankings
            
            return comparison_data
            
        finally:
            session.close()

    def calculate_risk_metrics(self, strategy_id: int, confidence_level: float = 0.95, timeframe: str = "30d") -> Dict[str, float]:
        """Calculate comprehensive risk metrics for a strategy."""
        if not db_client:
            raise ValueError("Database client not available")
        
        session = db_client.get_session()
        try:
            # Get strategy
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            # Get historical returns (mock data for now)
            returns = self._get_strategy_returns(strategy_id, timeframe)
            
            if not returns:
                return {
                    "volatility": 0.0,
                    "var": 0.0,
                    "cvar": 0.0,
                    "max_drawdown": 0.0,
                    "downside_deviation": 0.0,
                    "calmar_ratio": 0.0,
                    "sortino_ratio": 0.0,
                    "beta": 0.0,
                    "correlation": 0.0,
                    "risk_score": 0.0
                }
            
            # Calculate risk metrics
            risk_metrics = {}
            
            # Volatility (standard deviation of returns)
            import numpy as np
            returns_array = np.array(returns)
            risk_metrics["volatility"] = float(np.std(returns_array) * np.sqrt(252))  # Annualized
            
            # Value at Risk (VaR)
            var_percentile = (1 - confidence_level) * 100
            risk_metrics["var"] = float(np.percentile(returns_array, var_percentile))
            
            # Conditional Value at Risk (CVaR) / Expected Shortfall
            var_threshold = risk_metrics["var"]
            tail_returns = returns_array[returns_array <= var_threshold]
            risk_metrics["cvar"] = float(np.mean(tail_returns)) if len(tail_returns) > 0 else var_threshold
            
            # Maximum Drawdown
            cumulative_returns = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdowns = (cumulative_returns - running_max) / running_max
            risk_metrics["max_drawdown"] = float(np.min(drawdowns))
            
            # Downside Deviation
            downside_returns = returns_array[returns_array < 0]
            risk_metrics["downside_deviation"] = float(np.std(downside_returns) * np.sqrt(252)) if len(downside_returns) > 0 else 0.0
            
            # Calmar Ratio (Annual Return / Max Drawdown)
            annual_return = float(np.mean(returns_array) * 252)
            risk_metrics["calmar_ratio"] = annual_return / abs(risk_metrics["max_drawdown"]) if risk_metrics["max_drawdown"] != 0 else 0.0
            
            # Sortino Ratio (Excess Return / Downside Deviation)
            risk_free_rate = 0.02  # Assume 2% risk-free rate
            excess_return = annual_return - risk_free_rate
            risk_metrics["sortino_ratio"] = excess_return / risk_metrics["downside_deviation"] if risk_metrics["downside_deviation"] != 0 else 0.0
            
            # Beta (market correlation - simplified)
            # In a real implementation, this would compare against a market index
            risk_metrics["beta"] = 1.0  # Placeholder
            
            # Correlation with market (simplified)
            risk_metrics["correlation"] = 0.5  # Placeholder
            
            # Risk Score (composite risk measure)
            risk_score = (
                abs(risk_metrics["var"]) * 0.3 +
                abs(risk_metrics["max_drawdown"]) * 0.3 +
                risk_metrics["volatility"] * 0.2 +
                (1 - risk_metrics["calmar_ratio"]) * 0.2
            )
            risk_metrics["risk_score"] = min(risk_score, 1.0)
            
            return risk_metrics
            
        finally:
            session.close()

    def optimize_parameters(self, strategy_id: int, optimization_type: str, target_metric: str = "sharpe_ratio", 
                          max_iterations: int = 100, population_size: int = 50) -> Dict[str, Any]:
        """Optimize strategy parameters using various algorithms."""
        if not db_client:
            raise ValueError("Database client not available")
        
        session = db_client.get_session()
        try:
            # Get strategy
            strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")
            
            strategy_type = strategy.parameters.get("strategy_type", "unknown")
            current_params = strategy.parameters.get("parameters", {})
            
            if optimization_type == "genetic":
                return self._genetic_algorithm_optimization(
                    strategy_id, strategy_type, current_params, target_metric, max_iterations, population_size
                )
            elif optimization_type == "walk_forward":
                return self._walk_forward_optimization(
                    strategy_id, strategy_type, current_params, target_metric, max_iterations
                )
            elif optimization_type == "sensitivity":
                return self._sensitivity_analysis(
                    strategy_id, strategy_type, current_params, target_metric
                )
            elif optimization_type == "adaptive":
                return self._adaptive_optimization(
                    strategy_id, strategy_type, current_params, target_metric, max_iterations
                )
            else:
                raise ValueError(f"Unknown optimization type: {optimization_type}")
                
        finally:
            session.close()

    def _genetic_algorithm_optimization(self, strategy_id: int, strategy_type: str, current_params: Dict[str, Any], 
                                      target_metric: str, max_iterations: int, population_size: int) -> Dict[str, Any]:
        """Optimize parameters using genetic algorithm."""
        import random
        import numpy as np
        
        # Get parameter bounds from template
        template = self.strategy_templates.get(strategy_type, {})
        param_bounds = template.get("parameters", {})
        
        # Initialize population
        population = []
        for _ in range(population_size):
            individual = {}
            for param_name, param_config in param_bounds.items():
                if param_config.get("type") == "int":
                    individual[param_name] = random.randint(param_config["min"], param_config["max"])
                elif param_config.get("type") == "float":
                    individual[param_name] = random.uniform(param_config["min"], param_config["max"])
                elif param_config.get("type") == "str" and "options" in param_config:
                    individual[param_name] = random.choice(param_config["options"])
            population.append(individual)
        
        best_score = float('-inf')
        best_parameters = current_params
        optimization_history = []
        
        for generation in range(max_iterations):
            # Evaluate fitness for each individual
            fitness_scores = []
            for individual in population:
                # Simulate strategy performance with these parameters
                score = self._evaluate_parameters(strategy_id, individual, target_metric)
                fitness_scores.append(score)
                
                if score > best_score:
                    best_score = score
                    best_parameters = individual.copy()
            
            optimization_history.append({
                "generation": generation,
                "best_score": best_score,
                "avg_score": np.mean(fitness_scores),
                "best_parameters": best_parameters.copy()
            })
            
            # Selection (tournament selection)
            new_population = []
            for _ in range(population_size):
                # Tournament selection
                tournament_size = 3
                tournament = random.sample(list(enumerate(fitness_scores)), tournament_size)
                winner = max(tournament, key=lambda x: x[1])
                new_population.append(population[winner[0]].copy())
            
            # Crossover and mutation
            for i in range(0, population_size, 2):
                if i + 1 < population_size:
                    # Crossover
                    parent1, parent2 = new_population[i], new_population[i + 1]
                    child1, child2 = self._crossover(parent1, parent2)
                    
                    # Mutation
                    child1 = self._mutate(child1, param_bounds)
                    child2 = self._mutate(child2, param_bounds)
                    
                    new_population[i] = child1
                    new_population[i + 1] = child2
            
            population = new_population
        
        return {
            "best_parameters": best_parameters,
            "best_score": best_score,
            "optimization_history": optimization_history
        }

    def _walk_forward_optimization(self, strategy_id: int, strategy_type: str, current_params: Dict[str, Any], 
                                 target_metric: str, max_iterations: int) -> Dict[str, Any]:
        """Optimize parameters using walk-forward analysis."""
        import random
        
        # Simulate walk-forward optimization
        optimization_history = []
        best_score = float('-inf')
        best_parameters = current_params
        
        for iteration in range(max_iterations):
            # Simulate different time periods
            time_period = f"period_{iteration}"
            
            # Generate parameter variations
            test_params = current_params.copy()
            for param_name in test_params:
                if isinstance(test_params[param_name], (int, float)):
                    # Add some variation
                    variation = random.uniform(-0.1, 0.1)
                    test_params[param_name] = test_params[param_name] * (1 + variation)
            
            # Evaluate performance
            score = self._evaluate_parameters(strategy_id, test_params, target_metric)
            
            if score > best_score:
                best_score = score
                best_parameters = test_params.copy()
            
            optimization_history.append({
                "iteration": iteration,
                "time_period": time_period,
                "score": score,
                "best_score": best_score,
                "parameters": test_params.copy()
            })
        
        return {
            "best_parameters": best_parameters,
            "best_score": best_score,
            "optimization_history": optimization_history
        }

    def _sensitivity_analysis(self, strategy_id: int, strategy_type: str, current_params: Dict[str, Any], 
                            target_metric: str) -> Dict[str, Any]:
        """Perform parameter sensitivity analysis."""
        import random
        
        sensitivity_results = {}
        optimization_history = []
        
        for param_name, param_value in current_params.items():
            if isinstance(param_value, (int, float)):
                # Test parameter variations
                variations = []
                scores = []
                
                # Test ±20% variations
                for variation in [-0.2, -0.1, 0, 0.1, 0.2]:
                    test_params = current_params.copy()
                    test_params[param_name] = param_value * (1 + variation)
                    
                    score = self._evaluate_parameters(strategy_id, test_params, target_metric)
                    variations.append(variation)
                    scores.append(score)
                
                sensitivity_results[param_name] = {
                    "variations": variations,
                    "scores": scores,
                    "sensitivity": max(scores) - min(scores)  # Range of scores
                }
                
                optimization_history.append({
                    "parameter": param_name,
                    "variations": variations,
                    "scores": scores
                })
        
        return {
            "best_parameters": current_params,  # Return current parameters as best
            "best_score": max([max(result["scores"]) for result in sensitivity_results.values()]) if sensitivity_results else 0.0,
            "optimization_history": optimization_history
        }

    def _adaptive_optimization(self, strategy_id: int, strategy_type: str, current_params: Dict[str, Any], 
                             target_metric: str, max_iterations: int) -> Dict[str, Any]:
        """Adaptive parameter optimization based on market conditions."""
        import random
        
        optimization_history = []
        best_score = float('-inf')
        best_parameters = current_params
        
        for iteration in range(max_iterations):
            # Simulate market condition detection
            market_condition = random.choice(["trending", "ranging", "volatile", "stable"])
            
            # Adapt parameters based on market condition
            adapted_params = current_params.copy()
            
            if market_condition == "trending":
                # Increase trend-following parameters
                if "fast_period" in adapted_params:
                    adapted_params["fast_period"] = max(5, adapted_params["fast_period"] - 2)
                if "slow_period" in adapted_params:
                    adapted_params["slow_period"] = min(200, adapted_params["slow_period"] + 5)
            
            elif market_condition == "ranging":
                # Increase mean reversion parameters
                if "lookback_period" in adapted_params:
                    adapted_params["lookback_period"] = min(100, adapted_params["lookback_period"] + 5)
                if "std_dev_threshold" in adapted_params:
                    adapted_params["std_dev_threshold"] = max(1.0, adapted_params["std_dev_threshold"] - 0.1)
            
            elif market_condition == "volatile":
                # Increase volatility-based parameters
                if "std_dev" in adapted_params:
                    adapted_params["std_dev"] = min(3.0, adapted_params["std_dev"] + 0.1)
            
            # Evaluate adapted parameters
            score = self._evaluate_parameters(strategy_id, adapted_params, target_metric)
            
            if score > best_score:
                best_score = score
                best_parameters = adapted_params.copy()
            
            optimization_history.append({
                "iteration": iteration,
                "market_condition": market_condition,
                "score": score,
                "best_score": best_score,
                "adapted_parameters": adapted_params.copy()
            })
        
        return {
            "best_parameters": best_parameters,
            "best_score": best_score,
            "optimization_history": optimization_history
        }

    def _evaluate_parameters(self, strategy_id: int, parameters: Dict[str, Any], target_metric: str) -> float:
        """Evaluate strategy performance with given parameters."""
        # This would typically run a backtest with the given parameters
        # For now, return a simulated score based on parameter values
        import random
        
        # Use strategy_id as seed for reproducible results
        random.seed(strategy_id + hash(str(parameters)))
        
        # Simulate performance based on parameters
        base_score = random.uniform(0.5, 1.5)
        
        # Adjust score based on parameter values (simplified)
        if "fast_period" in parameters and "slow_period" in parameters:
            if parameters["fast_period"] < parameters["slow_period"]:
                base_score *= 1.1  # Good parameter relationship
            else:
                base_score *= 0.8  # Bad parameter relationship
        
        if "period" in parameters:
            if 10 <= parameters["period"] <= 20:
                base_score *= 1.05  # Good RSI period
        
        return base_score

    def _crossover(self, parent1: Dict[str, Any], parent2: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Perform crossover between two parent parameter sets."""
        import random
        
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # Single-point crossover
        crossover_point = random.randint(1, len(parent1) - 1)
        keys = list(parent1.keys())
        
        for i in range(crossover_point, len(keys)):
            key = keys[i]
            child1[key], child2[key] = child2[key], child1[key]
        
        return child1, child2

    def _mutate(self, individual: Dict[str, Any], param_bounds: Dict[str, Any]) -> Dict[str, Any]:
        """Mutate an individual's parameters."""
        import random
        
        mutated = individual.copy()
        mutation_rate = 0.1
        
        for param_name, param_config in param_bounds.items():
            if random.random() < mutation_rate:
                if param_config.get("type") == "int":
                    mutated[param_name] = random.randint(param_config["min"], param_config["max"])
                elif param_config.get("type") == "float":
                    mutated[param_name] = random.uniform(param_config["min"], param_config["max"])
                elif param_config.get("type") == "str" and "options" in param_config:
                    mutated[param_name] = random.choice(param_config["options"])
        
        return mutated

    def _get_strategy_returns(self, strategy_id: int, timeframe: str) -> List[float]:
        """Get historical returns for a strategy."""
        # This would typically query the database for actual trade data
        # For now, return mock data
        import random
        import numpy as np
        
        # Generate realistic return series
        np.random.seed(strategy_id)  # For reproducible results
        n_days = 30 if timeframe == "30d" else 90 if timeframe == "90d" else 365
        
        # Generate returns with some autocorrelation and volatility clustering
        returns = []
        current_return = 0.001  # Start with small positive return
        
        for _ in range(n_days):
            # Add some persistence
            current_return = current_return * 0.7 + np.random.normal(0.001, 0.02) * 0.3
            returns.append(current_return)
        
        return returns

    def _get_strategy_performance(self, strategy_id: int, timeframe: str) -> Dict[str, float]:
        """Get performance metrics for a strategy."""
        # This would typically query the database for actual performance data
        # For now, return mock data
        import random
        
        return {
            "total_return": random.uniform(-0.2, 0.5),
            "sharpe_ratio": random.uniform(-1.0, 2.0),
            "max_drawdown": random.uniform(0.05, 0.3),
            "win_rate": random.uniform(0.3, 0.7),
            "profit_factor": random.uniform(0.8, 2.0),
            "total_trades": random.randint(10, 100),
            "avg_trade_duration": random.uniform(1, 24)
        }

# Initialize strategy manager
strategy_manager = StrategyManager()

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
            health_status["checks"]["database"] = {"status": "healthy" if db_health else "error"}
        else:
            health_status["checks"]["database"] = {"status": "unavailable"}
    except Exception as e:
        health_status["checks"]["database"] = {"status": "error", "error": str(e)}
    
    # Vault health check
    try:
        if vault_client:
            vault_health = vault_client.health_check()
            health_status["checks"]["vault"] = {"status": "healthy" if vault_health else "error"}
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
            session = db_client.get_session()
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
            
            session.add(strategy)
            session.commit()
            session.refresh(strategy)
            
            logger.info(f"Created strategy: {request.name} (ID: {strategy.id})")
            
            session.close()
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
        
        session = db_client.get_session()
        query = session.query(Strategy)
        
        if status:
            if status == "active":
                query = query.filter(Strategy.is_active == True)
            elif status == "inactive":
                query = query.filter(Strategy.is_active == False)
        
        strategies = query.limit(limit).all()
        session.close()
        
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
        
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            session.close()
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        params = strategy.parameters or {}
        
        result = {
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
        
        session.close()
        return result
    
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
        
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            session.close()
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
        
        session.commit()
        session.close()
        
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
        
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            session.close()
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # TODO: Implement actual performance calculation
        # For now, return placeholder data
        performance_data = {
            "total_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "profit_factor": 0.0
        }
        
        session.close()
        
        return PerformanceResponse(
            strategy_id=strategy_id,
            performance=performance_data,
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
        
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            session.close()
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        strategy.is_active = True
        current_params = strategy.parameters or {}
        current_params["enabled"] = True
        strategy.parameters = current_params
        strategy.updated_at = datetime.utcnow()
        
        session.commit()
        strategy_name = strategy.name
        session.close()
        
        logger.info(f"Enabled strategy: {strategy_name} (ID: {strategy_id})")
        
        return {
            "strategy_id": strategy_id,
            "status": "enabled",
            "message": "Strategy enabled successfully"
        }
    
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
        
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            session.close()
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        strategy.is_active = False
        current_params = strategy.parameters or {}
        current_params["enabled"] = False
        strategy.parameters = current_params
        strategy.updated_at = datetime.utcnow()
        
        session.commit()
        strategy_name = strategy.name
        session.close()
        
        logger.info(f"Disabled strategy: {strategy_name} (ID: {strategy_id})")
        
        return {
            "strategy_id": strategy_id,
            "status": "disabled",
            "message": "Strategy disabled successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling strategy: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disable strategy: {str(e)}")

@app.post("/strategies/compare", response_model=StrategyComparisonResponse)
async def compare_strategies(request: StrategyComparisonRequest):
    """Compare multiple strategies based on performance metrics."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Validate that strategies exist
        session = db_client.get_session()
        strategies = session.query(Strategy).filter(Strategy.id.in_(request.strategy_ids)).all()
        session.close()
        
        if len(strategies) != len(request.strategy_ids):
            missing_ids = set(request.strategy_ids) - {s.id for s in strategies}
            raise HTTPException(status_code=404, detail=f"Strategies not found: {missing_ids}")
        
        # Perform comparison
        comparison_data = strategy_manager.compare_strategies(
            request.strategy_ids, 
            request.metrics, 
            request.timeframe
        )
        
        # Generate comparison ID
        comparison_id = f"comp_{int(time.time())}_{len(request.strategy_ids)}"
        
        return StrategyComparisonResponse(
            comparison_id=comparison_id,
            strategies=comparison_data["strategies"],
            metrics=comparison_data["metrics"],
            rankings=comparison_data["rankings"],
            created_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing strategies: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to compare strategies: {str(e)}")

@app.post("/strategies/{strategy_id}/risk-metrics", response_model=RiskMetricsResponse)
async def get_strategy_risk_metrics(strategy_id: int, request: RiskMetricsRequest):
    """Calculate comprehensive risk metrics for a strategy."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Validate strategy exists
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        session.close()
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Calculate risk metrics
        risk_metrics = strategy_manager.calculate_risk_metrics(
            strategy_id, 
            request.confidence_level, 
            request.timeframe
        )
        
        return RiskMetricsResponse(
            strategy_id=strategy_id,
            risk_metrics=risk_metrics,
            calculated_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate risk metrics: {str(e)}")

@app.post("/strategies/{strategy_id}/optimize", response_model=OptimizationResponse)
async def optimize_strategy_parameters(strategy_id: int, request: OptimizationRequest):
    """Optimize strategy parameters using various algorithms."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Validate strategy exists
        session = db_client.get_session()
        strategy = session.query(Strategy).filter(Strategy.id == strategy_id).first()
        session.close()
        
        if not strategy:
            raise HTTPException(status_code=404, detail=f"Strategy {strategy_id} not found")
        
        # Perform optimization
        optimization_result = strategy_manager.optimize_parameters(
            strategy_id,
            request.optimization_type,
            request.target_metric,
            request.max_iterations,
            request.population_size
        )
        
        # Generate optimization ID
        optimization_id = f"opt_{int(time.time())}_{strategy_id}_{request.optimization_type}"
        
        return OptimizationResponse(
            optimization_id=optimization_id,
            strategy_id=strategy_id,
            optimization_type=request.optimization_type,
            best_parameters=optimization_result["best_parameters"],
            best_score=optimization_result["best_score"],
            optimization_history=optimization_result["optimization_history"],
            completed_at=datetime.utcnow()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error optimizing strategy parameters: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to optimize strategy parameters: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8011)
