"""
VolexSwarm Risk Agent - Risk Management and Position Sizing
Handles position sizing algorithms, risk assessment, stop-loss management, and portfolio protection.
"""

import sys
import os
import logging
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import time
import json
import math

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Trade, Order

# Initialize structured logger
logger = get_logger("risk")

app = FastAPI(title="VolexSwarm Risk Agent", version="1.0.0")

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

# Risk management configuration
RISK_CONFIG = {
    "max_portfolio_risk": 0.02,  # 2% max risk per trade
    "max_position_size": 0.10,   # 10% max position size
    "max_drawdown": 0.15,        # 15% max drawdown
    "daily_loss_limit": 0.05,    # 5% daily loss limit
    "correlation_threshold": 0.7, # 70% correlation threshold
    "volatility_lookback": 30,   # 30 days for volatility calculation
    "kelly_fraction": 0.25,      # Conservative Kelly Criterion fraction
    "stop_loss_default": 0.02,   # 2% default stop loss
    "take_profit_default": 0.04, # 4% default take profit
    
    # Enhanced position sizing
    "max_position_per_symbol": 0.05,  # 5% max position per symbol
    "kelly_variants": {
        "full_kelly": 1.0,       # Full Kelly Criterion
        "half_kelly": 0.5,       # Half Kelly Criterion
        "quarter_kelly": 0.25,   # Quarter Kelly Criterion
        "eighth_kelly": 0.125    # Eighth Kelly Criterion
    },
    
    # Volatility-based sizing
    "volatility_multiplier": 1.0,
    "min_volatility": 0.01,      # 1% minimum volatility
    "max_volatility": 0.50,      # 50% maximum volatility
    
    # Circuit breakers
    "circuit_breaker_enabled": True,
    "circuit_breaker_threshold": 0.10,  # 10% market drop triggers circuit breaker
    "circuit_breaker_cooldown": 3600,   # 1 hour cooldown
    
    # Drawdown protection
    "drawdown_check_interval": 300,     # Check every 5 minutes
    "soft_drawdown_limit": 0.10,        # 10% soft limit
    "hard_drawdown_limit": 0.15,        # 15% hard limit
    
    # Daily limits
    "daily_loss_check_interval": 60,    # Check every minute
    "daily_loss_soft_limit": 0.03,      # 3% soft limit
    "daily_loss_hard_limit": 0.05,      # 5% hard limit
}


class PositionSizingRequest(BaseModel):
    """Request model for position sizing calculation."""
    symbol: str
    side: str  # 'buy' or 'sell'
    account_balance: float
    current_price: float
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    correlation: Optional[float] = None
    method: str = 'kelly'  # 'kelly', 'fixed', 'volatility', 'optimal_f'


class RiskAssessmentRequest(BaseModel):
    """Request model for risk assessment."""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    side: str  # 'buy' or 'sell'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    account_balance: float
    existing_positions: Optional[List[Dict[str, Any]]] = None


class StopLossRequest(BaseModel):
    """Request model for stop-loss calculation."""
    symbol: str
    entry_price: float
    current_price: float
    side: str  # 'buy' or 'sell'
    volatility: Optional[float] = None
    atr_multiplier: float = 2.0
    percentage: Optional[float] = None


class PortfolioRiskRequest(BaseModel):
    """Request model for portfolio risk assessment."""
    positions: List[Dict[str, Any]]
    account_balance: float
    risk_free_rate: float = 0.02


class EnhancedPositionSizingRequest(BaseModel):
    """Enhanced request model for position sizing with advanced features."""
    symbol: str
    side: str  # 'buy' or 'sell'
    account_balance: float
    current_price: float
    volatility: Optional[float] = None
    win_rate: Optional[float] = None
    avg_win: Optional[float] = None
    avg_loss: Optional[float] = None
    correlation: Optional[float] = None
    method: str = 'enhanced_kelly'  # 'enhanced_kelly', 'volatility_adaptive', 'correlation_adjusted'
    kelly_variant: str = 'quarter_kelly'  # 'full_kelly', 'half_kelly', 'quarter_kelly', 'eighth_kelly'
    existing_positions: Optional[List[Dict[str, Any]]] = None
    market_conditions: Optional[Dict[str, Any]] = None  # Market volatility, trend, etc.


