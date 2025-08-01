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
        Index('idx_trades_order_id', 'order_id'),
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
        UniqueConstraint('exchange', 'symbol', 'timestamp', name='uq_portfolio_position'),
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
        Index('idx_performance_strategy_date', 'strategy_id', 'date'),
        Index('idx_performance_date', 'date'),
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


class Conversation(Base):
    """Conversation sessions for conversational AI (Phase 3)."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    session_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_interaction = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)
    user_preferences = Column(JSONB, default={})  # User's trading preferences
    trading_context = Column(JSONB, default={})  # Budget, risk tolerance, goals
    conversation_metadata = Column(JSONB, default={})  # Additional metadata
    
    # Relationships
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    tasks = relationship("ConversationTask", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversations_user_active', 'user_id', 'is_active'),
        Index('idx_conversations_last_interaction', 'last_interaction'),
        Index('idx_conversations_session_start', 'session_start'),
    )


class ConversationMessage(Base):
    """Individual messages in a conversation (Phase 3)."""
    __tablename__ = "conversation_messages"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(100), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    message_order = Column(Integer, nullable=False)  # Order within conversation
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    message_metadata = Column(JSONB, default={})  # Additional message data
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index('idx_conv_messages_conv_order', 'conversation_id', 'message_order'),
        Index('idx_conv_messages_timestamp', 'timestamp'),
        Index('idx_conv_messages_role_timestamp', 'role', 'timestamp'),
        UniqueConstraint('conversation_id', 'message_order', name='uq_message_order'),
    )


class ConversationTask(Base):
    """Tasks decomposed from conversations (Phase 3)."""
    __tablename__ = "conversation_tasks"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), nullable=False, unique=True, index=True)
    conversation_id = Column(String(100), ForeignKey("conversations.conversation_id"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False, index=True)  # TaskType enum values
    description = Column(Text, nullable=False)
    agent = Column(String(50), nullable=False)  # Which agent should handle this
    parameters = Column(JSONB, default={})  # Task parameters
    status = Column(String(20), nullable=False, default='pending', index=True)  # TaskStatus enum values
    priority = Column(Integer, default=1)  # Task priority (1=highest, 5=lowest)
    dependencies = Column(JSONB, default=[])  # Task IDs this task depends on
    result = Column(JSONB)  # Task execution result
    error = Column(Text)  # Error message if task failed
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    started_at = Column(DateTime)  # When task execution began
    completed_at = Column(DateTime)  # When task completed/failed
    
    # Relationships
    conversation = relationship("Conversation", back_populates="tasks")
    
    # Indexes
    __table_args__ = (
        Index('idx_conv_tasks_conv_created', 'conversation_id', 'created_at'),
        Index('idx_conv_tasks_status_created', 'status', 'created_at'),
        Index('idx_conv_tasks_type_created', 'task_type', 'created_at'),
        Index('idx_conv_tasks_agent_status', 'agent', 'status'),
        Index('idx_conv_tasks_priority_status', 'priority', 'status'),
    )


class ConversationContext(Base):
    """Persistent conversation context and state (Phase 3)."""
    __tablename__ = "conversation_context"
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(100), ForeignKey("conversations.conversation_id"), nullable=False, unique=True, index=True)
    context_data = Column(JSONB, nullable=False, default={})  # Serialized conversation context
    symbols_mentioned = Column(JSONB, default=[])  # Symbols discussed in conversation
    strategies_discussed = Column(JSONB, default=[])  # Strategies mentioned
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    conversation = relationship("Conversation", uselist=False)
    
    # Indexes
    __table_args__ = (
        Index('idx_conv_context_updated', 'last_updated'),
    )


class UserProfile(Base):
    """User profiles for personalized trading assistance (Phase 3)."""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    risk_tolerance = Column(String(20), default='medium')  # low, medium, high
    trading_experience = Column(String(20), default='beginner')  # beginner, intermediate, advanced
    preferred_timeframes = Column(JSONB, default=['1h', '4h'])  # Preferred trading timeframes
    favorite_symbols = Column(JSONB, default=[])  # Frequently traded symbols
    trading_budget = Column(Float)  # Available trading capital
    goals = Column(JSONB, default={})  # Trading goals and targets
    restrictions = Column(JSONB, default={})  # Trading restrictions or limits
    preferences = Column(JSONB, default={})  # UI and notification preferences
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_profiles_last_active', 'last_active'),
        Index('idx_user_profiles_risk_tolerance', 'risk_tolerance'),
        Index('idx_user_profiles_trading_experience', 'trading_experience'),
    )


class TaskExecution(Base):
    """Task execution history and audit trail (Phase 3)."""
    __tablename__ = "task_executions"
    
    id = Column(Integer, primary_key=True)
    execution_id = Column(String(100), nullable=False, unique=True, index=True)
    task_id = Column(String(100), ForeignKey("conversation_tasks.task_id"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    execution_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    execution_end = Column(DateTime)
    status = Column(String(20), nullable=False, default='started', index=True)  # started, completed, failed
    inputs = Column(JSONB, default={})  # Task inputs/parameters
    outputs = Column(JSONB)  # Task outputs/results
    error_details = Column(JSONB)  # Detailed error information
    execution_metadata = Column(JSONB, default={})  # Additional execution data
    
    # Relationships
    task = relationship("ConversationTask")
    
    # Indexes
    __table_args__ = (
        Index('idx_task_exec_task_start', 'task_id', 'execution_start'),
        Index('idx_task_exec_agent_start', 'agent_name', 'execution_start'),
        Index('idx_task_exec_status_start', 'status', 'execution_start'),
    )


# Utility functions for common operations
def create_trade_id() -> str:
    """Generate a unique trade ID."""
    return f"trade_{uuid.uuid4().hex[:16]}"


def create_conversation_id() -> str:
    """Generate a unique conversation ID."""
    return f"conv_{uuid.uuid4().hex[:16]}"


def create_task_id() -> str:
    """Generate a unique task ID."""
    return f"task_{uuid.uuid4().hex[:16]}"


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