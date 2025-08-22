"""
VolexSwarm Agentic Strategy Agent - Autonomous Strategy Development and Management

This agent transforms the traditional FastAPI-based strategy agent into an intelligent,
autonomous AutoGen agent capable of self-directed strategy development and management.
"""

import sys
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
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
from common.websocket_client import AgentWebSocketClient, MessageType
from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig

# Initialize structured logger
logger = get_logger("agentic_strategy")

class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    TESTING = "testing"

@dataclass
class StrategyTemplate:
    """Strategy template model."""
    type: str
    name: str
    description: str
    parameters: Dict[str, Any]
    code_template: str

@dataclass
class StrategyRequest:
    """Strategy creation/update request model."""
    name: str
    description: Optional[str] = None
    strategy_type: str = "moving_average"
    parameters: Dict[str, Any] = None
    symbols: List[str] = None
    timeframe: str = "1h"
    risk_per_trade: float = 0.01
    max_positions: int = 5
    enabled: bool = False

@dataclass
class StrategyInfo:
    """Strategy information model."""
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

class StrategyManager:
    """Manages strategy operations and lifecycle."""
    
    def __init__(self):
        self.strategy_templates = self._initialize_templates()
        self.strategy_cache = {}
        
    def _initialize_templates(self) -> Dict[str, StrategyTemplate]:
        """Initialize strategy templates."""
        templates = {
            "moving_average": StrategyTemplate(
                type="moving_average",
                name="Moving Average Crossover",
                description="Simple moving average crossover strategy",
                parameters={
                    "fast_period": {"type": "int", "default": 10, "min": 5, "max": 50},
                    "slow_period": {"type": "int", "default": 20, "min": 10, "max": 200},
                    "signal_period": {"type": "int", "default": 9, "min": 5, "max": 20}
                },
                code_template="moving_average_crossover"
            ),
            "rsi": StrategyTemplate(
                type="rsi",
                name="RSI Strategy",
                description="Relative Strength Index strategy",
                parameters={
                    "period": {"type": "int", "default": 14, "min": 5, "max": 30},
                    "oversold": {"type": "float", "default": 30.0, "min": 10.0, "max": 40.0},
                    "overbought": {"type": "float", "default": 70.0, "min": 60.0, "max": 90.0}
                },
                code_template="rsi_strategy"
            ),
            "bollinger_bands": StrategyTemplate(
                type="bollinger_bands",
                name="Bollinger Bands Strategy",
                description="Bollinger Bands mean reversion strategy",
                parameters={
                    "period": {"type": "int", "default": 20, "min": 10, "max": 50},
                    "std_dev": {"type": "float", "default": 2.0, "min": 1.0, "max": 3.0}
                },
                code_template="bollinger_bands_strategy"
            ),
            "macd": StrategyTemplate(
                type="macd",
                name="MACD Strategy",
                description="MACD crossover strategy",
                parameters={
                    "fast_period": {"type": "int", "default": 12, "min": 5, "max": 20},
                    "slow_period": {"type": "int", "default": 26, "min": 20, "max": 50},
                    "signal_period": {"type": "int", "default": 9, "min": 5, "max": 20}
                },
                code_template="macd_strategy"
            )
        }
        return templates
        
    def validate_parameters(self, strategy_type: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate strategy parameters against template constraints."""
        try:
            if strategy_type not in self.strategy_templates:
                return False, f"Unknown strategy type: {strategy_type}"
                
            template = self.strategy_templates[strategy_type]
            
            for param_name, param_config in template.parameters.items():
                if param_name not in parameters:
                    if "default" in param_config:
                        parameters[param_name] = param_config["default"]
                    else:
                        return False, f"Missing required parameter: {param_name}"
                        
                value = parameters[param_name]
                param_type = param_config["type"]
                
                # Type validation
                if param_type == "int" and not isinstance(value, int):
                    return False, f"Parameter {param_name} must be an integer"
                elif param_type == "float" and not isinstance(value, (int, float)):
                    return False, f"Parameter {param_name} must be a number"
                    
                # Range validation
                if "min" in param_config and value < param_config["min"]:
                    return False, f"Parameter {param_name} must be >= {param_config['min']}"
                if "max" in param_config and value > param_config["max"]:
                    return False, f"Parameter {param_name} must be <= {param_config['max']}"
                    
            return True, "Parameters validated successfully"
            
        except Exception as e:
            return False, f"Parameter validation error: {str(e)}"
            
    def generate_strategy_code(self, strategy_type: str, parameters: Dict[str, Any]) -> str:
        """Generate strategy code based on template and parameters."""
        try:
            if strategy_type not in self.strategy_templates:
                raise ValueError(f"Unknown strategy type: {strategy_type}")
                
            template = self.strategy_templates[strategy_type]
            
            if template.code_template == "moving_average_crossover":
                return self._generate_moving_average_code(parameters)
            elif template.code_template == "rsi_strategy":
                return self._generate_rsi_code(parameters)
            elif template.code_template == "bollinger_bands_strategy":
                return self._generate_bollinger_bands_code(parameters)
            elif template.code_template == "macd_strategy":
                return self._generate_macd_code(parameters)
            else:
                raise ValueError(f"Unknown code template: {template.code_template}")
                
        except Exception as e:
            logger.error(f"Error generating strategy code: {e}")
            raise
            
    def _generate_moving_average_code(self, params: Dict[str, Any]) -> str:
        """Generate moving average crossover strategy code."""
        fast_period = params.get("fast_period", 10)
        slow_period = params.get("slow_period", 20)
        signal_period = params.get("signal_period", 9)
        
        code = f"""
def moving_average_strategy(data):
    \"\"\"
    Moving Average Crossover Strategy
    Fast Period: {fast_period}, Slow Period: {slow_period}, Signal Period: {signal_period}
    \"\"\"
    import pandas as pd
    import numpy as np
    
    # Calculate moving averages
    data['fast_ma'] = data['close'].rolling(window={fast_period}).mean()
    data['slow_ma'] = data['close'].rolling(window={slow_period}).mean()
    data['signal_ma'] = data['fast_ma'].rolling(window={signal_period}).mean()
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['fast_ma'] > data['slow_ma'], 'signal'] = 1  # Buy signal
    data.loc[data['fast_ma'] < data['slow_ma'], 'signal'] = -1  # Sell signal
    
    # Signal confirmation
    data.loc[data['signal_ma'] < data['slow_ma'], 'signal'] = 0  # No signal when below slow MA
    
    return data
