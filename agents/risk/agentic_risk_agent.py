"""
VolexSwarm Agentic Risk Agent - Autonomous Risk Management and Position Sizing

This agent transforms the traditional FastAPI-based risk agent into an intelligent,
autonomous AutoGen agent capable of self-directed risk management and position sizing.
"""

import sys
import os
import logging
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import time
import json
import math
from dataclasses import dataclass

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Trade, Order
from common.websocket_client import AgentWebSocketClient, MessageType
from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig
from common.config_manager import config_manager

# Initialize structured logger
logger = get_logger("agentic_risk")

# Risk management configuration is now loaded dynamically from database
# See common/config_manager.py for configuration management

@dataclass
class PositionSizingRequest:
    """Request model for position sizing calculation."""
    symbol: str
    side: str  # 'buy' or 'sell'
    account_balance: float
    current_price: float
    method: str = 'kelly'  # 'kelly', 'fixed', 'volatility', 'optimal_f'
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    correlation: Optional[float] = None

@dataclass
class RiskAssessmentRequest:
    """Request model for risk assessment."""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    side: str  # 'buy' or 'sell'
    account_balance: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    existing_positions: Optional[List[Dict[str, Any]]] = None

@dataclass
class StopLossRequest:
    """Request model for stop-loss calculation."""
    symbol: str
    entry_price: float
    current_price: float
    side: str  # 'buy' or 'sell'
    volatility: Optional[float] = None
    atr_multiplier: float = 2.0
    percentage: Optional[float] = None

@dataclass
class PortfolioRiskRequest:
    """Request model for portfolio risk assessment."""
    positions: List[Dict[str, Any]]
    account_balance: float
    risk_free_rate: float = 0.02

@dataclass
class EnhancedPositionSizingRequest:
    """Enhanced request model for position sizing with advanced features."""
    symbol: str
    side: str  # 'buy' or 'sell'
    account_balance: float
    current_price: float
    method: str = 'enhanced_kelly'  # 'enhanced_kelly', 'volatility_adaptive', 'correlation_adjusted'
    kelly_variant: str = 'quarter_kelly'  # 'full_kelly', 'half_kelly', 'quarter_kelly', 'eighth_kelly'
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    correlation: Optional[float] = None
    existing_positions: Optional[List[Dict[str, Any]]] = None
    market_conditions: Optional[Dict[str, Any]] = None  # Market volatility, trend, etc.

@dataclass
class CircuitBreakerRequest:
    """Request model for circuit breaker status."""
    symbol: str
    current_price: float
    previous_price: float
    timestamp: datetime

@dataclass
class DrawdownProtectionRequest:
    """Request model for drawdown protection."""
    account_balance: float
    initial_balance: float
    current_positions: List[Dict[str, Any]]
    timestamp: datetime

