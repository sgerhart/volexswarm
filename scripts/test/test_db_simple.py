#!/usr/bin/env python3
"""
Simple database test script using direct connection.
"""

import psycopg2
import sys

def test_database_connection():
    """Test database connection."""
    print("Testing database connection...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="volextrades",
            user="volex",
            password="volex_pass",
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ Database connected successfully")
        print(f"  PostgreSQL version: {version.split(',')[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_timescaledb_extension():
    """Test TimescaleDB extension."""
    print("Testing TimescaleDB extension...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="volextrades",
            user="volex",
            password="volex_pass",
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Check if TimescaleDB extension is installed
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'timescaledb';")
        result = cursor.fetchone()
        
        if result:
            print("✓ TimescaleDB extension is installed")
            
            # Check hypertables
            cursor.execute("SELECT count(*) FROM timescaledb_information.hypertables;")
            hypertable_count = cursor.fetchone()[0]
            print(f"  Found {hypertable_count} hypertables")
            
        else:
            print("✗ TimescaleDB extension not found")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ TimescaleDB test failed: {e}")
        return False

def test_dual_mode_tables():
    """Test dual-mode trading tables."""
    print("Testing dual-mode trading tables...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="volextrades",
            user="volex",
            password="volex_pass",
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Check if dual-mode tables exist
        tables_to_check = ['dual_mode_trades', 'dual_mode_performance']
        
        for table in tables_to_check:
            cursor.execute(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');")
            exists = cursor.fetchone()[0]
            
            if exists:
                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                print(f"✓ Table {table} exists with {count} records")
            else:
                print(f"✗ Table {table} not found")
                return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Dual-mode tables test failed: {e}")
        return False

def test_basic_operations():
    """Test basic database operations."""
    print("Testing basic database operations...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="volextrades",
            user="volex",
            password="volex_pass",
            connect_timeout=10
        )
        
        cursor = conn.cursor()
        
        # Test insert and select
        cursor.execute("""
            INSERT INTO dual_mode_trades (symbol, side, live_quantity, live_price, dry_run_price, timestamp)
            VALUES ('TEST/USDT', 'buy', 0.001, 50000.0, 50000.0, NOW())
            ON CONFLICT DO NOTHING;
        """)
        
        cursor.execute("SELECT COUNT(*) FROM dual_mode_trades WHERE symbol = 'TEST/USDT';")
        count = cursor.fetchone()[0]
        
        if count > 0:
            print("✓ Basic insert/select operations working")
        else:
            print("✗ Basic operations failed")
            return False
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Basic operations test failed: {e}")
        return False

def main():
    """Run all database tests."""
    print("🗄️ Simple Database Test")
    print("=" * 30)
    
    tests = [
        test_database_connection,
        test_timescaledb_extension,
        test_dual_mode_tables,
        test_basic_operations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check database setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 