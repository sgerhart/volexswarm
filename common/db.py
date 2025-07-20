"""
Database client module for VolexSwarm agents.
Provides TimescaleDB integration for storing trading data, backtests, and logs.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()


class DatabaseClient:
    """
    Client for interacting with TimescaleDB.
    Handles connections, migrations, and data operations for VolexSwarm.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database client.
        
        Args:
            db_url: Database connection URL (defaults to environment variables)
        """
        self.db_url = db_url or self._get_db_url()
        self.engine = None
        self.SessionLocal = None
        self.metadata = MetaData()
        
        # Initialize connection
        self._initialize_connection()
        
        # Create tables
        self._create_tables()
    
    def _get_db_url(self) -> str:
        """Get database URL from environment variables or Vault."""
        try:
            from .vault import get_database_credentials
            
            # Try to get credentials from Vault first
            db_creds = get_database_credentials("default")
            if db_creds:
                host = db_creds.get('host', 'db')
                port = db_creds.get('port', '5432')
                database = db_creds.get('database', 'volextrades')
                username = db_creds.get('username', 'volex')
                password = db_creds.get('password', 'volex_pass')
                
                return f"postgresql://{username}:{password}@{host}:{port}/{database}"
        except Exception as e:
            logger.warning(f"Could not get DB credentials from Vault: {e}")
        
        # Fallback to environment variables
        host = os.getenv('DB_HOST', 'db')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'volextrades')
        username = os.getenv('DB_USER', 'volex')
        password = os.getenv('DB_PASSWORD', 'volex_pass')
        
        # Force host to be 'db' for Docker containers
        if host == 'localhost' or host == '127.0.0.1':
            host = 'db'
            logger.warning(f"Detected localhost in DB_HOST, forcing to 'db' for Docker environment")
        
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    
    def _initialize_connection(self) -> None:
        """Initialize database connection."""
        try:
            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=False  # Set to True for SQL debugging
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Successfully connected to TimescaleDB")
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def _create_tables(self) -> None:
        """Create database tables and hypertables."""
        try:
            # Import models to register them
            from .models import (
                PriceData, Trade, Strategy, Backtest, 
                Signal, AgentLog, SystemConfig
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create hypertables for time-series data
            self._create_hypertables()
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def _create_hypertables(self) -> None:
        """Create TimescaleDB hypertables for time-series data."""
        try:
            with self.engine.connect() as conn:
                # For now, skip hypertable creation to avoid issues
                # We'll implement this later when we have a stable base
                logger.info("Skipping hypertable creation for now - using regular PostgreSQL tables")
                
                # Create regular indexes for time-series optimization
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_price_data_time_symbol 
                    ON price_data (time, symbol);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_trades_executed_at_symbol 
                    ON trades (executed_at, symbol);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_signals_timestamp_symbol 
                    ON signals (timestamp, symbol);
                """))
                
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp_agent 
                    ON agent_logs (timestamp, agent_name);
                """))
                
                conn.commit()
                
            logger.info("Regular PostgreSQL indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            # Don't raise - this is not critical for basic functionality
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.SessionLocal:
            raise RuntimeError("Database not initialized")
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check database connection health."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a raw SQL query."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query), params or {})
                return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        try:
            info = {}
            
            with self.engine.connect() as conn:
                # Get database size
                size_result = conn.execute(text("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """))
                info['database_size'] = size_result.fetchone()[0]
                
                # Get table counts
                tables = ['price_data', 'trades', 'strategies', 'backtests', 'signals', 'agent_logs']
                for table in tables:
                    try:
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        info[f'{table}_count'] = count_result.fetchone()[0]
                    except:
                        info[f'{table}_count'] = 0
                
                # Get hypertable info
                hypertable_result = conn.execute(text("""
                    SELECT hypertable_name, num_chunks 
                    FROM timescaledb_information.hypertables
                """))
                info['hypertables'] = [dict(row) for row in hypertable_result]
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}


# Global database client instance
_db_client: Optional[DatabaseClient] = None


def get_db_client() -> DatabaseClient:
    """
    Get or create a global database client instance.
    
    Returns:
        DatabaseClient instance
    """
    global _db_client
    
    if _db_client is None:
        _db_client = DatabaseClient()
    
    return _db_client


def get_session() -> Session:
    """
    Get a database session using the global client.
    
    Returns:
        Database session
    """
    return get_db_client().get_session()


def health_check() -> bool:
    """
    Check database health using the global client.
    
    Returns:
        True if healthy, False otherwise
    """
    return get_db_client().health_check()


def execute_query(query: str, params: Optional[Dict] = None) -> List[Dict]:
    """
    Execute a raw SQL query using the global client.
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        List of result dictionaries
    """
    return get_db_client().execute_query(query, params)


def get_database_info() -> Dict[str, Any]:
    """
    Get database information using the global client.
    
    Returns:
        Database information dictionary
    """
    return get_db_client().get_database_info() 