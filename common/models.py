"""
Database models for VolexSwarm.
Defines SQLAlchemy models for all trading data entities.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, 
    Text, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
import uuid

from .db import Base


class PriceData(Base):
    """Time-series price data for trading symbols."""
    __tablename__ = "price_data"
    
    # For TimescaleDB hypertables, use only time as primary key for partitioning
    time = Column(DateTime, nullable=False, primary_key=True)
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=False)
    open = Column(Float)  # Use standard column name
    high = Column(Float)  # Use standard column name
    low = Column(Float)   # Use standard column name
    close = Column(Float) # Use standard column name
    volume = Column(Float)
    timeframe = Column(String(10), default='1h')  # 1m, 5m, 1h, 4h, 1d
    
    # Additional indexes for efficient queries
    __table_args__ = (
        Index('idx_price_data_symbol_time', 'symbol', 'time'),
        Index('idx_price_data_exchange_symbol_time', 'exchange', 'symbol', 'time'),
    )


class Strategy(Base):
    """Trading strategy definitions."""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    agent_name = Column(String(50), nullable=False)  # research, signal, etc.
    parameters = Column(JSONB)  # Strategy parameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = relationship("Trade", back_populates="strategy")
    backtests = relationship("Backtest", back_populates="strategy")
    signals = relationship("Signal", back_populates="strategy")


class Order(Base):
    """Order records for tracking order lifecycle."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True)
    order_id = Column(String(100), unique=True)  # Exchange order ID
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), default='market')  # market, limit, stop
    quantity = Column(Float, nullable=False)
    price = Column(Float)  # Optional for market orders
    stop_price = Column(Float)  # For stop orders
    status = Column(String(20), default='pending')  # pending, filled, cancelled, failed
    filled_quantity = Column(Float, default=0.0)
    remaining_quantity = Column(Float)
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order_metadata = Column(JSONB)  # Additional order metadata
    
    # Relationships
    strategy = relationship("Strategy")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_orders_symbol_created', 'symbol', 'created_at'),
        Index('idx_orders_strategy_created', 'strategy_id', 'created_at'),
        Index('idx_orders_exchange_created', 'exchange', 'created_at'),
        Index('idx_orders_status_created', 'status', 'created_at'),
    )


class Trade(Base):
    """Trade execution records."""
    __tablename__ = "trades"
    
    # For TimescaleDB hypertables, use executed_at as primary key
    executed_at = Column(DateTime, nullable=False, primary_key=True)
    trade_id = Column(String(100), unique=True)  # Exchange trade ID
    order_id = Column(String(100))  # Reference to order
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False)
    exchange = Column(String(50), nullable=False)
    side = Column(String(10), nullable=False)  # buy, sell
    order_type = Column(String(20), default='market')  # market, limit, stop
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(20), default='filled')  # pending, filled, cancelled, failed
    fees = Column(Float, default=0.0)
    fees_currency = Column(String(10), default='USD')
    trade_metadata = Column(JSONB)  # Additional trade metadata
    
    # Relationships
    strategy = relationship("Strategy", back_populates="trades")
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_trades_symbol_executed', 'symbol', 'executed_at'),
        Index('idx_trades_strategy_executed', 'strategy_id', 'executed_at'),
        Index('idx_trades_exchange_executed', 'exchange', 'executed_at'),
        Index('idx_trades_side_executed', 'side', 'executed_at'),
    )


class Signal(Base):
    """Trading signals generated by agents."""
    __tablename__ = "signals"
    
    # For TimescaleDB hypertables, use timestamp as primary key
    timestamp = Column(DateTime, nullable=False, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(20), nullable=False)  # buy, sell, hold
    strength = Column(Float)  # Signal strength (0-1)
    confidence = Column(Float)  # Confidence level (0-1)
    timeframe = Column(String(10), default='1h')
    indicators = Column(JSONB)  # Technical indicators used
    signal_metadata = Column(JSONB)  # Additional signal data
    
    # Relationships
    strategy = relationship("Strategy", back_populates="signals")
    
    # Indexes
    __table_args__ = (
        Index('idx_signals_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_signals_strategy_timestamp', 'strategy_id', 'timestamp'),
        Index('idx_signals_type_timestamp', 'signal_type', 'timestamp'),
        Index('idx_signals_timeframe_timestamp', 'timeframe', 'timestamp'),
    )


class Backtest(Base):
    """Backtest results and configurations."""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    name = Column(String(100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    symbols = Column(JSONB)  # List of symbols tested
    parameters = Column(JSONB)  # Strategy parameters used
    results = Column(JSONB)  # Performance metrics
    trades = Column(JSONB)  # All trades from backtest
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='completed')  # running, completed, failed
    
    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    
    # Indexes
    __table_args__ = (
        Index('idx_backtests_strategy_created', 'strategy_id', 'created_at'),
        Index('idx_backtests_status_created', 'status', 'created_at'),
        Index('idx_backtests_date_range', 'start_date', 'end_date'),
    )


class AgentLog(Base):
    """Agent activity and system logs."""
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    agent_name = Column(String(50), nullable=False)
    level = Column(String(10), nullable=False)  # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    agent_metadata = Column("metadata", JSONB)  # Legacy metadata column (mapped to avoid SQLAlchemy conflict)
    log_context = Column(JSONB)  # Additional context data
    traceback = Column(Text)  # Error traceback if applicable
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_logs_agent_timestamp', 'agent_name', 'timestamp'),
        Index('idx_agent_logs_level_timestamp', 'level', 'timestamp'),
        Index('idx_agent_logs_timestamp', 'timestamp'),
    )


