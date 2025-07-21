#!/usr/bin/env python3
"""
Test script for VolexSwarm database integration.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.db import get_db_client, health_check, get_database_info
from common.models import PriceData, Strategy, Trade, Signal, AgentLog
from common.logging import get_logger


def test_database_connection():
    """Test basic database connection."""
    print("Testing database connection...")
    
    try:
        client = get_db_client()
        if health_check():
            print("✓ Database connection successful")
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return False


def test_table_creation():
    """Test that all tables are created correctly."""
    print("\nTesting table creation...")
    
    try:
        client = get_db_client()
        session = client.get_session()
        
        # Test that we can query each table
        tables = [
            ('price_data', PriceData),
            ('strategies', Strategy),
            ('trades', Trade),
            ('signals', Signal),
            ('agent_logs', AgentLog)
        ]
        
        for table_name, model in tables:
            try:
                count = session.query(model).count()
                print(f"✓ Table {table_name} exists ({count} records)")
            except Exception as e:
                print(f"✗ Table {table_name} error: {e}")
                return False
        
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Table creation test failed: {e}")
        return False


def test_hypertables():
    """Test TimescaleDB hypertables."""
    print("\nTesting TimescaleDB hypertables...")
    
    try:
        client = get_db_client()
        
        # Check if hypertables exist
        query = """
            SELECT hypertable_name, num_chunks 
            FROM timescaledb_information.hypertables
            WHERE hypertable_name IN ('price_data', 'trades', 'signals', 'agent_logs')
        """
        
        result = client.execute_query(query)
        
        expected_tables = ['price_data', 'trades', 'signals', 'agent_logs']
        found_tables = [row['hypertable_name'] for row in result]
        
        for table in expected_tables:
            if table in found_tables:
                print(f"✓ Hypertable {table} created successfully")
            else:
                print(f"✗ Hypertable {table} not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ Hypertable test failed: {e}")
        return False


def test_data_insertion():
    """Test inserting sample data."""
    print("\nTesting data insertion...")
    
    try:
        client = get_db_client()
        session = client.get_session()
        
        # Insert sample strategy
        strategy = Strategy(
            name="Test Strategy",
            description="A test strategy for database testing",
            agent_name="research",
            parameters={"param1": "value1", "param2": 42},
            is_active=True
        )
        session.add(strategy)
        session.commit()
        print("✓ Strategy inserted successfully")
        
        # Insert sample price data
        price_data = PriceData(
            time=datetime.utcnow(),
            symbol="BTCUSD",
            exchange="binanceus",
            open=50000.0,
            high=51000.0,
            low=49000.0,
            close=50500.0,
            volume=100.5,
            timeframe="1h"
        )
        session.add(price_data)
        session.commit()
        print("✓ Price data inserted successfully")
        
        # Insert sample signal
        signal = Signal(
            strategy_id=strategy.id,
            symbol="BTCUSD",
            signal_type="buy",
            strength=0.8,
            confidence=0.75,
            timestamp=datetime.utcnow(),
            timeframe="1h",
            indicators={"rsi": 30, "macd": "bullish"},
            signal_metadata={"source": "test"}
        )
        session.add(signal)
        session.commit()
        print("✓ Signal inserted successfully")
        
        # Insert sample trade
        trade = Trade(
            trade_id="test_trade_123",
            strategy_id=strategy.id,
            symbol="BTCUSD",
            exchange="binanceus",
            side="buy",
            order_type="market",
            quantity=0.1,
            price=50500.0,
            executed_at=datetime.utcnow(),
            status="filled",
            fees=5.05,
            fees_currency="USD",
            trade_metadata={"test": True}
        )
        session.add(trade)
        session.commit()
        print("✓ Trade inserted successfully")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Data insertion test failed: {e}")
        return False


def test_logging():
    """Test structured logging."""
    print("\nTesting structured logging...")
    
    try:
        logger = get_logger("test_agent")
        
        # Test different log levels
        logger.info("Test info message", {"test": True, "level": "info"})
        logger.warning("Test warning message", {"test": True, "level": "warning"})
        logger.error("Test error message", {"test": True, "level": "error"})
        
        # Test operation logging
        with logger.log_operation("test_operation", {"operation": "test"}):
            import time
            time.sleep(0.1)  # Simulate some work
        
        print("✓ Logging test completed")
        return True
        
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False


def test_database_info():
    """Test database information retrieval."""
    print("\nTesting database information...")
    
    try:
        info = get_database_info()
        
        print(f"✓ Database size: {info.get('database_size', 'unknown')}")
        print(f"✓ Price data records: {info.get('price_data_count', 0)}")
        print(f"✓ Trade records: {info.get('trades_count', 0)}")
        print(f"✓ Strategy records: {info.get('strategies_count', 0)}")
        print(f"✓ Signal records: {info.get('signals_count', 0)}")
        print(f"✓ Log records: {info.get('agent_logs_count', 0)}")
        
        hypertables = info.get('hypertables', [])
        print(f"✓ Hypertables: {len(hypertables)} found")
        for ht in hypertables:
            print(f"  - {ht['hypertable_name']}: {ht['num_chunks']} chunks")
        
        return True
        
    except Exception as e:
        print(f"✗ Database info test failed: {e}")
        return False


def main():
    """Run all database tests."""
    print("VolexSwarm Database Integration Test")
    print("=" * 40)
    
    tests = [
        test_database_connection,
        test_table_creation,
        test_hypertables,
        test_data_insertion,
        test_logging,
        test_database_info
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All database tests passed! Database integration is working correctly.")
        print("\nNext steps:")
        print("1. Update agents to use the new database client")
        print("2. Implement data storage in research agent")
        print("3. Add database endpoints to agent APIs")
        return 0
    else:
        print("❌ Some database tests failed. Please check your TimescaleDB setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 