class RiskManager:
    """Manages risk calculations and position sizing."""
    
    def __init__(self):
        self.config = {}
        self.circuit_breaker_status = {}
        self.drawdown_history = []
        self.daily_loss_history = []
    
    async def initialize(self):
        """Initialize risk manager with dynamic configuration."""
        try:
            await config_manager.initialize()
            self.config = await config_manager.get_risk_config()
            logger.info("Risk manager initialized with dynamic configuration")
        except Exception as e:
            logger.warning(f"Failed to initialize risk manager with database config: {e}")
            logger.info("Using default configuration values")
            self.config = self._get_default_config()
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback to default."""
        config_item = self.config.get(key)
        if config_item is None:
            return default
        # Handle both database config format (nested dict) and default config format (direct value)
        if isinstance(config_item, dict) and 'value' in config_item:
            return config_item['value']
        else:
            return config_item
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values when database config is not available."""
        return {
            "kelly_fraction": 0.25,
            "max_position_size": 0.10,
            "min_volatility": 0.01,
            "max_volatility": 0.50,
            "volatility_multiplier": 2.0,
            "stop_loss_default": 0.02,
            "take_profit_default": 0.04,
            "max_portfolio_risk": 0.05,
            "correlation_threshold": 0.7,
            "circuit_breaker_enabled": True,
            "circuit_breaker_threshold": 0.10,
            "circuit_breaker_cooldown": 300,
            "hard_drawdown_limit": 0.20,
            "soft_drawdown_limit": 0.10,
            "daily_loss_hard_limit": 0.15,
            "daily_loss_soft_limit": 0.08
        }
        
    def calculate_kelly_position_size(self, win_rate: float, avg_win: float, 
                                    avg_loss: float, account_balance: float) -> float:
        """Calculate position size using Kelly Criterion."""
        try:
            if avg_loss == 0:
                return 0.0
                
            # Kelly Criterion formula: f = (bp - q) / b
            # where b = odds received, p = probability of win, q = probability of loss
            b = avg_win / avg_loss  # odds received
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply conservative fraction
            conservative_fraction = kelly_fraction * self.get_config_value("kelly_fraction", 0.25)
            
            # Calculate position size
            position_size = account_balance * conservative_fraction
            
            # Apply maximum position size limit
            max_position = account_balance * self.get_config_value("max_position_size", 0.10)
            position_size = min(position_size, max_position)
            
            return max(0.0, position_size)
            
        except Exception as e:
            logger.error(f"Error calculating Kelly position size: {e}")
            return 0.0
            
    def calculate_volatility_position_size(self, volatility: float, 
                                         account_balance: float, 
                                         current_price: float) -> float:
        """Calculate position size based on volatility."""
        try:
            # Normalize volatility
            normalized_volatility = max(self.get_config_value("min_volatility", 0.01), 
                                      min(volatility, self.get_config_value("max_volatility", 0.50)))
            
            # Inverse relationship: higher volatility = smaller position
            volatility_factor = 1.0 / (normalized_volatility * self.get_config_value("volatility_multiplier", 2.0))
            
            # Calculate position size
            position_size = account_balance * volatility_factor * self.get_config_value("max_position_size", 0.10)
            
            # Apply maximum position size limit
            max_position = account_balance * self.get_config_value("max_position_size", 0.10)
            position_size = min(position_size, max_position)
            
            return max(0.0, position_size)
            
        except Exception as e:
            logger.error(f"Error calculating volatility position size: {e}")
            return 0.0
            
    def calculate_fixed_position_size(self, account_balance: float, 
                                    current_price: float) -> float:
        """Calculate fixed percentage position size."""
        try:
            position_size = account_balance * self.get_config_value("max_position_size", 0.10)
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating fixed position size: {e}")
            return 0.0
            
    def calculate_optimal_f_position_size(self, win_rate: float, avg_win: float, 
                                        avg_loss: float, account_balance: float) -> float:
        """Calculate position size using Optimal f method."""
        try:
            if avg_loss == 0:
                return 0.0
                
            # Optimal f formula: f = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            optimal_f = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            
            # Apply conservative fraction
            conservative_fraction = optimal_f * self.get_config_value("kelly_fraction", 0.25)
            
            # Calculate position size
            position_size = account_balance * conservative_fraction
            
            # Apply maximum position size limit
            max_position = account_balance * self.get_config_value("max_position_size", 0.10)
            position_size = min(position_size, max_position)
            
            return max(0.0, position_size)
            
        except Exception as e:
            logger.error(f"Error calculating Optimal f position size: {e}")
            return 0.0
            
    def calculate_position_size(self, request: PositionSizingRequest) -> Dict[str, Any]:
        """Calculate position size using specified method."""
        try:
            position_size = 0.0
            method_used = request.method
            
            if request.method == 'kelly':
                if request.win_rate and request.avg_win and request.avg_loss:
                    position_size = self.calculate_kelly_position_size(
                        request.win_rate, request.avg_win, request.avg_loss, request.account_balance
                    )
                else:
                    method_used = 'fixed'
                    position_size = self.calculate_fixed_position_size(
                        request.account_balance, request.current_price
                    )
                    
            elif request.method == 'volatility':
                if request.volatility:
                    position_size = self.calculate_volatility_position_size(
                        request.volatility, request.account_balance, request.current_price
                    )
                else:
                    method_used = 'fixed'
                    position_size = self.calculate_fixed_position_size(
                        request.account_balance, request.current_price
                    )
                    
            elif request.method == 'optimal_f':
                if request.win_rate and request.avg_win and request.avg_loss:
                    position_size = self.calculate_optimal_f_position_size(
                        request.win_rate, request.avg_win, request.avg_loss, request.account_balance
                    )
                else:
                    method_used = 'fixed'
                    position_size = self.calculate_fixed_position_size(
                        request.account_balance, request.current_price
                    )
                    
            else:  # fixed
                position_size = self.calculate_fixed_position_size(
                    request.account_balance, request.current_price
                )
                
            # Calculate number of units
            units = position_size / request.current_price if request.current_price > 0 else 0
            
            return {
                "position_size": position_size,
                "units": units,
                "method_used": method_used,
                "risk_percentage": (position_size / request.account_balance) * 100,
                "max_allowed": request.account_balance * self.get_config_value("max_position_size", 0.10)
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"error": str(e)}
            
    def assess_risk(self, request: RiskAssessmentRequest) -> Dict[str, Any]:
        """Assess risk for a potential trade."""
        try:
            # Calculate potential loss
            if request.stop_loss:
                if request.side == 'buy':
                    potential_loss = (request.entry_price - request.stop_loss) / request.entry_price
                else:
                    potential_loss = (request.stop_loss - request.entry_price) / request.entry_price
            else:
                potential_loss = self.get_config_value("stop_loss_default", 0.02)
                
            # Calculate potential profit
            if request.take_profit:
                if request.side == 'buy':
                    potential_profit = (request.take_profit - request.entry_price) / request.entry_price
                else:
                    potential_profit = (request.entry_price - request.take_profit) / request.entry_price
            else:
                potential_profit = self.get_config_value("take_profit_default", 0.04)
                
            # Calculate risk-reward ratio
            risk_reward_ratio = potential_profit / potential_loss if potential_loss > 0 else 0
            
            # Calculate portfolio risk
            portfolio_risk = (request.position_size * potential_loss) / request.account_balance
            
            # Check correlation risk
            correlation_risk = 0.0
            if request.existing_positions:
                correlation_risk = self.calculate_correlation_risk(request.symbol, request.existing_positions)
                
            # Risk assessment
            risk_level = "low"
            max_portfolio_risk = self.get_config_value("max_portfolio_risk", 0.05)
            if portfolio_risk > max_portfolio_risk:
                risk_level = "high"
            elif portfolio_risk > max_portfolio_risk * 0.5:
                risk_level = "medium"
                
            # Recommendations
            recommendations = []
            max_portfolio_risk = self.get_config_value("max_portfolio_risk", 0.05)
            correlation_threshold = self.get_config_value("correlation_threshold", 0.7)
            if portfolio_risk > max_portfolio_risk:
                recommendations.append("Reduce position size to meet risk limits")
            if risk_reward_ratio < 2.0:
                recommendations.append("Consider improving risk-reward ratio")
            if correlation_risk > correlation_threshold:
                recommendations.append("High correlation with existing positions - consider diversification")
                
            return {
                "risk_level": risk_level,
                "portfolio_risk": portfolio_risk,
                "potential_loss": potential_loss,
                "potential_profit": potential_profit,
                "risk_reward_ratio": risk_reward_ratio,
                "correlation_risk": correlation_risk,
                "recommendations": recommendations,
                "approved": portfolio_risk <= self.get_config_value("max_portfolio_risk", 0.05)
            }
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return {"error": str(e)}
            
    def calculate_stop_loss(self, request: StopLossRequest) -> Dict[str, Any]:
        """Calculate optimal stop-loss level."""
        try:
            if request.percentage:
                # Fixed percentage stop loss
                if request.side == 'buy':
                    stop_loss = request.entry_price * (1 - request.percentage)
                else:
                    stop_loss = request.entry_price * (1 + request.percentage)
            elif request.volatility:
                # Volatility-based stop loss
                volatility_stop = request.volatility * request.atr_multiplier
                if request.side == 'buy':
                    stop_loss = request.entry_price * (1 - volatility_stop)
                else:
                    stop_loss = request.entry_price * (1 + volatility_stop)
            else:
                # Default stop loss
                if request.side == 'buy':
                    stop_loss = request.entry_price * (1 - self.get_config_value("stop_loss_default", 0.02))
                else:
                    stop_loss = request.entry_price * (1 + self.get_config_value("stop_loss_default", 0.02))
                    
            # Calculate stop loss distance
            stop_distance = abs(stop_loss - request.entry_price) / request.entry_price
            
            return {
                "stop_loss": stop_loss,
                "stop_distance": stop_distance,
                "method": "percentage" if request.percentage else "volatility" if request.volatility else "default"
            }
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return {"error": str(e)}
            
    def calculate_correlation_risk(self, symbol: str, positions: List[Dict[str, Any]]) -> float:
        """Calculate correlation risk with existing positions."""
        try:
            # Simplified correlation calculation
            # In a real implementation, this would use historical price data
            total_correlation = 0.0
            count = 0
            
            for position in positions:
                if position.get('symbol') != symbol:
                    # Mock correlation calculation
                    correlation = 0.5  # Placeholder
                    total_correlation += correlation
                    count += 1
                    
            return total_correlation / count if count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {e}")
            return 0.0
            
    def check_circuit_breaker(self, request: CircuitBreakerRequest) -> Dict[str, Any]:
        """Check if circuit breaker should be triggered."""
        try:
            if not self.get_config_value("circuit_breaker_enabled", True):
                return {"triggered": False, "reason": "Circuit breaker disabled"}
                
            # Calculate price change
            price_change = abs(request.current_price - request.previous_price) / request.previous_price
            
            circuit_breaker_threshold = self.get_config_value("circuit_breaker_threshold", 0.10)
            if price_change > circuit_breaker_threshold:
                # Check cooldown
                last_trigger = self.circuit_breaker_status.get(request.symbol, {}).get('last_trigger')
                if last_trigger:
                    time_since_trigger = (request.timestamp - last_trigger).total_seconds()
                    circuit_breaker_cooldown = self.get_config_value("circuit_breaker_cooldown", 300)
                    if time_since_trigger < circuit_breaker_cooldown:
                        return {"triggered": False, "reason": "Circuit breaker in cooldown"}
                        
                # Trigger circuit breaker
                self.circuit_breaker_status[request.symbol] = {
                    'triggered': True,
                    'last_trigger': request.timestamp,
                    'price_change': price_change
                }
                
                return {
                    "triggered": True,
                    "reason": f"Price change {price_change:.2%} exceeds threshold {circuit_breaker_threshold:.2%}",
                    "price_change": price_change
                }
                
            return {"triggered": False, "reason": "Price change within normal range"}
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return {"error": str(e)}
            
    def check_drawdown_protection(self, request: DrawdownProtectionRequest) -> Dict[str, Any]:
        """Check drawdown protection limits."""
        try:
            # Calculate current drawdown
            drawdown = (request.initial_balance - request.account_balance) / request.initial_balance
            
            # Record drawdown
            self.drawdown_history.append({
                'timestamp': request.timestamp,
                'drawdown': drawdown,
                'balance': request.account_balance
            })
            
            # Keep only recent history
            if len(self.drawdown_history) > 100:
                self.drawdown_history = self.drawdown_history[-100:]
                
            # Check limits
            hard_drawdown_limit = self.get_config_value("hard_drawdown_limit", 0.20)
            if drawdown > hard_drawdown_limit:
                return {
                    "action": "stop_trading",
                    "reason": f"Hard drawdown limit exceeded: {drawdown:.2%}",
                    "drawdown": drawdown,
                    "limit": hard_drawdown_limit
                }
            
            soft_drawdown_limit = self.get_config_value("soft_drawdown_limit", 0.10)
            if drawdown > soft_drawdown_limit:
                return {
                    "action": "reduce_position_sizes",
                    "reason": f"Soft drawdown limit exceeded: {drawdown:.2%}",
                    "drawdown": drawdown,
                    "limit": soft_drawdown_limit
                }
            else:
                return {
                    "action": "continue_trading",
                    "reason": "Drawdown within acceptable limits",
                    "drawdown": drawdown
                }
                
        except Exception as e:
            logger.error(f"Error checking drawdown protection: {e}")
            return {"error": str(e)}
            
    def check_daily_loss_limit(self, current_balance: float, initial_balance: float) -> Dict[str, Any]:
        """Check daily loss limits."""
        try:
            # Calculate daily loss
            daily_loss = (initial_balance - current_balance) / initial_balance
            
            # Record daily loss
            self.daily_loss_history.append({
                'timestamp': datetime.now(),
                'daily_loss': daily_loss,
                'balance': current_balance
            })
            
            # Keep only recent history
            if len(self.daily_loss_history) > 30:
                self.daily_loss_history = self.daily_loss_history[-30:]
                
            # Check limits
            daily_loss_hard_limit = self.get_config_value("daily_loss_hard_limit", 0.15)
            if daily_loss > daily_loss_hard_limit:
                return {
                    "action": "stop_trading",
                    "reason": f"Hard daily loss limit exceeded: {daily_loss:.2%}",
                    "daily_loss": daily_loss,
                    "limit": daily_loss_hard_limit
                }
            
            daily_loss_soft_limit = self.get_config_value("daily_loss_soft_limit", 0.08)
            if daily_loss > daily_loss_soft_limit:
                return {
                    "action": "reduce_position_sizes",
                    "reason": f"Soft daily loss limit exceeded: {daily_loss:.2%}",
                    "daily_loss": daily_loss,
                    "limit": daily_loss_soft_limit
                }
            else:
                return {
                    "action": "continue_trading",
                    "reason": "Daily loss within acceptable limits",
                    "daily_loss": daily_loss
                }
                
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return {"error": str(e)}
            
    def assess_portfolio_risk(self, request: PortfolioRiskRequest) -> Dict[str, Any]:
        """Assess overall portfolio risk."""
        try:
            if not request.positions:
                return {
                    "total_risk": 0.0,
                    "portfolio_value": request.account_balance,
                    "risk_level": "low",
                    "recommendations": []
                }
                
            # Calculate portfolio metrics
            total_value = request.account_balance
            total_risk = 0.0
            position_risks = []
            
            for position in request.positions:
                position_value = position.get('value', 0)
                position_risk = position.get('risk', 0)
                
                total_value += position_value
                total_risk += position_risk
                position_risks.append({
                    'symbol': position.get('symbol'),
                    'value': position_value,
                    'risk': position_risk,
                    'risk_percentage': (position_risk / total_value) * 100
                })
                
            # Calculate portfolio risk percentage
            portfolio_risk_percentage = (total_risk / total_value) * 100
            
            # Determine risk level
            risk_level = "low"
            if portfolio_risk_percentage > 10:
                risk_level = "high"
            elif portfolio_risk_percentage > 5:
                risk_level = "medium"
                
            # Generate recommendations
            recommendations = []
            if portfolio_risk_percentage > 10:
                recommendations.append("Consider reducing overall portfolio risk")
            if len(request.positions) < 3:
                recommendations.append("Consider diversifying across more assets")
            if any(pos['risk_percentage'] > 5 for pos in position_risks):
                recommendations.append("Consider reducing concentration in high-risk positions")
                
            return {
                "total_risk": total_risk,
                "portfolio_value": total_value,
                "portfolio_risk_percentage": portfolio_risk_percentage,
                "risk_level": risk_level,
                "position_risks": position_risks,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return {"error": str(e)}

class AgenticRiskAgent(BaseAgent):
    """Intelligent Risk Agent for autonomous risk management and position sizing"""
    
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
        system_message = """You are an intelligent Risk Agent for VolexSwarm, a cryptocurrency trading system.

Your capabilities include:
- Autonomous risk assessment and portfolio protection
- Position sizing algorithms and risk calculation
- Stop-loss and take-profit management
- Self-directed risk monitoring and adjustment
- Reasoning about risk-reward ratios and portfolio exposure

You can:
1. Calculate optimal position sizes using various algorithms (Kelly Criterion, Volatility-based, Fixed)
2. Assess portfolio risk and implement protection measures
3. Manage stop-loss and take-profit levels
4. Monitor drawdown and implement circuit breakers
5. Optimize risk-reward ratios for trades
6. Analyze correlation risks and portfolio diversification
7. Implement daily loss limits and drawdown protection

Your responsibilities:
- Calculate safe position sizes based on account balance and risk tolerance
- Assess risk for potential trades and provide recommendations
- Monitor portfolio risk and trigger protection measures when needed
- Implement circuit breakers during extreme market conditions
- Track drawdown and daily loss limits
- Provide risk insights and optimization recommendations

Available position sizing methods:
- Kelly Criterion: Optimal position sizing based on win rate and profit/loss ratios
- Volatility-based: Position sizing adjusted for market volatility
- Fixed percentage: Simple percentage-based position sizing
- Optimal f: Advanced position sizing method

Always explain your risk decisions and protection measures.
Be proactive in identifying and mitigating risks.
Learn from risk management performance to improve protection over time.
Prioritize capital preservation and risk control in all decisions.
Consider market conditions and volatility when calculating position sizes."""

        config = AgentConfig(
            name="AgenticRiskAgent",
            system_message=system_message,
            llm_config=llm_config
        )
        super().__init__(config)
        
        # Initialize risk manager
        self.risk_manager = RiskManager()
        self.db_client = None
        self.ws_client = None
        self.risk_history = []
        self.performance_metrics = {
            "total_risk_assessments": 0,
            "high_risk_rejections": 0,
            "circuit_breaker_triggers": 0,
            "drawdown_protection_actions": 0,
            "average_position_size": 0.0,
            "average_risk_level": "low"
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
                agent_config = get_agent_config("risk")
                
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
            
            # Initialize risk manager with dynamic configuration
            await self.risk_manager.initialize()
            
            # Initialize WebSocket client for real-time communication
            self.ws_client = AgentWebSocketClient("agentic_risk")
            await self.ws_client.connect()
            
            logger.info("Agentic Risk Agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Agentic Risk Agent: {e}")
            return False
            
    async def shutdown(self):
        """Shutdown the agent."""
        try:
            if self.ws_client:
                await self.ws_client.disconnect()
            logger.info("Agentic Risk Agent shutdown successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            
    async def calculate_position_size(self, request: PositionSizingRequest) -> Dict[str, Any]:
        """Calculate optimal position size."""
        try:
            result = self.risk_manager.calculate_position_size(request)
            
            # Record risk assessment
            self.risk_history.append({
                "timestamp": datetime.now(),
                "symbol": request.symbol,
                "method": request.method,
                "position_size": result.get("position_size", 0),
                "risk_percentage": result.get("risk_percentage", 0)
            })
            
            # Update performance metrics
            self.performance_metrics["total_risk_assessments"] += 1
            if result.get("position_size", 0) > 0:
                self.performance_metrics["average_position_size"] = (
                    (self.performance_metrics["average_position_size"] * (self.performance_metrics["total_risk_assessments"] - 1) + 
                     result.get("position_size", 0)) / self.performance_metrics["total_risk_assessments"]
                )
                
            # Send real-time update
            if self.ws_client:
                await self.ws_client.send_message(
                    MessageType.RISK_UPDATE,
                    {
                        "agent": "agentic_risk",
                        "action": "position_size_calculated",
                        "data": result
                    }
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return {"error": str(e)}
            
    async def assess_risk(self, request: RiskAssessmentRequest) -> Dict[str, Any]:
        """Assess risk for a potential trade."""
        try:
            result = self.risk_manager.assess_risk(request)
            
            # Update performance metrics
            if result.get("risk_level") == "high":
                self.performance_metrics["high_risk_rejections"] += 1
                
            # Send real-time update
            if self.ws_client:
                await self.ws_client.send_message(
                    MessageType.RISK_UPDATE,
                    {
                        "agent": "agentic_risk",
                        "action": "risk_assessed",
                        "data": result
                    }
                )
                
            return result
            
        except Exception as e:
            logger.error(f"Error assessing risk: {e}")
            return {"error": str(e)}
            
    async def calculate_stop_loss(self, request: StopLossRequest) -> Dict[str, Any]:
        """Calculate optimal stop-loss level."""
        try:
            result = self.risk_manager.calculate_stop_loss(request)
            return result
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {e}")
            return {"error": str(e)}
            
    async def check_circuit_breaker(self, request: CircuitBreakerRequest) -> Dict[str, Any]:
        """Check if circuit breaker should be triggered."""
        try:
            result = self.risk_manager.check_circuit_breaker(request)
            
            if result.get("triggered", False):
                self.performance_metrics["circuit_breaker_triggers"] += 1
                
                # Send real-time alert
                if self.ws_client:
                    await self.ws_client.send_message(
                        MessageType.RISK_UPDATE,
                        {
                            "agent": "agentic_risk",
                            "action": "circuit_breaker_triggered",
                            "data": result
                        }
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {e}")
            return {"error": str(e)}
            
    async def check_drawdown_protection(self, request: DrawdownProtectionRequest) -> Dict[str, Any]:
        """Check drawdown protection limits."""
        try:
            result = self.risk_manager.check_drawdown_protection(request)
            
            if result.get("action") in ["stop_trading", "reduce_position_sizes"]:
                self.performance_metrics["drawdown_protection_actions"] += 1
                
                # Send real-time alert
                if self.ws_client:
                    await self.ws_client.send_message(
                        MessageType.RISK_UPDATE,
                        {
                            "agent": "agentic_risk",
                            "action": "drawdown_protection_triggered",
                            "data": result
                        }
                    )
                    
            return result
            
        except Exception as e:
            logger.error(f"Error checking drawdown protection: {e}")
            return {"error": str(e)}
            
    async def check_daily_loss_limit(self, current_balance: float, initial_balance: float) -> Dict[str, Any]:
        """Check daily loss limits."""
        try:
            result = self.risk_manager.check_daily_loss_limit(current_balance, initial_balance)
            return result
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {e}")
            return {"error": str(e)}
            
    async def assess_portfolio_risk(self, request: PortfolioRiskRequest) -> Dict[str, Any]:
        """Assess overall portfolio risk."""
        try:
            result = self.risk_manager.assess_portfolio_risk(request)
            
            # Update average risk level
            if result.get("risk_level"):
                self.performance_metrics["average_risk_level"] = result["risk_level"]
                
            return result
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {e}")
            return {"error": str(e)}
            
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and health information."""
        return {
            "agent": "agentic_risk",
            "status": "healthy",
            "total_risk_assessments": self.performance_metrics["total_risk_assessments"],
            "high_risk_rejections": self.performance_metrics["high_risk_rejections"],
            "circuit_breaker_triggers": self.performance_metrics["circuit_breaker_triggers"],
            "drawdown_protection_actions": self.performance_metrics["drawdown_protection_actions"],
            "average_position_size": self.performance_metrics["average_position_size"],
            "average_risk_level": self.performance_metrics["average_risk_level"],
            "risk_history_count": len(self.risk_history),
            "timestamp": datetime.now()
        }

# Global instance for integration with agentic framework
agentic_risk_agent = None

async def initialize_agentic_risk_agent(llm_config: Dict[str, Any]) -> AgenticRiskAgent:
    """Initialize the agentic risk agent."""
    global agentic_risk_agent
    
    if agentic_risk_agent is None:
        agentic_risk_agent = AgenticRiskAgent(llm_config)
        await agentic_risk_agent.initialize()
        
    return agentic_risk_agent

async def shutdown_agentic_risk_agent():
    """Shutdown the agentic risk agent."""
    global agentic_risk_agent
    
    if agentic_risk_agent:
        await agentic_risk_agent.shutdown()
        agentic_risk_agent = None 