class RiskLimitRequest(BaseModel):
    """Request model for risk limit management."""
    daily_loss_limit: Optional[float] = None
    max_drawdown_limit: Optional[float] = None
    max_position_per_symbol: Optional[float] = None
    circuit_breaker_enabled: Optional[bool] = None
    circuit_breaker_threshold: Optional[float] = None


class CircuitBreakerRequest(BaseModel):
    """Request model for circuit breaker status."""
    symbol: str
    current_price: float
    previous_price: float
    timestamp: datetime


class DrawdownProtectionRequest(BaseModel):
    """Request model for drawdown protection."""
    account_balance: float
    initial_balance: float
    current_positions: List[Dict[str, Any]]
    timestamp: datetime


class RiskManager:
    """Manages risk calculations and position sizing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.risk_metrics = {}
        
    def calculate_kelly_position_size(self, win_rate: float, avg_win: float, 
                                    avg_loss: float, account_balance: float) -> float:
        """Calculate position size using Kelly Criterion."""
        try:
            if win_rate <= 0 or win_rate >= 1:
                return 0.0
                
            # Kelly Criterion formula: f = (bp - q) / b
            # where b = odds received, p = probability of win, q = probability of loss
            b = avg_win / avg_loss if avg_loss > 0 else 1
            p = win_rate
            q = 1 - win_rate
            
            kelly_fraction = (b * p - q) / b
            
            # Apply conservative fraction
            kelly_fraction *= self.config['kelly_fraction']
            
            # Ensure it's within bounds
            kelly_fraction = max(0, min(kelly_fraction, self.config['max_position_size']))
            
            return kelly_fraction * account_balance
            
        except Exception as e:
            logger.error(f"Error calculating Kelly position size: {str(e)}")
            return 0.0
    
    def calculate_volatility_position_size(self, volatility: float, 
                                         account_balance: float, 
                                         current_price: float) -> float:
        """Calculate position size based on volatility."""
        try:
            if volatility <= 0:
                return 0.0
                
            # Risk per trade based on volatility
            risk_per_trade = self.config['max_portfolio_risk'] * account_balance
            
            # Position size = risk / (price * volatility)
            position_size = risk_per_trade / (current_price * volatility)
            
            # Ensure it doesn't exceed max position size
            max_position_value = self.config['max_position_size'] * account_balance
            position_value = position_size * current_price
            
            if position_value > max_position_value:
                position_size = max_position_value / current_price
                
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating volatility position size: {str(e)}")
            return 0.0
    
    def calculate_fixed_position_size(self, account_balance: float, 
                                    current_price: float) -> float:
        """Calculate fixed percentage position size."""
        try:
            position_value = self.config['max_position_size'] * account_balance
            return position_value / current_price
            
        except Exception as e:
            logger.error(f"Error calculating fixed position size: {str(e)}")
            return 0.0
    
    def calculate_optimal_f_position_size(self, win_rate: float, avg_win: float, 
                                        avg_loss: float, account_balance: float) -> float:
        """Calculate position size using Optimal F method."""
        try:
            if win_rate <= 0 or win_rate >= 1:
                return 0.0
                
            # Optimal F formula: f = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            optimal_f = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
            
            # Apply conservative fraction
            optimal_f *= self.config['kelly_fraction']
            
            # Ensure it's within bounds
            optimal_f = max(0, min(optimal_f, self.config['max_position_size']))
            
            return optimal_f * account_balance
            
        except Exception as e:
            logger.error(f"Error calculating Optimal F position size: {str(e)}")
            return 0.0
    
    def calculate_position_size(self, request: PositionSizingRequest) -> Dict[str, Any]:
        """Calculate optimal position size using specified method."""
        try:
            position_size = 0.0
            method_used = request.method
            
            if request.method == 'kelly':
                if request.win_rate and request.avg_win and request.avg_loss:
                    position_size = self.calculate_kelly_position_size(
                        request.win_rate, request.avg_win, request.avg_loss, 
                        request.account_balance
                    )
                else:
                    method_used = 'fixed'  # Fallback to fixed if missing data
                    
            elif request.method == 'volatility':
                if request.volatility:
                    position_size = self.calculate_volatility_position_size(
                        request.volatility, request.account_balance, request.current_price
                    )
                else:
                    method_used = 'fixed'  # Fallback to fixed if missing data
                    
            elif request.method == 'optimal_f':
                if request.win_rate and request.avg_win and request.avg_loss:
                    position_size = self.calculate_optimal_f_position_size(
                        request.win_rate, request.avg_win, request.avg_loss, 
                        request.account_balance
                    )
                else:
                    method_used = 'fixed'  # Fallback to fixed if missing data
                    
            else:  # fixed method
                position_size = self.calculate_fixed_position_size(
                    request.account_balance, request.current_price
                )
            
            # Calculate risk metrics
            position_value = position_size * request.current_price
            risk_amount = position_value * self.config['stop_loss_default']
            risk_percentage = (risk_amount / request.account_balance) * 100
            
            return {
                "position_size": position_size,
                "position_value": position_value,
                "risk_amount": risk_amount,
                "risk_percentage": risk_percentage,
                "method_used": method_used,
                "account_balance": request.account_balance,
                "symbol": request.symbol,
                "side": request.side,
                "current_price": request.current_price,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Position sizing calculation failed: {str(e)}")
    
    def assess_risk(self, request: RiskAssessmentRequest) -> Dict[str, Any]:
        """Assess risk for a potential trade."""
        try:
            # Calculate basic risk metrics
            position_value = request.position_size * request.current_price
            unrealized_pnl = (request.current_price - request.entry_price) * request.position_size
            
            if request.side == 'sell':
                unrealized_pnl = -unrealized_pnl
            
            # Calculate stop loss and take profit levels
            stop_loss = request.stop_loss or (request.entry_price * (1 - self.config['stop_loss_default']))
            take_profit = request.take_profit or (request.entry_price * (1 + self.config['take_profit_default']))
            
            if request.side == 'sell':
                stop_loss = request.stop_loss or (request.entry_price * (1 + self.config['stop_loss_default']))
                take_profit = request.take_profit or (request.entry_price * (1 - self.config['take_profit_default']))
            
            # Calculate risk/reward ratio
            risk = abs(request.entry_price - stop_loss) * request.position_size
            reward = abs(take_profit - request.entry_price) * request.position_size
            risk_reward_ratio = reward / risk if risk > 0 else 0
            
            # Calculate portfolio risk
            portfolio_risk = (risk / request.account_balance) * 100
            
            # Check risk limits
            risk_checks = {
                "within_position_limit": position_value <= (self.config['max_position_size'] * request.account_balance),
                "within_portfolio_risk": portfolio_risk <= (self.config['max_portfolio_risk'] * 100),
                "positive_risk_reward": risk_reward_ratio >= 1.5,
                "stop_loss_set": request.stop_loss is not None or stop_loss != request.entry_price
            }
            
            # Calculate correlation risk if existing positions provided
            correlation_risk = 0
            if request.existing_positions:
                correlation_risk = self.calculate_correlation_risk(request.symbol, request.existing_positions)
            
            return {
                "symbol": request.symbol,
                "position_size": request.position_size,
                "position_value": position_value,
                "entry_price": request.entry_price,
                "current_price": request.current_price,
                "unrealized_pnl": unrealized_pnl,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_amount": risk,
                "reward_amount": reward,
                "risk_reward_ratio": risk_reward_ratio,
                "portfolio_risk_percentage": portfolio_risk,
                "correlation_risk": correlation_risk,
                "risk_checks": risk_checks,
                "all_checks_passed": all(risk_checks.values()),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error assessing risk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")
    
    def calculate_stop_loss(self, request: StopLossRequest) -> Dict[str, Any]:
        """Calculate optimal stop loss levels."""
        try:
            stop_loss = None
            
            if request.percentage:
                # Fixed percentage stop loss
                if request.side == 'buy':
                    stop_loss = request.entry_price * (1 - request.percentage)
                else:
                    stop_loss = request.entry_price * (1 + request.percentage)
            elif request.volatility:
                # ATR-based stop loss
                atr = request.volatility * request.entry_price
                if request.side == 'buy':
                    stop_loss = request.entry_price - (atr * request.atr_multiplier)
                else:
                    stop_loss = request.entry_price + (atr * request.atr_multiplier)
            else:
                # Default stop loss
                if request.side == 'buy':
                    stop_loss = request.entry_price * (1 - self.config['stop_loss_default'])
                else:
                    stop_loss = request.entry_price * (1 + self.config['stop_loss_default'])
            
            # Calculate risk amount
            risk_amount = abs(request.entry_price - stop_loss)
            risk_percentage = (risk_amount / request.entry_price) * 100
            
            return {
                "symbol": request.symbol,
                "entry_price": request.entry_price,
                "current_price": request.current_price,
                "stop_loss": stop_loss,
                "risk_amount": risk_amount,
                "risk_percentage": risk_percentage,
                "side": request.side,
                "method": "percentage" if request.percentage else "atr" if request.volatility else "default",
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating stop loss: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Stop loss calculation failed: {str(e)}")
    
    def calculate_correlation_risk(self, symbol: str, positions: List[Dict[str, Any]]) -> float:
        """Calculate correlation risk with existing positions."""
        try:
            # This is a simplified correlation calculation
            # In a real implementation, you would use historical price data
            correlation_risk = 0.0
            
            for position in positions:
                if position['symbol'] == symbol:
                    correlation_risk += 1.0  # Perfect correlation with same symbol
                elif position['symbol'].split('/')[0] == symbol.split('/')[0]:
                    correlation_risk += 0.5  # Partial correlation with same base currency
                elif position['symbol'].split('/')[1] == symbol.split('/')[1]:
                    correlation_risk += 0.3  # Partial correlation with same quote currency
            
            return min(correlation_risk, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating correlation risk: {str(e)}")
            return 0.0
    
    def calculate_enhanced_kelly_position_size(self, request: EnhancedPositionSizingRequest) -> Dict[str, Any]:
        """Calculate position size using enhanced Kelly Criterion with multiple variants."""
        try:
            if not request.win_rate or not request.avg_win or not request.avg_loss:
                raise ValueError("Win rate, average win, and average loss are required for Kelly Criterion")
            
            # Calculate base Kelly fraction
            b = request.avg_win / request.avg_loss if request.avg_loss > 0 else 1
            p = request.win_rate
            q = 1 - request.win_rate
            
            base_kelly = (b * p - q) / b
            
            # Apply Kelly variant
            kelly_fraction = self.config['kelly_variants'].get(request.kelly_variant, 0.25)
            adjusted_kelly = base_kelly * kelly_fraction
            
            # Apply volatility adjustment
            volatility_adjustment = 1.0
            if request.volatility:
                volatility_adjustment = max(
                    self.config['min_volatility'] / request.volatility,
                    request.volatility / self.config['max_volatility']
                )
                volatility_adjustment = min(volatility_adjustment, 1.0)
            
            # Apply correlation adjustment
            correlation_adjustment = 1.0
            if request.existing_positions:
                correlation_risk = self.calculate_correlation_risk(request.symbol, request.existing_positions)
                correlation_adjustment = 1.0 - (correlation_risk * 0.5)  # Reduce size by up to 50% for high correlation
            
            # Calculate final position size
            final_kelly = adjusted_kelly * volatility_adjustment * correlation_adjustment
            final_kelly = max(0, min(final_kelly, self.config['max_position_size']))
            
            position_size = final_kelly * request.account_balance / request.current_price
            
            # Apply per-symbol limit
            max_position_value = self.config['max_position_per_symbol'] * request.account_balance
            position_value = position_size * request.current_price
            
            if position_value > max_position_value:
                position_size = max_position_value / request.current_price
            
            return {
                "position_size": position_size,
                "position_value": position_size * request.current_price,
                "kelly_fraction": base_kelly,
                "adjusted_kelly": adjusted_kelly,
                "volatility_adjustment": volatility_adjustment,
                "correlation_adjustment": correlation_adjustment,
                "final_kelly": final_kelly,
                "method": "enhanced_kelly",
                "kelly_variant": request.kelly_variant,
                "symbol": request.symbol,
                "side": request.side,
                "current_price": request.current_price,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating enhanced Kelly position size: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Enhanced Kelly calculation failed: {str(e)}")
    
    def calculate_volatility_adaptive_position_size(self, request: EnhancedPositionSizingRequest) -> Dict[str, Any]:
        """Calculate position size using volatility-adaptive sizing."""
        try:
            if not request.volatility:
                raise ValueError("Volatility is required for volatility-adaptive sizing")
            
            # Normalize volatility to 0-1 range
            normalized_volatility = max(
                self.config['min_volatility'],
                min(request.volatility, self.config['max_volatility'])
            )
            
            # Inverse relationship: higher volatility = smaller position
            volatility_factor = 1.0 - (normalized_volatility / self.config['max_volatility'])
            
            # Base position size (2% risk per trade)
            base_risk = self.config['max_portfolio_risk'] * request.account_balance
            base_position_size = base_risk / (request.current_price * normalized_volatility)
            
            # Apply volatility adjustment
            adjusted_position_size = base_position_size * volatility_factor * self.config['volatility_multiplier']
            
            # Apply limits
            max_position_value = min(
                self.config['max_position_size'] * request.account_balance,
                self.config['max_position_per_symbol'] * request.account_balance
            )
            
            position_value = adjusted_position_size * request.current_price
            if position_value > max_position_value:
                adjusted_position_size = max_position_value / request.current_price
            
            return {
                "position_size": adjusted_position_size,
                "position_value": adjusted_position_size * request.current_price,
                "volatility_factor": volatility_factor,
                "normalized_volatility": normalized_volatility,
                "base_position_size": base_position_size,
                "method": "volatility_adaptive",
                "symbol": request.symbol,
                "side": request.side,
                "current_price": request.current_price,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating volatility-adaptive position size: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Volatility-adaptive calculation failed: {str(e)}")
    
    def check_circuit_breaker(self, request: CircuitBreakerRequest) -> Dict[str, Any]:
        """Check if circuit breaker should be triggered."""
        try:
            if not self.config['circuit_breaker_enabled']:
                return {"triggered": False, "reason": "Circuit breaker disabled"}
            
            # Calculate price change percentage
            price_change = (request.current_price - request.previous_price) / request.previous_price
            
            # Check if threshold exceeded
            threshold_exceeded = abs(price_change) >= self.config['circuit_breaker_threshold']
            
            # Check cooldown (simplified - in real implementation, store last trigger time)
            cooldown_expired = True  # Placeholder
            
            triggered = threshold_exceeded and cooldown_expired
            
            return {
                "triggered": triggered,
                "price_change": price_change,
                "threshold": self.config['circuit_breaker_threshold'],
                "reason": f"Price change {price_change:.2%} exceeds threshold {self.config['circuit_breaker_threshold']:.2%}" if triggered else "No trigger",
                "symbol": request.symbol,
                "timestamp": request.timestamp
            }
            
        except Exception as e:
            logger.error(f"Error checking circuit breaker: {str(e)}")
            return {"triggered": False, "error": str(e)}
    
    def check_drawdown_protection(self, request: DrawdownProtectionRequest) -> Dict[str, Any]:
        """Check drawdown protection limits."""
        try:
            # Calculate current drawdown
            current_drawdown = (request.initial_balance - request.account_balance) / request.initial_balance
            
            # Calculate position values
            total_position_value = sum(pos.get('value', 0) for pos in request.current_positions)
            
            # Check soft and hard limits
            soft_limit_exceeded = current_drawdown >= self.config['soft_drawdown_limit']
            hard_limit_exceeded = current_drawdown >= self.config['hard_drawdown_limit']
            
            # Determine action
            action = "none"
            if hard_limit_exceeded:
                action = "close_all_positions"
            elif soft_limit_exceeded:
                action = "reduce_positions"
            
            return {
                "current_drawdown": current_drawdown,
                "soft_limit": self.config['soft_drawdown_limit'],
                "hard_limit": self.config['hard_drawdown_limit'],
                "soft_limit_exceeded": soft_limit_exceeded,
                "hard_limit_exceeded": hard_limit_exceeded,
                "action": action,
                "total_position_value": total_position_value,
                "account_balance": request.account_balance,
                "initial_balance": request.initial_balance,
                "timestamp": request.timestamp
            }
            
        except Exception as e:
            logger.error(f"Error checking drawdown protection: {str(e)}")
            return {"error": str(e)}
    
    def check_daily_loss_limit(self, current_balance: float, initial_balance: float) -> Dict[str, Any]:
        """Check daily loss limit."""
        try:
            daily_loss = (initial_balance - current_balance) / initial_balance
            
            soft_limit_exceeded = daily_loss >= self.config['daily_loss_soft_limit']
            hard_limit_exceeded = daily_loss >= self.config['daily_loss_hard_limit']
            
            action = "none"
            if hard_limit_exceeded:
                action = "stop_trading"
            elif soft_limit_exceeded:
                action = "reduce_risk"
            
            return {
                "daily_loss": daily_loss,
                "soft_limit": self.config['daily_loss_soft_limit'],
                "hard_limit": self.config['daily_loss_hard_limit'],
                "soft_limit_exceeded": soft_limit_exceeded,
                "hard_limit_exceeded": hard_limit_exceeded,
                "action": action,
                "current_balance": current_balance,
                "initial_balance": initial_balance,
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error checking daily loss limit: {str(e)}")
            return {"error": str(e)}
    
    def assess_portfolio_risk(self, request: PortfolioRiskRequest) -> Dict[str, Any]:
        """Assess overall portfolio risk."""
        try:
            total_value = request.account_balance
            total_pnl = 0
            total_risk = 0
            position_weights = []
            
            for position in request.positions:
                position_value = position.get('value', 0)
                position_pnl = position.get('unrealized_pnl', 0)
                position_risk = position.get('risk_amount', 0)
                
                total_value += position_value
                total_pnl += position_pnl
                total_risk += position_risk
                
                if total_value > 0:
                    weight = position_value / total_value
                    position_weights.append(weight)
            
            # Calculate portfolio metrics
            portfolio_return = (total_pnl / request.account_balance) * 100 if request.account_balance > 0 else 0
            portfolio_risk_percentage = (total_risk / request.account_balance) * 100 if request.account_balance > 0 else 0
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = (portfolio_return - request.risk_free_rate) / portfolio_risk_percentage if portfolio_risk_percentage > 0 else 0
            
            # Calculate maximum drawdown (simplified)
            max_drawdown = min(0, portfolio_return)
            
            # Risk checks
            risk_checks = {
                "within_drawdown_limit": abs(max_drawdown) <= self.config['max_drawdown'],
                "within_daily_loss_limit": portfolio_return >= -self.config['daily_loss_limit'],
                "diversified": len(request.positions) >= 3,  # At least 3 positions
                "position_concentration": max(position_weights) <= 0.3 if position_weights else True  # No position > 30%
            }
            
            return {
                "total_value": total_value,
                "total_pnl": total_pnl,
                "total_risk": total_risk,
                "portfolio_return": portfolio_return,
                "portfolio_risk_percentage": portfolio_risk_percentage,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "position_count": len(request.positions),
                "risk_checks": risk_checks,
                "all_checks_passed": all(risk_checks.values()),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error assessing portfolio risk: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Portfolio risk assessment failed: {str(e)}")


# Initialize risk manager
risk_manager = RiskManager(RISK_CONFIG)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    global vault_client, db_client
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized")
        
        # Get agent configuration
        config = get_agent_config("risk")
        if config:
            logger.info(f"Risk agent configuration loaded: {config}")
        
        logger.info("Risk Agent started successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Risk Agent: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Risk Agent shutting down")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Check Vault connection
        vault_connected = vault_client is not None
        
        # Check database connection
        db_connected = db_client is not None and db_health_check()
        
        # Check risk manager
        risk_manager_ready = risk_manager is not None
        
        status = "healthy" if all([vault_connected, db_connected, risk_manager_ready]) else "unhealthy"
        
        return {
            "status": status,
            "timestamp": datetime.now(),
            "components": {
                "vault": vault_connected,
                "database": db_connected,
                "risk_manager": risk_manager_ready
            },
            "agent": "risk"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e),
            "agent": "risk"
        }


@app.post("/position-size")
async def calculate_position_size(request: PositionSizingRequest):
    """Calculate optimal position size for a trade."""
    return risk_manager.calculate_position_size(request)


@app.post("/assess-risk")
async def assess_risk(request: RiskAssessmentRequest):
    """Assess risk for a potential trade."""
    return risk_manager.assess_risk(request)


@app.post("/stop-loss")
async def calculate_stop_loss(request: StopLossRequest):
    """Calculate optimal stop loss levels."""
    return risk_manager.calculate_stop_loss(request)


@app.post("/portfolio-risk")
async def assess_portfolio_risk(request: PortfolioRiskRequest):
    """Assess overall portfolio risk."""
    return risk_manager.assess_portfolio_risk(request)


@app.get("/config")
def get_risk_config():
    """Get current risk management configuration."""
    return {
        "config": RISK_CONFIG,
        "timestamp": datetime.now()
    }


@app.put("/config")
def update_risk_config(config: Dict[str, Any]):
    """Update risk management configuration."""
    global RISK_CONFIG
    try:
        # Validate configuration
        required_keys = [
            "max_portfolio_risk", "max_position_size", "max_drawdown",
            "daily_loss_limit", "correlation_threshold", "volatility_lookback",
            "kelly_fraction", "stop_loss_default", "take_profit_default"
        ]
        
        for key in required_keys:
            if key not in config:
                raise HTTPException(status_code=400, detail=f"Missing required config key: {key}")
        
        # Update configuration
        RISK_CONFIG.update(config)
        
        # Reinitialize risk manager with new config
        global risk_manager
        risk_manager = RiskManager(RISK_CONFIG)
        
        logger.info(f"Risk configuration updated: {config}")
        
        return {
            "message": "Risk configuration updated successfully",
            "config": RISK_CONFIG,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to update risk configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Configuration update failed: {str(e)}")


@app.get("/metrics")
def get_risk_metrics():
    """Get current risk metrics and statistics."""
    try:
        return {
            "agent": "risk",
            "metrics": {
                "total_requests": 0,  # Placeholder for actual metrics
                "average_response_time": 0.0,
                "error_rate": 0.0,
                "config_version": "1.0"
            },
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/enhanced-position-size")
async def calculate_enhanced_position_size(request: EnhancedPositionSizingRequest):
    """Calculate position size using enhanced methods."""
    try:
        if request.method == "enhanced_kelly":
            return risk_manager.calculate_enhanced_kelly_position_size(request)
        elif request.method == "volatility_adaptive":
            return risk_manager.calculate_volatility_adaptive_position_size(request)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {request.method}")
    except Exception as e:
        logger.error(f"Error in enhanced position sizing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/circuit-breaker")
async def check_circuit_breaker(request: CircuitBreakerRequest):
    """Check if circuit breaker should be triggered."""
    return risk_manager.check_circuit_breaker(request)


@app.post("/drawdown-protection")
async def check_drawdown_protection(request: DrawdownProtectionRequest):
    """Check drawdown protection limits."""
    return risk_manager.check_drawdown_protection(request)


@app.post("/daily-loss-limit")
async def check_daily_loss_limit(current_balance: float, initial_balance: float):
    """Check daily loss limit."""
    return risk_manager.check_daily_loss_limit(current_balance, initial_balance)


@app.put("/risk-limits")
async def update_risk_limits(request: RiskLimitRequest):
    """Update risk limits."""
    try:
        global RISK_CONFIG
        
        if request.daily_loss_limit is not None:
            RISK_CONFIG['daily_loss_limit'] = request.daily_loss_limit
        if request.max_drawdown_limit is not None:
            RISK_CONFIG['max_drawdown'] = request.max_drawdown_limit
        if request.max_position_per_symbol is not None:
            RISK_CONFIG['max_position_per_symbol'] = request.max_position_per_symbol
        if request.circuit_breaker_enabled is not None:
            RISK_CONFIG['circuit_breaker_enabled'] = request.circuit_breaker_enabled
        if request.circuit_breaker_threshold is not None:
            RISK_CONFIG['circuit_breaker_threshold'] = request.circuit_breaker_threshold
        
        # Update risk manager config
        risk_manager.config = RISK_CONFIG
        
        return {
            "message": "Risk limits updated successfully",
            "config": RISK_CONFIG,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error updating risk limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk-status")
async def get_risk_status():
    """Get comprehensive risk status."""
    try:
        return {
            "agent": "risk",
            "status": "active",
            "features": {
                "enhanced_kelly": True,
                "volatility_adaptive": True,
                "circuit_breaker": RISK_CONFIG['circuit_breaker_enabled'],
                "drawdown_protection": True,
                "daily_loss_limits": True,
                "correlation_adjustment": True
            },
            "config_summary": {
                "max_portfolio_risk": RISK_CONFIG['max_portfolio_risk'],
                "max_position_size": RISK_CONFIG['max_position_size'],
                "max_drawdown": RISK_CONFIG['max_drawdown'],
                "daily_loss_limit": RISK_CONFIG['daily_loss_limit'],
                "circuit_breaker_threshold": RISK_CONFIG['circuit_breaker_threshold']
            },
            "kelly_variants": list(RISK_CONFIG['kelly_variants'].keys()),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error getting risk status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009) 