#!/usr/bin/env python3
"""
Migration script to reorganize existing Vault secrets for VolexSwarm.
"""

import os
import sys
import hvac
from typing import Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.vault import VaultClient


def migrate_existing_secrets():
    """Migrate existing secrets to the expected VolexSwarm structure."""
    print("Migrating existing secrets to VolexSwarm structure...")
    
    try:
        client = VaultClient()
        
        # Get existing secrets
        existing_secrets = client.list_secrets()
        print(f"Found existing secrets: {existing_secrets}")
        
        # Migrate Binance credentials (fix typo)
        if "biance" in existing_secrets:
            print("Migrating 'biance' to 'api_keys/binance'...")
            biance_creds = client.get_secret("biance")
            if biance_creds:
                # Store in new structure
                client.client.secrets.kv.v2.create_or_update_secret(
                    mount_point="secret",
                    path="api_keys/binance",
                    secret={
                        "api_key": biance_creds.get("api_key"),
                        "secret_key": biance_creds.get("api_secret")
                    }
                )
                print("✓ Migrated Binance credentials")
        
        # Migrate OpenAI credentials
        if "openai" in existing_secrets:
            print("Migrating OpenAI credentials...")
            openai_creds = client.get_secret("openai")
            if openai_creds:
                # Store in new structure
                client.client.secrets.kv.v2.create_or_update_secret(
                    mount_point="secret",
                    path="api_keys/openai",
                    secret={
                        "api_key": openai_creds.get("api_key")
                    }
                )
                print("✓ Migrated OpenAI credentials")
        
        # Create default agent configurations
        print("Creating default agent configurations...")
        
        agent_configs = {
            "research": {
                "data_sources": "['binanceus', 'coinbase']",
                "update_interval": "300",
                "max_requests_per_minute": "60",
                "enabled_pairs": "['BTC/USD', 'ETH/USD', 'ADA/USD']"
            },
            "signal": {
                "indicators": "['RSI', 'MACD', 'Bollinger_Bands']",
                "timeframes": "['1h', '4h', '1d']",
                "signal_threshold": "0.7"
            },
            "strategy": {
                "max_position_size": "0.1",
                "stop_loss_pct": "0.05",
                "take_profit_pct": "0.15",
                "max_open_trades": "5"
            },
            "execution": {
                "default_exchange": "binanceus",
                "order_timeout": "30",
                "retry_attempts": "3"
            },
            "risk": {
                "max_portfolio_risk": "0.02",
                "max_drawdown": "0.15",
                "position_sizing_method": "kelly"
            },
            "monitor": {
                "check_interval": "60",
                "alert_channels": "['email', 'slack']",
                "log_level": "INFO"
            }
        }
        
        for agent, config in agent_configs.items():
            client.client.secrets.kv.v2.create_or_update_secret(
                mount_point="secret",
                path=f"agents/{agent}",
                secret=config
            )
            print(f"✓ Created {agent} agent configuration")
        
        # Create database credentials
        print("Creating database credentials...")
        db_creds = {
            "host": "db",
            "port": "5432",
            "database": "volextrades",
            "username": "volex",
            "password": "volex_pass"
        }
        
        client.client.secrets.kv.v2.create_or_update_secret(
            mount_point="secret",
            path="databases/default",
            secret=db_creds
        )
        print("✓ Created database credentials")
        
        print("\nMigration completed successfully!")
        print("\nNew secret structure:")
        print("secret/")
        print("├── api_keys/")
        print("│   ├── binance/")
        print("│   └── openai/")
        print("├── databases/")
        print("│   └── default/")
        print("└── agents/")
        print("    ├── research/")
        print("    ├── signal/")
        print("    ├── strategy/")
        print("    ├── execution/")
        print("    ├── risk/")
        print("    └── monitor/")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        return False
    
    return True


def verify_migration():
    """Verify that the migration was successful."""
    print("\nVerifying migration...")
    
    try:
        client = VaultClient()
        
        # Test new structure
        binance_creds = client.get_exchange_credentials("binance")
        if binance_creds:
            print("✓ Binance credentials accessible")
        else:
            print("✗ Binance credentials not found")
        
        openai_key = client.get_secret("api_keys/openai")
        if openai_key:
            print("✓ OpenAI credentials accessible")
        else:
            print("✗ OpenAI credentials not found")
        
        research_config = client.get_agent_config("research")
        if research_config:
            print("✓ Research agent configuration accessible")
        else:
            print("✗ Research agent configuration not found")
        
        db_creds = client.get_database_credentials("default")
        if db_creds:
            print("✓ Database credentials accessible")
        else:
            print("✗ Database credentials not found")
        
        # List all secrets
        secrets = client.list_secrets()
        print(f"✓ Found {len(secrets)} top-level secret paths: {secrets}")
        
        return True
        
    except Exception as e:
        print(f"Error during verification: {e}")
        return False


def main():
    """Main migration function."""
    print("VolexSwarm Secret Migration")
    print("=" * 30)
    
    # Check if Vault is accessible
    try:
        client = VaultClient()
        print("✓ Vault connection successful")
    except Exception as e:
        print(f"✗ Vault connection failed: {e}")
        return 1
    
    # Perform migration
    if migrate_existing_secrets():
        # Verify migration
        if verify_migration():
            print("\n✅ Migration completed successfully!")
            print("\nYou can now:")
            print("1. Start your agents: docker-compose up research")
            print("2. Test the API: curl http://localhost:8001/health")
            print("3. Run tests: python scripts/test_vault.py")
            return 0
        else:
            print("\n⚠️ Migration completed but verification failed")
            return 1
    else:
        print("\n❌ Migration failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 