"""
        return code
        
    def _generate_rsi_code(self, params: Dict[str, Any]) -> str:
        """Generate RSI strategy code."""
        period = params.get("period", 14)
        oversold = params.get("oversold", 30.0)
        overbought = params.get("overbought", 70.0)
        
        code = f"""
def rsi_strategy(data):
    \"\"\"
    RSI Strategy
    Period: {period}, Oversold: {oversold}, Overbought: {overbought}
    \"\"\"
    import pandas as pd
    import numpy as np
    
    # Calculate RSI
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window={period}).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window={period}).mean()
    rs = gain / loss
    data['rsi'] = 100 - (100 / (1 + rs))
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['rsi'] < {oversold}, 'signal'] = 1  # Buy signal (oversold)
    data.loc[data['rsi'] > {overbought}, 'signal'] = -1  # Sell signal (overbought)
    
    return data
"""
        return code
        
    def _generate_bollinger_bands_code(self, params: Dict[str, Any]) -> str:
        """Generate Bollinger Bands strategy code."""
        period = params.get("period", 20)
        std_dev = params.get("std_dev", 2.0)
        
        code = f"""
def bollinger_bands_strategy(data):
    \"\"\"
    Bollinger Bands Strategy
    Period: {period}, Standard Deviation: {std_dev}
    \"\"\"
    import pandas as pd
    import numpy as np
    
    # Calculate Bollinger Bands
    data['bb_middle'] = data['close'].rolling(window={period}).mean()
    bb_std = data['close'].rolling(window={period}).std()
    data['bb_upper'] = data['bb_middle'] + (bb_std * {std_dev})
    data['bb_lower'] = data['bb_middle'] - (bb_std * {std_dev})
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['close'] < data['bb_lower'], 'signal'] = 1  # Buy signal (below lower band)
    data.loc[data['close'] > data['bb_upper'], 'signal'] = -1  # Sell signal (above upper band)
    
    return data
