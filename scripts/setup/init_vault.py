#!/usr/bin/env python3
"""
Vault initialization script for VolexSwarm.
Populates Vault with sample secrets and configuration.
"""

import os
import sys
import subprocess
import json
from typing import Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.vault import VaultClient


def run_vault_command(command: str) -> str:
    """Run a Vault CLI command."""
    try:
        result = subprocess.run(
            f"docker exec -it volexswarm-vault vault {command}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Warning: Command failed: {result.stderr}")
        return result.stdout
    except Exception as e:
        print(f"Error running Vault command: {e}")
        return ""


def initialize_vault():
    """Initialize Vault with KV v2 secrets engine."""
    print("Initializing Vault...")
    
    # Enable KV v2 secrets engine
    print("Enabling KV v2 secrets engine...")
    run_vault_command("secrets enable -path=secret kv-v2")
    
    print("Vault initialization complete!")


def create_sample_secrets():
    """Create sample secrets for development."""
    print("Creating sample secrets...")
    
    # Sample API keys (replace with real ones for production)
    api_keys = {
        "binance": {
            "api_key": "your_binance_api_key_here",
            "secret_key": "your_binance_secret_key_here"
        },
        "coinbase": {
            "api_key": "your_coinbase_api_key_here",
            "secret_key": "your_coinbase_secret_key_here"
        },
        "kraken": {
            "api_key": "your_kraken_api_key_here",
            "secret_key": "your_kraken_secret_key_here"
        }
    }
    
    # Store API keys
    for exchange, credentials in api_keys.items():
        print(f"Storing {exchange} API credentials...")
        for key_type, value in credentials.items():
            run_vault_command(f"kv put secret/api_keys/{exchange} {key_type}=\"{value}\"")
    
    # Database credentials
    print("Storing database credentials...")
    db_creds = {
        "host": "db",
        "port": "5432",
        "database": "volextrades",
        "username": "volex",
        "password": "volex_pass"
    }
    
    for key, value in db_creds.items():
        run_vault_command(f"kv put secret/databases/default {key}=\"{value}\"")
    
    # Agent configurations
    agent_configs = {
        "research": {
            "data_sources": "['binance', 'coinbase']",
            "update_interval": "300",
            "max_requests_per_minute": "60",
            "enabled_pairs": "['BTC/USDT', 'ETH/USDT', 'ADA/USDT']"
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
            "default_exchange": "binance",
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
        print(f"Storing {agent} agent configuration...")
        for key, value in config.items():
            run_vault_command(f"kv put secret/agents/{agent} {key}=\"{value}\"")
    
    print("Sample secrets created successfully!")


def verify_secrets():
    """Verify that secrets were created correctly."""
    print("Verifying secrets...")
    
    try:
        # Test Vault client connection
        vault_client = VaultClient()
        
        # Test API key retrieval
        binance_creds = vault_client.get_exchange_credentials("binance")
        if binance_creds:
            print("✓ Binance credentials retrieved successfully")
        else:
            print("✗ Failed to retrieve Binance credentials")
        
        # Test agent configuration
        research_config = vault_client.get_agent_config("research")
        if research_config:
            print("✓ Research agent configuration retrieved successfully")
        else:
            print("✗ Failed to retrieve research agent configuration")
        
        # Test database credentials
        db_creds = vault_client.get_database_credentials("default")
        if db_creds:
            print("✓ Database credentials retrieved successfully")
        else:
            print("✗ Failed to retrieve database credentials")
        
        # List all secrets
        secrets = vault_client.list_secrets()
        print(f"✓ Found {len(secrets)} top-level secret paths")
        
        print("Vault verification complete!")
        
    except Exception as e:
        print(f"Error verifying secrets: {e}")


def main():
    """Main function."""
    print("VolexSwarm Vault Initialization Script")
    print("=" * 40)
    
    # Check if Vault container is running
    try:
        result = subprocess.run(
            "docker ps --filter name=volexswarm-vault --format '{{.Names}}'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "volexswarm-vault" not in result.stdout:
            print("Error: Vault container is not running!")
            print("Please start the infrastructure first:")
            print("  docker-compose up -d vault db")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking Vault container: {e}")
        sys.exit(1)
    
    # Initialize Vault
    initialize_vault()
    
    # Create sample secrets
    create_sample_secrets()
    
    # Verify secrets
    verify_secrets()
    
    print("\nVault initialization complete!")
    print("\nNext steps:")
    print("1. Replace sample API keys with real ones")
    print("2. Start your agents: docker-compose up research")
    print("3. Test the API: curl http://localhost:8001/health")


if __name__ == "__main__":
    main() 