class SystemConfig(Base):
    """System configuration and settings."""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False, unique=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(50))  # Which agent updated this
    
    # Indexes
    __table_args__ = (
        Index('idx_system_config_key', 'key'),
        Index('idx_system_config_updated', 'updated_at'),
    )


class Portfolio(Base):
    """Portfolio positions and balances."""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    exchange = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    quantity = Column(Float, nullable=False)
    average_price = Column(Float)
    current_price = Column(Float)
    unrealized_pnl = Column(Float)
    realized_pnl = Column(Float)
    
    # Indexes
    __table_args__ = (
        Index('idx_portfolios_exchange_symbol_timestamp', 'exchange', 'symbol', 'timestamp'),
        Index('idx_portfolios_timestamp', 'timestamp'),
    )


class PerformanceMetrics(Base):
    """Performance metrics and analytics."""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))
    date = Column(DateTime, nullable=False, index=True)
    total_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    average_win = Column(Float)
    average_loss = Column(Float)
    metrics_metadata = Column(JSONB)  # Additional metrics
    
    # Indexes
    __table_args__ = (
        Index('idx_performance_metrics_strategy_date', 'strategy_id', 'date'),
        Index('idx_performance_metrics_date', 'date'),
    )


class MarketData(Base):
    """Additional market data beyond price (sentiment, news, etc.)."""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)  # sentiment, news, volume_profile, etc.
    source = Column(String(100))  # Data source
    data = Column(JSONB, nullable=False)  # The actual data
    confidence = Column(Float)  # Data quality/confidence score
    
    # Indexes
    __table_args__ = (
        Index('idx_market_data_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_market_data_type_timestamp', 'data_type', 'timestamp'),
    )


class ProductionStrategy(Base):
    """Production strategy model for promoted strategies."""
    __tablename__ = "production_strategies"
    
    id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    parameters = Column(JSONB)  # Strategy parameters
    risk_profile = Column(String(20), default="balanced")
    status = Column(String(20), default="active")  # active, paused, inactive, deactivated
    allocation = Column(JSONB)  # Capital allocation settings
    risk_limits = Column(JSONB)  # Risk management limits
    monitoring_config = Column(JSONB)  # Monitoring configuration
    strategy_metadata = Column(JSONB)  # Additional metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_production_strategies_status', 'status'),
        Index('idx_production_strategies_symbol', 'symbol'),
        Index('idx_production_strategies_type', 'type'),
        Index('idx_production_strategies_created', 'created_at'),
        Index('idx_production_strategies_updated', 'updated_at'),
    )


class PortfolioPerformance(Base):
    """Portfolio performance tracking for starting balances and returns."""
    __tablename__ = "portfolio_performance"
    
    id = Column(Integer, primary_key=True)
    exchange = Column(String(50), nullable=False, unique=True)  # One record per exchange
    initial_balance = Column(Float, nullable=False)  # Starting portfolio value
    initial_timestamp = Column(DateTime, nullable=False, index=True)  # When balance was first recorded
    current_balance = Column(Float, nullable=False)  # Current portfolio value
    last_updated = Column(DateTime, nullable=False, index=True)  # Last update timestamp
    absolute_return = Column(Float, default=0.0)  # Absolute dollar return
    total_return_percentage = Column(Float, default=0.0)  # Percentage return
    realized_pnl = Column(Float, default=0.0)  # Realized profit/loss
    unrealized_pnl = Column(Float, default=0.0)  # Unrealized profit/loss
    daily_return = Column(Float, default=0.0)  # Daily return amount
    annualized_return = Column(Float, default=0.0)  # Annualized return percentage
    days_elapsed = Column(Integer, default=0)  # Days since initial balance
    performance_metadata = Column(JSONB)  # Additional performance data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_portfolio_performance_exchange', 'exchange'),
        Index('idx_portfolio_performance_timestamp', 'initial_timestamp'),
        Index('idx_portfolio_performance_last_updated', 'last_updated'),
        UniqueConstraint('exchange', name='uq_portfolio_performance_exchange'),
    )


class PortfolioHistory(Base):
    """Portfolio value history over time for charting."""
    __tablename__ = "portfolio_history"
    
    id = Column(Integer, primary_key=True)
    exchange = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    portfolio_value = Column(Float, nullable=False)
    usdt_balance = Column(Float, default=0.0)
    btc_balance = Column(Float, default=0.0)
    btc_price = Column(Float, default=0.0)
    total_positions_value = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    total_return_percentage = Column(Float, default=0.0)
    daily_return = Column(Float, default=0.0)
    annualized_return = Column(Float, default=0.0)
    performance_metadata = Column(JSONB)  # Renamed from metadata to avoid SQLAlchemy conflict
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient time-series queries
    __table_args__ = (
        Index('idx_portfolio_history_exchange_timestamp', 'exchange', 'timestamp'),
        Index('idx_portfolio_history_timestamp', 'timestamp'),
        Index('idx_portfolio_history_exchange', 'exchange'),
    )


# Utility functions for common operations
def create_trade_id() -> str:
    """Generate a unique trade ID."""
    return f"trade_{uuid.uuid4().hex[:16]}"


def get_timeframe_interval(timeframe: str) -> str:
    """Convert timeframe string to PostgreSQL interval."""
    timeframe_map = {
        '1m': '1 minute',
        '5m': '5 minutes',
        '15m': '15 minutes',
        '30m': '30 minutes',
        '1h': '1 hour',
        '4h': '4 hours',
        '1d': '1 day',
        '1w': '1 week'
    }
    return timeframe_map.get(timeframe, '1 hour') 