"""
        return code
        
    def _generate_macd_code(self, params: Dict[str, Any]) -> str:
        """Generate MACD strategy code."""
        fast_period = params.get("fast_period", 12)
        slow_period = params.get("slow_period", 26)
        signal_period = params.get("signal_period", 9)
        
        code = f"""
def macd_strategy(data):
    \"\"\"
    MACD Strategy
    Fast Period: {fast_period}, Slow Period: {slow_period}, Signal Period: {signal_period}
    \"\"\"
    import pandas as pd
    import numpy as np
    
    # Calculate MACD
    exp1 = data['close'].ewm(span={fast_period}).mean()
    exp2 = data['close'].ewm(span={slow_period}).mean()
    data['macd'] = exp1 - exp2
    data['signal_line'] = data['macd'].ewm(span={signal_period}).mean()
    data['histogram'] = data['macd'] - data['signal_line']
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['macd'] > data['signal_line'], 'signal'] = 1  # Buy signal
    data.loc[data['macd'] < data['signal_line'], 'signal'] = -1  # Sell signal
    
    return data
"""
        return code

class AgenticStrategyAgent(BaseAgent):
    """Intelligent Strategy Agent for autonomous strategy development and management"""
    
    def __init__(self, llm_config: Dict[str, Any] = None):
        # Provide a default LLM config if none is provided
        if llm_config is None:
            llm_config = {
                "config_list": [
                    {
                        "api_type": "openai",
                        "api_key": "dummy-key",  # Will be overridden by environment
                        "model": "gpt-4o-mini"
                    }
                ],
                "temperature": 0.7
            }
        system_message = """You are an intelligent Strategy Agent for VolexSwarm, a cryptocurrency trading system.

Your capabilities include:
- Autonomous strategy development and management
- Strategy template creation and customization
- Strategy lifecycle management
- Self-directed strategy optimization
- Reasoning about strategy selection and design

You can:
1. Create and manage trading strategies using templates
2. Generate strategy code based on parameters
3. Validate strategy parameters and constraints
4. Manage strategy lifecycle (draft, active, paused, archived)
5. Analyze strategy performance and provide insights
6. Recommend strategy improvements and optimizations
7. Coordinate with other agents for strategy execution

Your responsibilities:
- Develop new trading strategies based on market conditions
- Manage existing strategies and their lifecycle
- Validate strategy parameters and ensure they meet requirements
- Generate executable strategy code
- Provide strategy recommendations and insights
- Coordinate with execution and monitoring agents

Available strategy templates:
- Moving Average Crossover: Simple MA crossover strategy
- RSI Strategy: Relative Strength Index mean reversion
- Bollinger Bands: Mean reversion using Bollinger Bands
- MACD Strategy: MACD crossover signals

