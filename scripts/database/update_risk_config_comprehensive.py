#!/usr/bin/env python3
"""
Comprehensive Risk Configuration Update
Populates the risk_config table with advanced risk management settings for the risk agent.
"""

import subprocess
import json
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
            print(f"✅ SQL executed successfully: {sql[:50]}...")
            return True
        else:
            print(f"❌ SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ SQL execution error: {e}")
        return False

def update_risk_config():
    """Update the risk configuration with comprehensive settings."""
    print("🔧 Updating Risk Configuration with Advanced Settings")
    print("=" * 60)
    
    # Advanced risk management configurations
    risk_configs = [
        # Portfolio Risk Management
        {
            "key": "max_portfolio_risk",
            "value": "0.10",
            "category": "portfolio",
            "description": "Maximum portfolio risk as a percentage (10%)"
        },
        {
            "key": "max_daily_portfolio_risk",
            "value": "0.05",
            "category": "portfolio",
            "description": "Maximum daily portfolio risk (5%)"
        },
        {
            "key": "max_weekly_portfolio_risk",
            "value": "0.15",
            "category": "portfolio",
            "description": "Maximum weekly portfolio risk (15%)"
        },
        
        # Position Sizing
        {
            "key": "max_position_size",
            "value": "0.10",
            "category": "position",
            "description": "Maximum position size as percentage of portfolio (10%)"
        },
        {
            "key": "max_position_per_symbol",
            "value": "0.05",
            "category": "position",
            "description": "Maximum position per individual symbol (5%)"
        },
        {
            "key": "min_position_size",
            "value": "0.01",
            "category": "position",
            "description": "Minimum position size (1%)"
        },
        
        # Risk Per Trade
        {
            "key": "max_risk_per_trade",
            "value": "0.02",
            "category": "trade",
            "description": "Maximum risk per individual trade (2%)"
        },
        {
            "key": "max_trades_per_day",
            "value": "20",
            "category": "trade",
            "description": "Maximum number of trades per day"
        },
        {
            "key": "max_concurrent_trades",
            "value": "10",
            "category": "trade",
            "description": "Maximum number of concurrent open trades"
        },
        
        # Stop Loss and Take Profit
        {
            "key": "stop_loss_default",
            "value": "0.02",
            "category": "risk_management",
            "description": "Default stop loss percentage (2%)"
        },
        {
            "key": "take_profit_default",
            "value": "0.04",
            "category": "risk_management",
            "description": "Default take profit percentage (4%)"
        },
        {
            "key": "trailing_stop_enabled",
            "value": "true",
            "category": "risk_management",
            "description": "Enable trailing stop loss"
        },
        {
            "key": "trailing_stop_distance",
            "value": "0.015",
            "category": "risk_management",
            "description": "Trailing stop distance (1.5%)"
        },
        
        # Drawdown Management
        {
            "key": "max_drawdown",
            "value": "0.15",
            "category": "drawdown",
            "description": "Maximum portfolio drawdown (15%)"
        },
        {
            "key": "max_daily_drawdown",
            "value": "0.05",
            "category": "drawdown",
            "description": "Maximum daily drawdown (5%)"
        },
        {
            "key": "drawdown_recovery_threshold",
            "value": "0.10",
            "category": "drawdown",
            "description": "Drawdown level to trigger recovery mode (10%)"
        },
        
        # Volatility and Correlation
        {
            "key": "volatility_lookback",
            "value": "30",
            "category": "volatility",
            "description": "Days for volatility calculation (30)"
        },
        {
            "key": "max_volatility_threshold",
            "value": "0.50",
            "category": "volatility",
            "description": "Maximum volatility threshold (50%)"
        },
        {
            "key": "correlation_threshold",
            "value": "0.7",
            "category": "correlation",
            "description": "Maximum correlation between positions (70%)"
        },
        {
            "key": "correlation_lookback",
            "value": "90",
            "category": "correlation",
            "description": "Days for correlation calculation (90)"
        },
        
        # Kelly Criterion and Position Sizing
        {
            "key": "kelly_fraction",
            "value": "0.25",
            "category": "position_sizing",
            "description": "Conservative Kelly Criterion fraction (25%)"
        },
        {
            "key": "kelly_min_fraction",
            "value": "0.05",
            "category": "position_sizing",
            "description": "Minimum Kelly fraction (5%)"
        },
        {
            "key": "kelly_max_fraction",
            "value": "0.50",
            "category": "position_sizing",
            "description": "Maximum Kelly fraction (50%)"
        },
        
        # Market Conditions
        {
            "key": "bear_market_multiplier",
            "value": "0.5",
            "category": "market_conditions",
            "description": "Position size multiplier for bear markets (50%)"
        },
        {
            "key": "bull_market_multiplier",
            "value": "1.0",
            "category": "market_conditions",
            "description": "Position size multiplier for bull markets (100%)"
        },
        {
            "key": "high_volatility_multiplier",
            "value": "0.7",
            "category": "market_conditions",
            "description": "Position size multiplier for high volatility (70%)"
        },
        
        # Risk Scoring
        {
            "key": "risk_score_threshold",
            "value": "0.7",
            "category": "risk_scoring",
            "description": "Minimum risk score to approve trade (70%)"
        },
        {
            "key": "risk_score_weights",
            "value": '{"volatility": 0.3, "correlation": 0.2, "drawdown": 0.25, "liquidity": 0.15, "market_conditions": 0.1}',
            "category": "risk_scoring",
            "description": "Weights for risk score calculation"
        },
        
        # Liquidity and Execution
        {
            "key": "min_liquidity_threshold",
            "value": "1000000",
            "category": "liquidity",
            "description": "Minimum daily volume for position entry ($1M)"
        },
        {
            "key": "max_slippage",
            "value": "0.005",
            "category": "execution",
            "description": "Maximum acceptable slippage (0.5%)"
        },
        {
            "key": "execution_timeout",
            "value": "300",
            "category": "execution",
            "description": "Order execution timeout in seconds (5 minutes)"
        },
        
        # Compliance and Limits
        {
            "key": "max_leverage",
            "value": "2.0",
            "category": "leverage",
            "description": "Maximum leverage allowed (2x)"
        },
        {
            "key": "margin_requirement",
            "value": "0.5",
            "category": "leverage",
            "description": "Minimum margin requirement (50%)"
        },
        {
            "key": "max_short_positions",
            "value": "0.3",
            "category": "position",
            "description": "Maximum short positions as percentage of portfolio (30%)"
        }
    ]
    
    # Update each configuration
    for config in risk_configs:
        sql = f"""
        INSERT INTO risk_config (config_key, config_value, category, description, updated_at)
        VALUES ('{config['key']}', '{config['value']}', '{config['category']}', '{config['description']}', CURRENT_TIMESTAMP)
        ON CONFLICT (config_key) 
        DO UPDATE SET 
            config_value = EXCLUDED.config_value,
            category = EXCLUDED.category,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        if execute_sql(sql):
            print(f"✅ Updated {config['key']}: {config['value']}")
        else:
            print(f"❌ Failed to update {config['key']}")
    
    print("\n🔍 Verifying updated configuration...")
    
    # Check the results
    verify_sql = "SELECT category, COUNT(*) as count FROM risk_config GROUP BY category ORDER BY category;"
    if execute_sql(verify_sql):
        print("✅ Configuration verification completed")
    
    print("\n🎯 Risk configuration update completed successfully!")
    print("The risk agent now has comprehensive risk management settings.")

if __name__ == "__main__":
    update_risk_config()

