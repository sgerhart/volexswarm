#!/usr/bin/env python3
"""
Comprehensive system initialization script for VolexSwarm.
Automatically sets up Vault and database when containers restart.
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def run_command(command: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            print(f"❌ Command failed: {command}")
            print(f"Error: {result.stderr}")
        return result
    except Exception as e:
        print(f"❌ Command error: {e}")
        if check:
            raise
        return subprocess.CompletedProcess(command, 1, "", str(e))

def wait_for_service(service_name: str, port: int, max_retries: int = 30) -> bool:
    """Wait for a service to be ready."""
    print(f"⏳ Waiting for {service_name} to be ready...")
    
    for i in range(max_retries):
        try:
            if service_name == "Database":
                # For database, check if we can connect via psql
                result = run_command("docker exec volexstorm-db psql -U volex -d volextrades -c 'SELECT 1;'", check=False)
            else:
                # For other services, check health endpoint
                result = run_command(f"curl -s http://localhost:{port}/health", check=False)
            
            if result.returncode == 0:
                print(f"✅ {service_name} is ready!")
                return True
        except:
            pass
        
        print(f"   Attempt {i+1}/{max_retries}...")
        time.sleep(2)
    
    print(f"❌ {service_name} failed to start within {max_retries * 2} seconds")
    return False

def initialize_vault():
    """Initialize Vault with secrets."""
    print("🔐 Initializing Vault...")
    
    # Enable KV v2 secrets engine
    print("   Enabling KV v2 secrets engine...")
    run_command("export VAULT_ADDR=http://localhost:8200 && export VAULT_TOKEN=root && vault secrets enable -path=secret kv-v2", check=False)
    
    # Add sample API keys
    print("   Adding sample API keys...")
    api_keys = {
        "binance": {"api_key": "your_binance_api_key_here", "secret_key": "your_binance_secret_key_here"},
        "coinbase": {"api_key": "your_coinbase_api_key_here", "secret_key": "your_coinbase_secret_key_here"},
        "kraken": {"api_key": "your_kraken_api_key_here", "secret_key": "your_kraken_secret_key_here"}
    }
    
    for exchange, credentials in api_keys.items():
        print(f"     Adding {exchange} credentials...")
        cmd = f"export VAULT_ADDR=http://localhost:8200 && export VAULT_TOKEN=root && vault kv put secret/api_keys/{exchange}"
        for key, value in credentials.items():
            cmd += f" {key}='{value}'"
        run_command(cmd, check=False)
    
    # Add agent configurations
    print("   Adding agent configurations...")
    agent_configs = {
        "research": {
            "data_sources": '["binance", "coinbase"]',
            "update_interval": "300",
            "max_requests_per_minute": "60"
        },
        "signal": {
            "indicators": '["RSI", "MACD", "Bollinger_Bands"]',
            "timeframes": '["1h", "4h", "1d"]',
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
        }
    }
    
    for agent, config in agent_configs.items():
        print(f"     Adding {agent} configuration...")
        cmd = f"export VAULT_ADDR=http://localhost:8200 && export VAULT_TOKEN=root && vault kv put secret/agents/{agent}"
        for key, value in config.items():
            cmd += f" {key}='{value}'"
        run_command(cmd, check=False)
    
    print("✅ Vault initialization complete!")

def setup_database_schema():
    """Set up database schema."""
    print("🗄️  Setting up database schema...")
    
    # Run the existing setup_schema.py script
    script_path = os.path.join(os.path.dirname(__file__), "..", "database", "setup_schema.py")
    result = run_command(f"PYTHONPATH={os.path.dirname(os.path.dirname(os.path.dirname(__file__)))} python {script_path}", check=False)
    
    if result.returncode == 0:
        print("✅ Database schema setup complete!")
    else:
        print("⚠️  Database schema setup had issues, but continuing...")

def verify_system():
    """Verify that the system is properly initialized."""
    print("🔍 Verifying system initialization...")
    
    # Check Vault secrets
    print("   Checking Vault secrets...")
    result = run_command("export VAULT_ADDR=http://localhost:8200 && export VAULT_TOKEN=root && vault kv list secret/", check=False)
    if result.returncode == 0 and "api_keys" in result.stdout:
        print("   ✅ Vault secrets found")
    else:
        print("   ❌ Vault secrets not found")
    
    # Check database tables
    print("   Checking database tables...")
    result = run_command("docker exec volexstorm-db psql -U volex -d volextrades -c '\\dt'", check=False)
    if result.returncode == 0 and "strategies" in result.stdout:
        print("   ✅ Database tables found")
    else:
        print("   ❌ Database tables not found")
    
    # Check agent health
    print("   Checking agent health...")
    agents = [
        ("Research Agent", 8001),
        ("Strategy Agent", 8011),
        ("Execution Agent", 8002),
        ("Signal Agent", 8003),
        ("Meta Agent", 8004),
        ("Risk Agent", 8009),
        ("Compliance Agent", 8010)
    ]
    
    healthy_agents = 0
    for name, port in agents:
        try:
            result = run_command(f"curl -s http://localhost:{port}/health", check=False)
            if result.returncode == 0 and "healthy" in result.stdout:
                print(f"   ✅ {name} is healthy")
                healthy_agents += 1
            else:
                print(f"   ❌ {name} is not healthy")
        except:
            print(f"   ❌ {name} is not responding")
    
    print(f"✅ System verification complete! {healthy_agents}/{len(agents)} agents are healthy")

def main():
    """Main function."""
    print("🚀 VolexSwarm System Initialization")
    print("=" * 50)
    
    # Check if containers are running
    print("🔍 Checking container status...")
    result = run_command("docker-compose ps --format 'table {{.Name}}\t{{.Status}}'", check=False)
    if result.returncode != 0:
        print("❌ Error checking container status")
        return
    
    print(result.stdout)
    
    # Wait for core services
    print("\n⏳ Waiting for core services...")
    
    # Wait for Vault
    if not wait_for_service("Vault", 8200):
        print("❌ Vault is not ready. Please check the container logs.")
        return
    
    # Wait for Database
    if not wait_for_service("Database", 5432):
        print("❌ Database is not ready. Please check the container logs.")
        return
    
    # Initialize Vault
    initialize_vault()
    
    # Setup database schema
    setup_database_schema()
    
    # Wait for agents to be ready
    print("\n⏳ Waiting for agents to be ready...")
    time.sleep(10)  # Give agents time to start
    
    # Verify system
    verify_system()
    
    print("\n🎉 System initialization complete!")
    print("\n📋 Next steps:")
    print("1. Replace sample API keys with real ones in Vault")
    print("2. Access the WebUI at: http://localhost:8005")
    print("3. Monitor agent status in the Agent Management interface")
    print("4. Check logs if any agents are not healthy")

if __name__ == "__main__":
    main() 