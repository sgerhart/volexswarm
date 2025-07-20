"""
Structured logging framework for VolexSwarm agents.
Provides database logging and standard logging with consistent formatting.
"""

import logging
import json
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from functools import wraps
from sqlalchemy import func

from .db import get_session
from .models import AgentLog


class VolexSwarmLogger:
    """
    Structured logger for VolexSwarm agents.
    Logs to both database and standard output.
    """
    
    def __init__(self, agent_name: str, log_to_db: bool = True):
        """
        Initialize logger for an agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'research', 'signal')
            log_to_db: Whether to log to database
        """
        self.agent_name = agent_name
        self.log_to_db = log_to_db
        
        # Standard logger
        self.logger = logging.getLogger(f"volexswarm.{agent_name}")
        self.logger.setLevel(logging.INFO)
        
        # Create handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log_to_db(self, level: str, message: str, context: Optional[Dict] = None, 
                   traceback_text: Optional[str] = None) -> None:
        """Log message to database."""
        if not self.log_to_db:
            return
        
        try:
            session = get_session()
            log_entry = AgentLog(
                agent_name=self.agent_name,
                level=level.upper(),
                message=message,
                timestamp=datetime.utcnow(),
                log_context=context or {},
                traceback=traceback_text
            )
            session.add(log_entry)
            session.commit()
            session.close()
        except Exception as e:
            # Fallback to standard logging if DB fails
            self.logger.error(f"Failed to log to database: {e}")
    
    def debug(self, message: str, context: Optional[Dict] = None) -> None:
        """Log debug message."""
        self.logger.debug(message)
        self._log_to_db('DEBUG', message, context)
    
    def info(self, message: str, context: Optional[Dict] = None) -> None:
        """Log info message."""
        self.logger.info(message)
        self._log_to_db('INFO', message, context)
    
    def warning(self, message: str, context: Optional[Dict] = None) -> None:
        """Log warning message."""
        self.logger.warning(message)
        self._log_to_db('WARNING', message, context)
    
    def error(self, message: str, context: Optional[Dict] = None, 
              exception: Optional[Exception] = None) -> None:
        """Log error message."""
        self.logger.error(message)
        
        traceback_text = None
        if exception:
            traceback_text = traceback.format_exc()
        
        self._log_to_db('ERROR', message, context, traceback_text)
    
    def critical(self, message: str, context: Optional[Dict] = None, 
                 exception: Optional[Exception] = None) -> None:
        """Log critical message."""
        self.logger.critical(message)
        
        traceback_text = None
        if exception:
            traceback_text = traceback.format_exc()
        
        self._log_to_db('CRITICAL', message, context, traceback_text)
    
    @contextmanager
    def log_operation(self, operation_name: str, context: Optional[Dict] = None):
        """Context manager for logging operations."""
        start_time = datetime.utcnow()
        self.info(f"Starting operation: {operation_name}", context)
        
        try:
            yield
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.info(f"Completed operation: {operation_name} (took {duration:.2f}s)", 
                     {**(context or {}), 'duration': duration})
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.error(f"Failed operation: {operation_name} (took {duration:.2f}s)", 
                      {**(context or {}), 'duration': duration}, e)
            raise
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log trade execution."""
        context = {
            'trade_id': trade_data.get('trade_id'),
            'symbol': trade_data.get('symbol'),
            'side': trade_data.get('side'),
            'quantity': trade_data.get('quantity'),
            'price': trade_data.get('price'),
            'exchange': trade_data.get('exchange')
        }
        self.info(f"Trade executed: {trade_data.get('side', 'unknown')} {trade_data.get('quantity')} {trade_data.get('symbol')} @ {trade_data.get('price')}", context)
    
    def log_signal(self, signal_data: Dict[str, Any]) -> None:
        """Log trading signal."""
        context = {
            'symbol': signal_data.get('symbol'),
            'signal_type': signal_data.get('signal_type'),
            'strength': signal_data.get('strength'),
            'confidence': signal_data.get('confidence')
        }
        self.info(f"Signal generated: {signal_data.get('signal_type', 'unknown')} {signal_data.get('symbol')} (strength: {signal_data.get('strength', 0):.2f})", context)
    
    def log_performance(self, metrics: Dict[str, Any]) -> None:
        """Log performance metrics."""
        context = {
            'total_return': metrics.get('total_return'),
            'sharpe_ratio': metrics.get('sharpe_ratio'),
            'max_drawdown': metrics.get('max_drawdown'),
            'win_rate': metrics.get('win_rate')
        }
        self.info(f"Performance update: Return: {metrics.get('total_return', 0):.2%}, Sharpe: {metrics.get('sharpe_ratio', 0):.2f}, Drawdown: {metrics.get('max_drawdown', 0):.2%}", context)


def log_function_call(func):
    """Decorator to log function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(f"volexswarm.{func.__module__}")
        
        # Log function entry
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed with error: {e}")
            raise
    
    return wrapper


