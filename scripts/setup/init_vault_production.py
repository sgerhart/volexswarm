#!/usr/bin/env python3
"""
Initialize Vault in production mode with proper persistence.
This script handles unsealing and setting up initial secrets.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

VAULT_ADDR = "http://localhost:8200"
VAULT_DATA_FILE = Path("vault_init.json")

def wait_for_vault():
    """Wait for vault to be ready."""
    print("Waiting for Vault to be ready...")
    for _ in range(30):
        try:
            response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=5)
            if response.status_code in [200, 429, 472, 473, 501, 503]:
                print("✅ Vault is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False

def initialize_vault():
    """Initialize vault if not already initialized."""
    try:
        # Check if vault is already initialized
        response = requests.get(f"{VAULT_ADDR}/v1/sys/init")
        if response.json().get("initialized"):
            print("✅ Vault is already initialized")
            return load_vault_data()
        
        # Initialize vault
        print("🔧 Initializing Vault...")
        init_data = {
            "secret_shares": 1,
            "secret_threshold": 1
        }
        
        response = requests.post(f"{VAULT_ADDR}/v1/sys/init", json=init_data)
        response.raise_for_status()
        
        vault_data = response.json()
        
        # Save the unseal key and root token securely
        save_vault_data(vault_data)
        
        print("✅ Vault initialized successfully!")
        return vault_data
        
    except Exception as e:
        print(f"❌ Failed to initialize vault: {e}")
        return None

def save_vault_data(vault_data):
    """Save vault initialization data."""
    # In production, this should be stored more securely
    with open(VAULT_DATA_FILE, 'w') as f:
        json.dump(vault_data, f, indent=2)
    
    # Restrict file permissions
    os.chmod(VAULT_DATA_FILE, 0o600)
    print(f"🔒 Vault data saved to {VAULT_DATA_FILE}")

def load_vault_data():
    """Load vault initialization data."""
    if not VAULT_DATA_FILE.exists():
        print(f"❌ Vault data file {VAULT_DATA_FILE} not found")
        return None
    
    with open(VAULT_DATA_FILE, 'r') as f:
        return json.load(f)

def unseal_vault(vault_data):
    """Unseal vault using the unseal key."""
    try:
        # Check if vault is sealed
        response = requests.get(f"{VAULT_ADDR}/v1/sys/seal-status")
        seal_status = response.json()
        
        if not seal_status.get("sealed"):
            print("✅ Vault is already unsealed")
            return True
        
        print("🔓 Unsealing Vault...")
        unseal_data = {
            "key": vault_data["keys"][0]
        }
        
        response = requests.post(f"{VAULT_ADDR}/v1/sys/unseal", json=unseal_data)
        response.raise_for_status()
        
        print("✅ Vault unsealed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to unseal vault: {e}")
        return False

def enable_kv_engine(root_token):
    """Enable KV secrets engine."""
    try:
        headers = {"X-Vault-Token": root_token}
        
        # Check if secret/ path is already enabled
        response = requests.get(f"{VAULT_ADDR}/v1/sys/mounts", headers=headers)
        mounts = response.json()
        
        if "secret/" in mounts.get("data", {}):
            print("✅ KV secrets engine already enabled")
            return True
        
        print("🔧 Enabling KV secrets engine...")
        mount_data = {
            "type": "kv",
            "options": {"version": "2"}
        }
        
        response = requests.post(f"{VAULT_ADDR}/v1/sys/mounts/secret", 
                                json=mount_data, headers=headers)
        response.raise_for_status()
        
        print("✅ KV secrets engine enabled!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to enable KV engine: {e}")
        return False

def restore_existing_secrets(root_token):
    """Restore existing secrets if vault backup exists."""
    backup_dir = Path("backup/vault")
    if not backup_dir.exists():
        print("📝 No existing vault backup found - starting fresh")
        return True
    
    # Check if we have a recent backup to restore
    backup_files = list(backup_dir.glob("vault_backup_*.json.gz.enc"))
    if not backup_files:
        print("📝 No vault backup files found - starting fresh")
        return True
    
    print(f"💾 Found {len(backup_files)} backup files")
    print("🔄 To restore from backup, run: python scripts/database/restore_vault.py")
    return True

def setup_development_secrets(root_token):
    """Set up basic development secrets."""
    try:
        headers = {"X-Vault-Token": root_token}
        
        # Create basic OpenAI secret structure
        openai_secret = {
            "api_key": "your-openai-api-key-here"
        }
        
        response = requests.post(f"{VAULT_ADDR}/v1/secret/data/openai/api_key",
                                json={"data": openai_secret}, headers=headers)
        
        if response.status_code in [200, 204]:
            print("✅ Development secrets structure created")
            print("📝 Please update secrets using: python scripts/setup/add_api_keys.py")
        
        return True
        
    except Exception as e:
        print(f"⚠️  Warning: Could not create development secrets: {e}")
        return True  # Non-critical

def main():
    """Main initialization process."""
    print("🚀 Initializing Vault in Production Mode")
    print("=" * 50)
    
    # Wait for vault to be ready
    if not wait_for_vault():
        print("❌ Vault is not responding. Check if it's running.")
        return False
    
    # Initialize vault
    vault_data = initialize_vault()
    if not vault_data:
        vault_data = load_vault_data()
        if not vault_data:
            print("❌ Could not initialize or load vault data")
            return False
    
    # Unseal vault
    if not unseal_vault(vault_data):
        return False
    
    # Enable KV engine
    root_token = vault_data["root_token"]
    if not enable_kv_engine(root_token):
        return False
    
    # Restore existing secrets or create development structure
    restore_existing_secrets(root_token)
    setup_development_secrets(root_token)
    
    print("=" * 50)
    print("🎉 Vault Production Setup Complete!")
    print(f"🔑 Root Token: {root_token}")
    print("⚠️  Save this token securely - it won't be shown again!")
    print("")
    print("Next steps:")
    print("1. Set up your API keys: python scripts/setup/add_api_keys.py")
    print("2. Create vault backups: python scripts/database/backup_vault.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 