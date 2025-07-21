#!/usr/bin/env python3
"""
Optimize the empty database with TimescaleDB-ready schema before any data is added.
This ensures all tables are properly configured from the start.
"""

import subprocess
import sys

# Database configuration
DB_CONFIG = {
    "host": "localhost",
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
            return True
        else:
            print(f"SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"SQL execution error: {e}")
        return False

def create_optimized_tables() -> bool:
    """Create tables with optimized schema for TimescaleDB."""
    print("🏗️  Creating optimized tables...")
    
    # Create tables with proper primary keys and data types
    tables_sql = [
        # price_data - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS price_data (
            id SERIAL,
            time TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            open_price DOUBLE PRECISION NOT NULL,
            high_price DOUBLE PRECISION NOT NULL,
            low_price DOUBLE PRECISION NOT NULL,
            close_price DOUBLE PRECISION NOT NULL,
            volume DOUBLE PRECISION NOT NULL,
            PRIMARY KEY (id, time)
        );
        """,
        
        # market_data - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS market_data (
            id SERIAL,
            timestamp TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            data_type TEXT NOT NULL,
            source TEXT NOT NULL,
            data JSONB NOT NULL,
            PRIMARY KEY (id, timestamp)
        );
        """,
        
        # signals - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS signals (
            id SERIAL,
            timestamp TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            strength DOUBLE PRECISION NOT NULL,
            timeframe TEXT NOT NULL,
            metadata JSONB,
            PRIMARY KEY (id, timestamp)
        );
        """,
        
        # orders - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL,
            order_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            exchange TEXT NOT NULL,
            side TEXT NOT NULL,
            order_type TEXT NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            price DOUBLE PRECISION,
            status TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL,
            updated_at TIMESTAMPTZ NOT NULL,
            strategy_id INTEGER,
            signal_confidence DOUBLE PRECISION,
            PRIMARY KEY (id, created_at)
        );
        """,
        
        # dual_mode_trades - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS dual_mode_trades (
            id SERIAL,
            timestamp TIMESTAMPTZ NOT NULL,
            trade_id TEXT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            order_type TEXT,
            live_quantity DOUBLE PRECISION,
            live_price DOUBLE PRECISION,
            live_fees DOUBLE PRECISION,
            live_status TEXT,
            live_order_id TEXT,
            live_execution_time TIMESTAMPTZ,
            dry_run_quantity DOUBLE PRECISION,
            dry_run_price DOUBLE PRECISION,
            dry_run_fees DOUBLE PRECISION,
            dry_run_status TEXT,
            dry_run_order_id TEXT,
            dry_run_execution_time TIMESTAMPTZ,
            price_difference DOUBLE PRECISION,
            execution_time_difference DOUBLE PRECISION,
            slippage_live DOUBLE PRECISION,
            slippage_dry_run DOUBLE PRECISION,
            strategy_id INTEGER,
            signal_confidence DOUBLE PRECISION,
            signal_type TEXT,
            trade_metadata JSONB,
            PRIMARY KEY (id, timestamp)
        );
        """,
        
        # dual_mode_performance - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS dual_mode_performance (
            id SERIAL,
            timestamp TIMESTAMPTZ NOT NULL,
            period TEXT NOT NULL,
            live_pnl DOUBLE PRECISION,
            dry_run_pnl DOUBLE PRECISION,
            performance_difference DOUBLE PRECISION,
            live_win_rate DOUBLE PRECISION,
            dry_run_win_rate DOUBLE PRECISION,
            live_sharpe_ratio DOUBLE PRECISION,
            dry_run_sharpe_ratio DOUBLE PRECISION,
            metrics JSONB,
            PRIMARY KEY (id, timestamp)
        );
        """,
        
        # agent_logs - optimized for hypertable
        """
        CREATE TABLE IF NOT EXISTS agent_logs (
            id SERIAL,
            timestamp TIMESTAMPTZ NOT NULL,
            agent_name TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            metadata JSONB,
            PRIMARY KEY (id, timestamp)
        );
        """,
        
        # Other tables (not hypertables)
        """
        CREATE TABLE IF NOT EXISTS strategies (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            parameters JSONB,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS system_config (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS api_cost_tracking (
            id SERIAL PRIMARY KEY,
            agent_name TEXT NOT NULL,
            api_name TEXT NOT NULL,
            cost DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS backtests (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER REFERENCES strategies(id),
            start_date TIMESTAMPTZ NOT NULL,
            end_date TIMESTAMPTZ NOT NULL,
            results JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id SERIAL PRIMARY KEY,
            strategy_id INTEGER REFERENCES strategies(id),
            metric_name TEXT NOT NULL,
            metric_value DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS portfolios (
            id SERIAL PRIMARY KEY,
            symbol TEXT NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            average_price DOUBLE PRECISION NOT NULL,
            current_price DOUBLE PRECISION,
            pnl DOUBLE PRECISION,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS trades (
            id SERIAL PRIMARY KEY,
            order_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity DOUBLE PRECISION NOT NULL,
            price DOUBLE PRECISION NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        );
        """,
        
        """
        CREATE TABLE IF NOT EXISTS trading_configuration (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ]
    
    for i, sql in enumerate(tables_sql, 1):
        print(f"   Creating table {i}/{len(tables_sql)}...")
        if not execute_sql(sql):
            print(f"   ❌ Failed to create table {i}")
            return False
    
    print("   ✅ All tables created with optimized schema")
    return True

def create_hypertables() -> bool:
    """Create hypertables for time-series data."""
    print("📊 Creating hypertables...")
    
    hypertable_candidates = [
        ("price_data", "time"),
        ("market_data", "timestamp"),
        ("signals", "timestamp"),
        ("orders", "created_at"),
        ("dual_mode_trades", "timestamp"),
        ("dual_mode_performance", "timestamp"),
        ("agent_logs", "timestamp")
    ]
    
    for table, time_column in hypertable_candidates:
        print(f"   Converting {table} to hypertable...")
        
        convert_sql = f"""
        SELECT create_hypertable('{table}', '{time_column}', 
                               if_not_exists => TRUE);
        """
        
        if execute_sql(convert_sql):
            print(f"   ✅ {table} converted to hypertable")
        else:
            print(f"   ❌ Failed to convert {table} to hypertable")
    
    return True

def create_indexes() -> bool:
    """Create performance indexes."""
    print("📈 Creating performance indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_price_data_symbol_time ON price_data(symbol, time DESC);",
        "CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_signals_symbol_timestamp ON signals(symbol, timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_orders_symbol_created_at ON orders(symbol, created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_dual_mode_trades_timestamp ON dual_mode_trades(timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_dual_mode_performance_timestamp ON dual_mode_performance(timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_timestamp ON agent_logs(agent_name, timestamp DESC);"
    ]
    
    for i, index_sql in enumerate(indexes, 1):
        print(f"   Creating index {i}/{len(indexes)}...")
        if execute_sql(index_sql):
            print(f"   ✅ Index {i} created")
        else:
            print(f"   ❌ Failed to create index {i}")
    
    return True

def create_initial_data() -> bool:
    """Create initial data."""
    print("🏗️  Creating initial data...")
    
    # Create default strategy
    strategy_sql = """
    INSERT INTO strategies (name, description, parameters, is_active, created_at, updated_at)
    VALUES ('Default Strategy', 'Default trading strategy', '{}', true, NOW(), NOW());
    """
    
    if execute_sql(strategy_sql):
        print("   ✅ Created default strategy")
    else:
        print("   ❌ Failed to create default strategy")
    
    # Create default system config
    config_sql = """
    INSERT INTO system_config (key, value, description, updated_at)
    VALUES 
        ('dual_mode_enabled', 'true', 'Enable dual-mode trading', NOW()),
        ('live_trade_size_percent', '10', 'Live trade size as percentage of dry run', NOW()),
        ('default_exchange', 'binanceus', 'Default exchange for trading', NOW());
    """
    
    if execute_sql(config_sql):
        print("   ✅ Created default system configuration")
    else:
        print("   ❌ Failed to create default system configuration")
    
    return True

def verify_optimization() -> bool:
    """Verify that optimization was successful."""
    print("🔍 Verifying optimization...")
    
    # Check hypertables
    cmd = [
        "docker", "exec", "volexstorm-db", "psql",
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "-c", "SELECT hypertable_name FROM timescaledb_information.hypertables ORDER BY hypertable_name;"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("   ✅ Hypertables found:")
        lines = result.stdout.strip().split('\n')
        for line in lines[2:-1]:  # Skip header and footer
            if line.strip():
                print(f"      - {line.strip()}")
    else:
        print("   ❌ Could not verify hypertables")
        return False
    
    # Check table count
    cmd = [
        "docker", "exec", "volexstorm-db", "psql",
        "-U", DB_CONFIG["user"],
        "-d", DB_CONFIG["database"],
        "-t", "-c", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        try:
            table_count = int(result.stdout.strip())
            print(f"   ✅ Total tables: {table_count}")
        except ValueError:
            print("   ❌ Could not parse table count")
            return False
    else:
        print("   ❌ Could not verify table count")
        return False
    
    return True

def main():
    """Optimize the empty database."""
    print("🚀 Optimizing Empty Database")
    print("=" * 50)
    
    # Create optimized tables
    if not create_optimized_tables():
        return False
    
    # Create hypertables
    if not create_hypertables():
        return False
    
    # Create indexes
    if not create_indexes():
        return False
    
    # Create initial data
    if not create_initial_data():
        return False
    
    # Verify optimization
    if not verify_optimization():
        return False
    
    print("\n🎉 Database optimization completed successfully!")
    print("   Database is now perfectly optimized for TimescaleDB performance.")
    print("   All tables are ready for dual-mode trading.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 