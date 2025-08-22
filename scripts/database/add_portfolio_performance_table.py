#!/usr/bin/env python3
"""
Add portfolio_performance table to track starting balances and returns.
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

def add_portfolio_performance_table():
    """Add the portfolio_performance table."""
    print("🗄️  Adding Portfolio Performance Table")
    print("=" * 50)
    
    # Check if table already exists
    if check_table_exists("portfolio_performance"):
        print("✅ portfolio_performance table already exists")
        return True
    
    # Create the table
    create_table_sql = """
    CREATE TABLE portfolio_performance (
        id SERIAL PRIMARY KEY,
        exchange VARCHAR(50) NOT NULL UNIQUE,
        initial_balance DOUBLE PRECISION NOT NULL,
        initial_timestamp TIMESTAMP NOT NULL,
        current_balance DOUBLE PRECISION NOT NULL,
        last_updated TIMESTAMP NOT NULL,
        absolute_return DOUBLE PRECISION DEFAULT 0.0,
        total_return_percentage DOUBLE PRECISION DEFAULT 0.0,
        realized_pnl DOUBLE PRECISION DEFAULT 0.0,
        unrealized_pnl DOUBLE PRECISION DEFAULT 0.0,
        daily_return DOUBLE PRECISION DEFAULT 0.0,
        annualized_return DOUBLE PRECISION DEFAULT 0.0,
        days_elapsed INTEGER DEFAULT 0,
        performance_metadata JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    print("🔨 Creating portfolio_performance table...")
    if not execute_sql(create_table_sql):
        print("❌ Failed to create portfolio_performance table")
        return False
    
    # Create indexes
    print("🔨 Creating indexes...")
    indexes = [
        "CREATE INDEX idx_portfolio_performance_exchange ON portfolio_performance (exchange);",
        "CREATE INDEX idx_portfolio_performance_timestamp ON portfolio_performance (initial_timestamp);",
        "CREATE INDEX idx_portfolio_performance_last_updated ON portfolio_performance (last_updated);"
    ]
    
    for index_sql in indexes:
        if not execute_sql(index_sql):
            print(f"❌ Failed to create index: {index_sql}")
            return False
    
    print("✅ portfolio_performance table created successfully with indexes")
    return True

if __name__ == "__main__":
    add_portfolio_performance_table()