Always explain your strategy decisions and reasoning.
Be proactive in identifying market opportunities for new strategies.
Learn from strategy performance to improve future designs.
Consider risk management and position sizing in strategy design.
Prioritize strategy robustness and adaptability to market conditions."""

        config = AgentConfig(
            name="AgenticStrategyAgent",
            system_message=system_message,
            llm_config=llm_config
        )
        super().__init__(config)
        
        # Initialize strategy manager
        self.strategy_manager = StrategyManager()
        self.db_client = None
        self.ws_client = None
        self.strategy_history = []
        self.performance_metrics = {
            "total_strategies": 0,
            "active_strategies": 0,
            "successful_strategies": 0,
            "failed_strategies": 0,
            "average_performance": 0.0
        }
        
        # Initialize infrastructure attributes for test compatibility
        self.vault_client = None
        self.db_client = None
        self.openai_client = None
        
    async def initialize_infrastructure(self):
        """Initialize connections to existing infrastructure."""
        try:
            # Initialize Vault client
            from common.vault import get_vault_client, get_agent_config
            self.vault_client = get_vault_client()
            
            # Initialize database client
            from common.db import get_db_client
            self.db_client = get_db_client()
            
            # Initialize OpenAI client
            from common.openai_client import get_openai_client
            self.openai_client = get_openai_client()
            
            # Configure LLM with real API key from Vault
            if self.vault_client:
                # Get agent-specific config
                agent_config = get_agent_config("strategy")
                
                # Get OpenAI API key from the correct location
                openai_secret = self.vault_client.get_secret("openai/api_key")
                openai_api_key = None
                if openai_secret and "api_key" in openai_secret:
                    openai_api_key = openai_secret["api_key"]
                
                if openai_api_key:
                    # Update the LLM config with the real API key
                    self.config.llm_config = {
                        "config_list": [{
                            "api_type": "openai",
                            "model": "gpt-4o-mini",
                            "api_key": openai_api_key
                        }],
                        "temperature": 0.7
                    }
                    logger.info("LLM configured with Vault API key")
                else:
                    logger.warning("OpenAI API key not found in Vault")
            
            logger.info("Infrastructure initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize infrastructure: {e}")
            raise
        
    async def initialize(self):
        """Initialize the agent."""
        try:
            # Initialize database client
            self.db_client = get_db_client()
            
            # Initialize WebSocket client for real-time communication
            self.ws_client = AgentWebSocketClient("agentic_strategy")
            await self.ws_client.connect()
            
            # Load existing strategies
            await self._load_existing_strategies()
            
            logger.info("Agentic Strategy Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Agentic Strategy Agent: {e}")
            return False
            
    async def shutdown(self):
        """Shutdown the agent."""
        try:
            if self.ws_client:
                await self.ws_client.disconnect()
            logger.info("Agentic Strategy Agent shutdown successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    async def _load_existing_strategies(self):
        """Load existing strategies from database."""
        try:
            if self.db_client:
                # Query existing strategies
                query = "SELECT * FROM strategies ORDER BY created_at DESC"
                result = await self.db_client.execute_query(query)
                
                # Handle case where result might be empty or None
                if result is None:
                    logger.info("No existing strategies found in database")
                    return
                
                # Convert result to list if it's not already
                if not isinstance(result, list):
                    result = list(result) if result else []
                
                for row in result:
                    try:
                        # Safely access row data
                        row_dict = dict(row) if hasattr(row, '_asdict') else row
                        
                        # Parse parameters from JSON string
                        parameters = {}
                        if row_dict.get('parameters'):
                            try:
                                parameters = json.loads(row_dict['parameters']) if isinstance(row_dict['parameters'], str) else row_dict['parameters']
                            except:
                                parameters = {}
                        
                        strategy_info = StrategyInfo(
                            id=row_dict.get('id', 0),
                            name=row_dict.get('name', 'Unknown'),
                            description=row_dict.get('description', ''),
                            strategy_type="unknown",  # Not stored in DB
                            parameters=parameters,
                            symbols=[],  # Not stored in DB
                            timeframe="1h",  # Default
                            risk_per_trade=0.01,  # Default
                            max_positions=5,  # Default
                            enabled=row_dict.get('is_active', False),
                            status=StrategyStatus.ACTIVE if row_dict.get('is_active', False) else StrategyStatus.DRAFT,
                            created_at=row_dict.get('created_at', datetime.now()),
                            updated_at=row_dict.get('updated_at', datetime.now())
                        )
                        self.strategy_history.append(strategy_info)
                    except Exception as row_error:
                        logger.warning(f"Error processing strategy row: {row_error}")
                        continue
                    
                logger.info(f"Loaded {len(self.strategy_history)} existing strategies")
                
        except Exception as e:
            logger.error(f"Error loading existing strategies: {e}")
            # Don't let this error prevent agent initialization
            logger.info("Continuing with empty strategy history")
            
    async def create_strategy(self, strategy_request: StrategyRequest) -> Dict[str, Any]:
        """Create a new strategy autonomously."""
        try:
            # Validate parameters
            is_valid, validation_message = self.strategy_manager.validate_parameters(
                strategy_request.strategy_type, 
                strategy_request.parameters or {}
            )
            
            if not is_valid:
                return {"error": validation_message}
                
            # Generate strategy code
            strategy_code = self.strategy_manager.generate_strategy_code(
                strategy_request.strategy_type,
                strategy_request.parameters or {}
            )
            
            # Create strategy record
            strategy_data = {
                "name": strategy_request.name,
                "description": strategy_request.description,
                "agent_name": "strategy",  # This is the agent that created it
                "parameters": json.dumps(strategy_request.parameters or {}),
                "is_active": strategy_request.enabled
            }
            
            # Save to database
            if self.db_client:
                query = """
                INSERT INTO strategies (name, description, agent_name, parameters, is_active)
                VALUES (:name, :description, :agent_name, :parameters, :is_active)
                RETURNING id
                """
                result = await self.db_client.execute_query(query, strategy_data)
                strategy_id = result[0]['id']
                strategy_data['id'] = strategy_id
                
            # Update performance metrics
            self.performance_metrics["total_strategies"] += 1
            if strategy_request.enabled:
                self.performance_metrics["active_strategies"] += 1
                
            # Send real-time update
            if self.ws_client:
                await self.ws_client.send_message(
                    MessageType.STRATEGY_UPDATE,
                    {
                        "agent": "agentic_strategy",
                        "action": "strategy_created",
                        "data": strategy_data
                    }
                )
                
            return {
                "success": True,
                "strategy_id": strategy_data.get('id'),
                "strategy": strategy_data,
                "code": strategy_code
            }
            
        except Exception as e:
            logger.error(f"Error creating strategy: {e}")
            return {"error": str(e)}
            
    async def get_strategy_templates(self) -> Dict[str, Any]:
        """Get available strategy templates."""
        try:
            templates = {}
            for template_type, template in self.strategy_manager.strategy_templates.items():
                templates[template_type] = {
                    "type": template.type,
                    "name": template.name,
                    "description": template.description,
                    "parameters": template.parameters
                }
                
            return {
                "success": True,
                "templates": templates,
                "count": len(templates)
            }
            
        except Exception as e:
            logger.error(f"Error getting strategy templates: {e}")
            return {"error": str(e)}
            
    async def list_strategies(self, status: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """List strategies with optional filtering."""
        try:
            strategies = []
            
            if self.db_client:
                query = "SELECT * FROM strategies"
                params = {}
                
                if status:
                    query += " WHERE status = :status"
                    params['status'] = status
                    
                query += " ORDER BY created_at DESC LIMIT :limit"
                params['limit'] = limit
                
                result = await self.db_client.execute_query(query, params)
                
                for row in result:
                    strategy_info = {
                        "id": row['id'],
                        "name": row['name'],
                        "description": row['description'],
                        "strategy_type": row['strategy_type'],
                        "parameters": row['parameters'],
                        "symbols": row['symbols'],
                        "timeframe": row['timeframe'],
                        "risk_per_trade": row['risk_per_trade'],
                        "max_positions": row['max_positions'],
                        "enabled": row['enabled'],
                        "status": row['status'],
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at']
                    }
                    strategies.append(strategy_info)
                    
            return {
                "success": True,
                "strategies": strategies,
                "count": len(strategies),
                "total_strategies": self.performance_metrics["total_strategies"]
            }
            
        except Exception as e:
            logger.error(f"Error listing strategies: {e}")
            return {"error": str(e)}
            
    async def update_strategy(self, strategy_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing strategy."""
        try:
            if self.db_client:
                # Build update query
                set_clauses = []
                params = {"strategy_id": strategy_id}
                
                for key, value in updates.items():
                    if key in ["name", "description", "parameters", "symbols", "timeframe", 
                              "risk_per_trade", "max_positions", "enabled"]:
                        set_clauses.append(f"{key} = :{key}")
                        params[key] = value
                        
                if not set_clauses:
                    return {"error": "No valid fields to update"}
                    
                set_clauses.append("updated_at = :updated_at")
                params["updated_at"] = datetime.now()
                
                query = f"UPDATE strategies SET {', '.join(set_clauses)} WHERE id = :strategy_id"
                await self.db_client.execute_query(query, params)
                
                # Get updated strategy
                result = await self.db_client.execute_query(
                    "SELECT * FROM strategies WHERE id = :strategy_id",
                    {"strategy_id": strategy_id}
                )
                
                if result:
                    strategy_data = result[0]
                    return {
                        "success": True,
                        "strategy": strategy_data
                    }
                else:
                    return {"error": "Strategy not found"}
                    
            return {"error": "Database not available"}
            
        except Exception as e:
            logger.error(f"Error updating strategy: {e}")
            return {"error": str(e)}
            
    async def analyze_strategy_performance(self, strategy_id: int) -> Dict[str, Any]:
        """Analyze strategy performance and provide insights."""
        try:
            if self.db_client:
                # Get strategy details
                strategy_result = await self.db_client.execute_query(
                    "SELECT * FROM strategies WHERE id = :strategy_id",
                    {"strategy_id": strategy_id}
                )
                
                if not strategy_result:
                    return {"error": "Strategy not found"}
                    
                strategy = strategy_result[0]
                
                # Get performance metrics
                performance_result = await self.db_client.execute_query(
                    "SELECT * FROM performance_metrics WHERE strategy_id = :strategy_id ORDER BY timestamp DESC LIMIT 100",
                    {"strategy_id": strategy_id}
                )
                
                if performance_result:
                    # Calculate performance statistics
                    returns = [row['return'] for row in performance_result]
                    total_return = sum(returns)
                    avg_return = total_return / len(returns) if returns else 0
                    max_return = max(returns) if returns else 0
                    min_return = min(returns) if returns else 0
                    
                    analysis = {
                        "strategy_id": strategy_id,
                        "strategy_name": strategy['name'],
                        "total_trades": len(performance_result),
                        "total_return": total_return,
                        "average_return": avg_return,
                        "max_return": max_return,
                        "min_return": min_return,
                        "performance_trend": "improving" if avg_return > 0 else "declining",
                        "recommendations": []
                    }
                    
                    # Generate recommendations
                    if avg_return < 0:
                        analysis["recommendations"].append("Consider adjusting strategy parameters")
                        analysis["recommendations"].append("Review market conditions and strategy fit")
                        
                    if len(performance_result) < 10:
                        analysis["recommendations"].append("Need more data for reliable analysis")
                        
                    return {
                        "success": True,
                        "analysis": analysis
                    }
                else:
                    return {
                        "success": True,
                        "analysis": {
                            "strategy_id": strategy_id,
                            "strategy_name": strategy['name'],
                            "message": "No performance data available yet"
                        }
                    }
                    
            return {"error": "Database not available"}
            
        except Exception as e:
            logger.error(f"Error analyzing strategy performance: {e}")
            return {"error": str(e)}
            
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and health information."""
        return {
            "agent": "agentic_strategy",
            "status": "healthy",
            "total_strategies": self.performance_metrics["total_strategies"],
            "active_strategies": self.performance_metrics["active_strategies"],
            "strategy_templates": len(self.strategy_manager.strategy_templates),
            "performance_metrics": self.performance_metrics,
            "timestamp": datetime.now()
        }

# Global instance for integration with agentic framework
agentic_strategy_agent = None

async def initialize_agentic_strategy_agent(llm_config: Dict[str, Any]) -> AgenticStrategyAgent:
    """Initialize the agentic strategy agent."""
    global agentic_strategy_agent
    
    if agentic_strategy_agent is None:
        agentic_strategy_agent = AgenticStrategyAgent(llm_config)
        await agentic_strategy_agent.initialize()
        
    return agentic_strategy_agent

async def shutdown_agentic_strategy_agent():
    """Shutdown the agentic strategy agent."""
    global agentic_strategy_agent
    
    if agentic_strategy_agent:
        await agentic_strategy_agent.shutdown()
        agentic_strategy_agent = None 