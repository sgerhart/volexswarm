#!/usr/bin/env python3
"""
Recreate portfolio_history table with correct schema.
"""

import subprocess
import sys
import os

# Add the parent directory to the path to import common modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Database configuration
DB_CONFIG = {
    "host": "172.18.0.3",  # Use Docker container IP for SQLAlchemy connection
    "port": "5432",
    "database": "volextrades",
    "user": "volex",
    "password": "volex_pass"
}

def execute_sql(sql: str) -> bool:
    """Execute SQL command on the database."""
    try:
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", DB_CONFIG["database"],
            "-c", sql
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SQL executed successfully")
            return True
        else:
            print(f"❌ SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ SQL execution error: {e}")
        return False

def recreate_portfolio_history_table():
    """Recreate the portfolio_history table with correct schema."""
    print("🗄️  Recreating Portfolio History Table")
    print("=" * 50)
    
    # Drop existing table
    print("🗑️  Dropping existing portfolio_history table...")
    if not execute_sql("DROP TABLE IF EXISTS portfolio_history CASCADE;"):
        print("❌ Failed to drop portfolio_history table")
        return False
    
    # Create the table with correct schema
    create_table_sql = """
    CREATE TABLE portfolio_history (
        id SERIAL PRIMARY KEY,
        exchange VARCHAR(50) NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        portfolio_value DOUBLE PRECISION NOT NULL,
        usdt_balance DOUBLE PRECISION DEFAULT 0.0,
        btc_balance DOUBLE PRECISION DEFAULT 0.0,
        btc_price DOUBLE PRECISION DEFAULT 0.0,
        total_positions_value DOUBLE PRECISION DEFAULT 0.0,
        realized_pnl DOUBLE PRECISION DEFAULT 0.0,
        unrealized_pnl DOUBLE PRECISION DEFAULT 0.0,
        total_return_percentage DOUBLE PRECISION DEFAULT 0.0,
        daily_return DOUBLE PRECISION DEFAULT 0.0,
        annualized_return DOUBLE PRECISION DEFAULT 0.0,
        performance_metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    print("🔨 Creating portfolio_history table with correct schema...")
    if not execute_sql(create_table_sql):
        print("❌ Failed to create portfolio_history table")
        return False
    
    # Create indexes for efficient time-series queries
    print("🔨 Creating indexes for time-series queries...")
    indexes = [
        "CREATE INDEX idx_portfolio_history_exchange_timestamp ON portfolio_history (exchange, timestamp);",
        "CREATE INDEX idx_portfolio_history_timestamp ON portfolio_history (timestamp);",
        "CREATE INDEX idx_portfolio_history_exchange ON portfolio_history (exchange);"
    ]
    
    for index_sql in indexes:
        if not execute_sql(index_sql):
            print(f"❌ Failed to create index: {index_sql}")
            return False
    
    print("✅ portfolio_history table recreated successfully with correct schema and indexes")
    return True

if __name__ == "__main__":
    recreate_portfolio_history_table()
