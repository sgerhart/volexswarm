#!/usr/bin/env python3
"""
Database schema setup script for VolexSwarm.
Creates all tables with the correct schema for new deployments.
"""

import subprocess
import sys
import os

# Add the parent directory to the path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.db import DatabaseClient
from common.models import Base

# Database configuration
DB_CONFIG = {
    "host": "localhost",  # Use localhost for local development
    "port": "5432",
    "database": "volextrades",
    "user": "volex",
    "password": "volex_pass"
}

def execute_sql(sql: str, database: str = None) -> bool:
    """Execute SQL command on the database."""
    try:
        db = database or DB_CONFIG["database"]
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", db,
            "-c", sql
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SQL executed successfully: {sql[:50]}...")
            return True
        else:
            print(f"❌ SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ SQL execution error: {e}")
        return False

def check_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    sql = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}'
    );
    """
    
    cmd = [
        "docker", "exec", "volexstorm-db", "psql",
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "-t", "-c", sql
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() == "t"

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    sql = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}' 
        AND column_name = '{column_name}'
    );
    """
    
    cmd = [
        "docker", "exec", "volexstorm-db", "psql",
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "-t", "-c", sql
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() == "t"

def setup_database_schema():
    """Set up the complete database schema."""
    print("🗄️  Setting up VolexSwarm Database Schema")
    print("=" * 50)
    
    # Check if database exists
    print("🔍 Checking database connection...")
    if not execute_sql("SELECT 1;"):
        print("❌ Cannot connect to database. Make sure the database container is running.")
        return False
    
    # Create TimescaleDB extension if not exists
    print("🔧 Creating TimescaleDB extension...")
    if not execute_sql("CREATE EXTENSION IF NOT EXISTS timescaledb;"):
        print("❌ Failed to create TimescaleDB extension")
        return False
    
    # Create tables using SQLAlchemy
    print("🏗️  Creating tables using SQLAlchemy...")
    try:
        # Create database client with explicit URL for local development
        db_url = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        db_client = DatabaseClient(db_url)
        
        # Create all tables
        Base.metadata.create_all(bind=db_client.engine)
        print("✅ All tables created successfully")
        
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False
    
    # Check and fix specific schema issues
    print("🔍 Checking for schema inconsistencies...")
    
    # Check if strategies table has agent_name column
    if check_table_exists("strategies"):
        if not check_column_exists("strategies", "agent_name"):
            print("🔧 Adding missing agent_name column to strategies table...")
            if not execute_sql("ALTER TABLE strategies ADD COLUMN agent_name VARCHAR(50) NOT NULL DEFAULT 'strategy';"):
                print("❌ Failed to add agent_name column")
                return False
        else:
            print("✅ strategies.agent_name column already exists")
    
    # Check if trades table has executed_at column
    if check_table_exists("trades"):
        if not check_column_exists("trades", "executed_at"):
            print("🔧 Adding missing executed_at column to trades table...")
            if not execute_sql("ALTER TABLE trades ADD COLUMN executed_at TIMESTAMP WITH TIME ZONE;"):
                print("❌ Failed to add executed_at column")
                return False
        else:
            print("✅ trades.executed_at column already exists")
    
    # Check if agent_logs table has log_context column
    if check_table_exists("agent_logs"):
        if not check_column_exists("agent_logs", "log_context"):
            print("🔧 Adding missing log_context column to agent_logs table...")
            if not execute_sql("ALTER TABLE agent_logs ADD COLUMN log_context JSONB;"):
                print("❌ Failed to add log_context column")
                return False
        else:
            print("✅ agent_logs.log_context column already exists")
    
    # Create indexes for performance
    print("📊 Creating performance indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_price_data_time_symbol ON price_data (time, symbol);",
        "CREATE INDEX IF NOT EXISTS idx_trades_executed_at_symbol ON trades (executed_at, symbol);",
        "CREATE INDEX IF NOT EXISTS idx_signals_timestamp_symbol ON signals (timestamp, symbol);",
        "CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp_agent ON agent_logs (timestamp, agent_name);",
        "CREATE INDEX IF NOT EXISTS idx_strategies_name ON strategies (name);",
        "CREATE INDEX IF NOT EXISTS idx_strategies_agent_name ON strategies (agent_name);",
        "CREATE INDEX IF NOT EXISTS idx_orders_symbol_created ON orders (symbol, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_orders_strategy_created ON orders (strategy_id, created_at);",
        "CREATE INDEX IF NOT EXISTS idx_backtests_strategy_created ON backtests (strategy_id, created_at);",
    ]
    
    for index_sql in indexes:
        if not execute_sql(index_sql):
            print(f"⚠️  Warning: Failed to create index: {index_sql[:50]}...")
    
    print("✅ Database schema setup completed successfully!")
    print("   All tables and indexes are ready for use.")
    
    return True

def main():
    """Main function."""
    try:
        success = setup_database_schema()
        if success:
            print("\n🎉 Database schema is ready for VolexSwarm!")
            print("   You can now start the agents and they will work with the correct schema.")
        else:
            print("\n❌ Database schema setup failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 