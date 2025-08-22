#!/usr/bin/env python3
"""
Add portfolio_history table to track portfolio values over time for charting.
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

def add_portfolio_history_table():
    """Add the portfolio_history table for tracking portfolio values over time."""
    print("🗄️  Adding Portfolio History Table for Charting")
    print("=" * 60)
    
    # Check if table already exists
    if check_table_exists("portfolio_history"):
        print("✅ portfolio_history table already exists")
        return True
    
    # Create the table
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
    
    print("🔨 Creating portfolio_history table...")
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
    
    print("✅ portfolio_history table created successfully with time-series indexes")
    return True

if __name__ == "__main__":
    add_portfolio_history_table()
