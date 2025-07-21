#!/usr/bin/env python3
"""
Script to add API keys to Vault for VolexSwarm.
"""

import requests
import json
import getpass
import sys

VAULT_ADDR = "http://localhost:8200"
VAULT_TOKEN = "root"

def add_secret_to_vault(path: str, data: dict):
    """Add a secret to Vault."""
    url = f"{VAULT_ADDR}/v1/secret/data/{path}"
    headers = {"X-Vault-Token": VAULT_TOKEN}
    
    response = requests.post(url, headers=headers, json={"data": data})
    
    if response.status_code == 200:
        print(f"✅ Successfully added secret: {path}")
        return True
    else:
        print(f"❌ Failed to add secret {path}: {response.status_code} - {response.text}")
        return False

def add_openai_key():
    """Add OpenAI API key to Vault."""
    print("\n=== Adding OpenAI API Key ===")
    api_key = getpass.getpass("Enter your OpenAI API key: ")
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    data = {"api_key": api_key}
    return add_secret_to_vault("api_keys/openai", data)

def add_binance_keys():
    """Add Binance API keys to Vault."""
    print("\n=== Adding Binance API Keys ===")
    print("Choose your Binance exchange:")
    print("1. Binance.US (US-regulated, for US users)")
    print("2. Binance.com (International, for non-US users)")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        exchange_name = "binanceus"
        print("Using Binance.US (US-regulated)")
    elif choice == "2":
        exchange_name = "binance"
        print("Using Binance.com (International)")
    else:
        print("❌ Invalid choice. Using Binance.US as default.")
        exchange_name = "binanceus"
    
    api_key = getpass.getpass(f"Enter your {exchange_name} API key: ")
    secret_key = getpass.getpass(f"Enter your {exchange_name} secret key: ")
    
    if not api_key or not secret_key:
        print("❌ Both API key and secret key are required")
        return False
    
    data = {
        "api_key": api_key,
        "secret_key": secret_key
    }
    return add_secret_to_vault(f"api_keys/{exchange_name}", data)

def test_vault_connection():
    """Test Vault connection."""
    try:
        response = requests.get(f"{VAULT_ADDR}/v1/sys/health")
        if response.status_code == 200:
            print("✅ Vault connection successful")
            return True
        else:
            print(f"❌ Vault connection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Vault connection error: {e}")
        return False

def main():
    """Main function."""
    print("🔐 VolexSwarm API Key Configuration")
    print("=" * 40)
    
    # Test Vault connection
    if not test_vault_connection():
        print("❌ Cannot connect to Vault. Make sure it's running.")
        return
    
    print("\nThis script will help you add your API keys to Vault securely.")
    print("Your keys will be stored encrypted in Vault and used by the VolexSwarm agents.")
    
    success_count = 0
    
    # Add OpenAI key
    if add_openai_key():
        success_count += 1
    
    # Add Binance keys
    if add_binance_keys():
        success_count += 1
    
    print(f"\n{'='*40}")
    print(f"✅ Successfully added {success_count}/2 API key sets")
    
    if success_count > 0:
        print("\n🎉 API keys added successfully!")
        print("The VolexSwarm agents will now be able to use these keys.")
        print("\nNext steps:")
        print("1. Restart the agents to pick up the new keys")
        print("2. Check the web UI to see updated status")
        print("3. Test the research and execution agents")
    else:
        print("\n❌ No API keys were added. Please try again.")

if __name__ == "__main__":
    main() 