def get_agent_logs(agent_name: Optional[str] = None, level: Optional[str] = None, 
                   start_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
    """
    Retrieve agent logs from database.
    
    Args:
        agent_name: Filter by agent name
        level: Filter by log level
        start_time: Start time filter
        end_time: End time filter
        limit: Maximum number of logs to return
        
    Returns:
        List of log entries
    """
    try:
        session = get_session()
        query = session.query(AgentLog)
        
        if agent_name:
            query = query.filter(AgentLog.agent_name == agent_name)
        
        if level:
            query = query.filter(AgentLog.level == level.upper())
        
        if start_time:
            query = query.filter(AgentLog.timestamp >= start_time)
        
        if end_time:
            query = query.filter(AgentLog.timestamp <= end_time)
        
        logs = query.order_by(AgentLog.timestamp.desc()).limit(limit).all()
        
        result = []
        for log in logs:
            result.append({
                'id': log.id,
                'agent_name': log.agent_name,
                'level': log.level,
                'message': log.message,
                'timestamp': log.timestamp.isoformat(),
                'context': log.log_context,
                'traceback': log.traceback
            })
        
        session.close()
        return result
        
    except Exception as e:
        logging.error(f"Failed to retrieve logs: {e}")
        return []


def get_system_health() -> Dict[str, Any]:
    """
    Get system health information from logs.
    
    Returns:
        Dictionary with health metrics
    """
    try:
        session = get_session()
        
        # Get recent error count
        error_count = session.query(AgentLog).filter(
            AgentLog.level == 'ERROR',
            AgentLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        # Get recent warning count
        warning_count = session.query(AgentLog).filter(
            AgentLog.level == 'WARNING',
            AgentLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        # Get agent activity
        agent_activity = session.query(AgentLog.agent_name, 
                                     func.count(AgentLog.id)).filter(
            AgentLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).group_by(AgentLog.agent_name).all()
        
        session.close()
        
        return {
            'errors_last_hour': error_count,
            'warnings_last_hour': warning_count,
            'agent_activity': dict(agent_activity),
            'status': 'healthy' if error_count == 0 else 'degraded' if error_count < 5 else 'unhealthy'
        }
        
    except Exception as e:
        logging.error(f"Failed to get system health: {e}")
        return {'status': 'unknown', 'error': str(e)}


# Global logger instances
_loggers = {}


def get_logger(agent_name: str, log_to_db: bool = True) -> VolexSwarmLogger:
    """
    Get or create a logger for an agent.
    
    Args:
        agent_name: Name of the agent
        log_to_db: Whether to log to database
        
    Returns:
        VolexSwarmLogger instance
    """
    if agent_name not in _loggers:
        _loggers[agent_name] = VolexSwarmLogger(agent_name, log_to_db)
    
    return _loggers[agent_name] 