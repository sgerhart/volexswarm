#!/usr/bin/env python3
"""
Update Risk Configuration in Database
Populates the risk_config table with comprehensive risk management settings.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.db import get_db_client
from common.logging import get_logger

logger = get_logger("update_risk_config")

# Comprehensive risk configuration data
RISK_CONFIG_DATA = [
    # Portfolio Risk Management
    {
        "config_key": "max_portfolio_risk",
        "config_value": 0.10,
        "category": "portfolio",
        "description": "Maximum portfolio risk as a percentage (10%)"
    },
    {
        "config_key": "max_daily_loss",
        "config_value": 0.05,
        "category": "portfolio",
        "description": "Maximum daily loss as a percentage (5%)"
    },
    {
        "config_key": "max_drawdown",
        "config_value": 0.20,
        "category": "portfolio",
        "description": "Maximum drawdown as a percentage (20%)"
    },
    {
        "config_key": "correlation_threshold",
        "config_value": 0.70,
        "category": "portfolio",
        "description": "Maximum correlation between positions (70%)"
    },
    
    # Position Sizing
    {
        "config_key": "max_position_size",
        "config_value": 0.05,
        "category": "position",
        "description": "Maximum position size as a percentage of portfolio (5%)"
    },
    {
        "config_key": "min_position_size",
        "config_value": 0.01,
        "category": "position",
        "description": "Minimum position size as a percentage of portfolio (1%)"
    },
    {
        "config_key": "kelly_fraction",
        "config_value": 0.25,
        "category": "position",
        "description": "Kelly criterion fraction for position sizing (25%)"
    },
    {
        "config_key": "volatility_multiplier",
        "config_value": 1.5,
        "category": "position",
        "description": "Multiplier for volatility-based position sizing"
    },
    {
        "config_key": "optimal_f_fraction",
        "config_value": 0.20,
        "category": "position",
        "description": "Optimal f fraction for position sizing (20%)"
    },
    
    # Risk Management
    {
        "config_key": "stop_loss_default",
        "config_value": 0.02,
        "category": "risk_management",
        "description": "Default stop loss percentage (2%)"
    },
    {
        "config_key": "take_profit_default",
        "config_value": 0.04,
        "category": "risk_management",
        "description": "Default take profit percentage (4%)"
    },
    {
        "config_key": "trailing_stop_enabled",
        "config_value": True,
        "category": "risk_management",
        "description": "Enable trailing stop loss"
    },
    {
        "config_key": "trailing_stop_distance",
        "config_value": 0.015,
        "category": "risk_management",
        "description": "Trailing stop distance as percentage (1.5%)"
    },
    
    # Circuit Breaker Settings
    {
        "config_key": "circuit_breaker_drawdown",
        "config_value": 0.15,
        "category": "circuit_breaker",
        "description": "Drawdown threshold for circuit breaker (15%)"
    },
    {
        "config_key": "circuit_breaker_daily_loss",
        "config_value": 0.08,
        "category": "circuit_breaker",
        "description": "Daily loss threshold for circuit breaker (8%)"
    },
    {
        "config_key": "circuit_breaker_volatility",
        "config_value": 0.08,
        "category": "circuit_breaker",
        "description": "Volatility threshold for circuit breaker (8%)"
    },
    {
        "config_key": "circuit_breaker_cooldown_hours",
        "config_value": 24,
        "category": "circuit_breaker",
        "description": "Cooldown period after circuit breaker (24 hours)"
    },
    
    # Market Risk
    {
        "config_key": "high_volatility_threshold",
        "config_value": 0.06,
        "category": "market_risk",
        "description": "High volatility threshold (6%)"
    },
    {
        "config_key": "low_liquidity_threshold",
        "config_value": 1000000,
        "category": "market_risk",
        "description": "Low liquidity threshold in USD"
    },
    {
        "config_key": "market_crash_threshold",
        "config_value": 0.20,
        "category": "market_risk",
        "description": "Market crash threshold (20% drop)"
    },
    
    # Performance Metrics
    {
        "config_key": "min_sharpe_ratio",
        "config_value": 1.0,
        "category": "performance",
        "description": "Minimum Sharpe ratio for strategy approval"
    },
    {
        "config_key": "max_var_95",
        "config_value": 0.03,
        "category": "performance",
        "description": "Maximum 95% Value at Risk (3%)"
    },
    {
        "config_key": "min_win_rate",
        "config_value": 0.45,
        "category": "performance",
        "description": "Minimum win rate for strategy approval (45%)"
    },
    
    # Regulatory Compliance
    {
        "config_key": "max_leverage",
        "config_value": 3.0,
        "category": "compliance",
        "description": "Maximum leverage allowed (3x)"
    },
    {
        "config_key": "max_concentration",
        "config_value": 0.25,
        "category": "compliance",
        "description": "Maximum concentration in single asset (25%)"
    },
    {
        "config_key": "min_balance_requirement",
        "config_value": 1000.0,
        "category": "compliance",
        "description": "Minimum account balance requirement ($1000)"
    }
]

async def create_risk_config_table():
    """Create the risk_config table if it doesn't exist."""
    try:
        db_client = get_db_client()
        
        # Check if table exists
        result = await db_client.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'risk_config'
        """)
        
        if not result:
            print("Creating risk_config table...")
            
            # Create the table
            await db_client.execute("""
                CREATE TABLE IF NOT EXISTS risk_config (
                    id SERIAL PRIMARY KEY,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value JSONB NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index
            await db_client.execute("""
                CREATE INDEX IF NOT EXISTS idx_risk_config_category 
                ON risk_config (category)
            """)
            
            print("✅ risk_config table created successfully")
        else:
            print("✅ risk_config table already exists")
        
        await db_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create risk_config table: {e}")
        return False

async def insert_risk_config_data():
    """Insert risk configuration data into the database."""
    try:
        db_client = get_db_client()
        
        print(f"Inserting {len(RISK_CONFIG_DATA)} risk configuration items...")
        
        # Insert each configuration item
        for config in RISK_CONFIG_DATA:
            try:
                await db_client.execute("""
                    INSERT INTO risk_config (config_key, config_value, category, description)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (config_key) DO UPDATE SET
                        config_value = EXCLUDED.config_value,
                        category = EXCLUDED.category,
                        description = EXCLUDED.description,
                        updated_at = CURRENT_TIMESTAMP
                """, config["config_key"], json.dumps(config["config_value"]), 
                     config["category"], config["description"])
                
                print(f"   ✅ {config['config_key']} ({config['category']})")
                
            except Exception as e:
                print(f"   ❌ Failed to insert {config['config_key']}: {e}")
        
        await db_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to insert risk config data: {e}")
        return False

async def verify_risk_config_data():
    """Verify that the risk configuration data was inserted correctly."""
    try:
        db_client = get_db_client()
        
        print("\nVerifying risk configuration data...")
        
        # Count total items
        count_result = await db_client.fetch("SELECT COUNT(*) as count FROM risk_config")
        total_count = count_result[0]['count']
        print(f"Total configuration items: {total_count}")
        
        # Count by category
        category_result = await db_client.fetch("""
            SELECT category, COUNT(*) as count 
            FROM risk_config 
            GROUP BY category 
            ORDER BY category
        """)
        
        print("\nConfiguration by category:")
        for row in category_result:
            print(f"   {row['category']}: {row['count']} items")
        
        # Show sample items from each category
        print("\nSample configuration items:")
        for row in category_result:
            category = row['category']
            sample_result = await db_client.fetch("""
                SELECT config_key, config_value, description 
                FROM risk_config 
                WHERE category = $1 
                LIMIT 2
            """, category)
            
            print(f"\n   {category}:")
            for sample in sample_result:
                print(f"     - {sample['config_key']}: {sample['config_value']}")
                print(f"       {sample['description']}")
        
        await db_client.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to verify risk config data: {e}")
        return False

async def test_risk_agent_integration():
    """Test that the risk agent can read the configuration."""
    try:
        print("\nTesting risk agent integration...")
        
        # Import and test the config manager
        from common.config_manager import config_manager
        
        # Initialize config manager
        await config_manager.initialize()
        
        # Get risk config
        risk_config = await config_manager.get_risk_config()
        
        if risk_config:
            print(f"✅ Risk agent can read {len(risk_config)} configuration items")
            
            # Test specific values
            max_portfolio_risk = await config_manager.get_risk_config_value("max_portfolio_risk")
            if max_portfolio_risk is not None:
                print(f"   ✅ max_portfolio_risk: {max_portfolio_risk}")
            else:
                print("   ❌ max_portfolio_risk not found")
                
            kelly_fraction = await config_manager.get_risk_config_value("kelly_fraction")
            if kelly_fraction is not None:
                print(f"   ✅ kelly_fraction: {kelly_fraction}")
            else:
                print("   ❌ kelly_fraction not found")
        else:
            print("❌ Risk agent cannot read configuration")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Risk agent integration test failed: {e}")
        return False

async def main():
    """Main function to update risk configuration."""
    print("🚀 Starting Risk Configuration Update")
    print("=" * 60)
    
    try:
        # Step 1: Create table
        if not await create_risk_config_table():
            return False
        
        # Step 2: Insert data
        if not await insert_risk_config_data():
            return False
        
        # Step 3: Verify data
        if not await verify_risk_config_data():
            return False
        
        # Step 4: Test integration
        if not await test_risk_agent_integration():
            return False
        
        print("\n🎉 Risk configuration update completed successfully!")
        print("\nThe risk agent now has access to comprehensive configuration data for:")
        print("   • Portfolio risk management")
        print("   • Position sizing algorithms")
        print("   • Risk management parameters")
        print("   • Circuit breaker settings")
        print("   • Market risk thresholds")
        print("   • Performance metrics")
        print("   • Regulatory compliance")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Risk configuration update failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())

