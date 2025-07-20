import hvac
import json
import os
import sys
from crypto_utils import decrypt_sensitive_fields, prompt_for_master_key, VaultBackupCrypto

# Vault Configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
KV_MOUNT_PATH = "secret"

def restore_secrets(client, mount_point, data, path=""):
    """Recursively restore KV secrets to Vault."""
    for key, value in data.items():
        full_path = f"{path}{key}"
        if isinstance(value, dict) and all(isinstance(v, dict) for v in value.values()):
            # Nested structure
            restore_secrets(client, mount_point, value, full_path)
        else:
            try:
                client.secrets.kv.v2.create_or_update_secret(
                    mount_point=mount_point,
                    path=full_path,
                    secret=value
                )
                print(f"✅ Restored: {full_path}")
            except Exception as e:
                print(f"❌ Failed to restore {full_path}: {e}")

def restore_vault(backup_path, master_key=None):
    """
    Restore Vault secrets from backup file.
    
    Args:
        backup_path: Path to backup file
        master_key: Master key for decryption (will prompt if not provided)
    """
    if not os.path.exists(backup_path):
        print(f"❌ Backup file does not exist: {backup_path}")
        return

    print(f"📂 Loading backup from {backup_path}...")
    with open(backup_path, "r") as f:
        backup_data = json.load(f)

    # Handle both old and new backup formats
    if "metadata" in backup_data:
        # New format with metadata
        metadata = backup_data["metadata"]
        secrets = backup_data["secrets"]
        is_encrypted = metadata.get("encrypted", False)
        version = metadata.get("version", "1.0")
        
        print(f"📊 Backup metadata:")
        print(f"   Version: {version}")
        print(f"   Timestamp: {metadata.get('timestamp', 'Unknown')}")
        print(f"   Encrypted: {is_encrypted}")
        print(f"   Description: {metadata.get('description', 'N/A')}")
    else:
        # Old format (direct secrets)
        secrets = backup_data
        is_encrypted = False
        print("📊 Legacy backup format detected")

    # Decrypt if necessary
    if is_encrypted:
        if not master_key:
            master_key = prompt_for_master_key()
        
        print("🔓 Decrypting sensitive data...")
        try:
            secrets = decrypt_sensitive_fields(secrets, master_key)
            print("✅ Sensitive data decrypted successfully")
        except Exception as e:
            print(f"❌ Failed to decrypt sensitive data: {e}")
            print("   Cannot proceed with encrypted backup without valid master key")
            return
    else:
        print("ℹ️  Backup contains unencrypted data")

    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

    if not client.is_authenticated():
        print("❌ Vault authentication failed.")
        return

    print(f"♻️ Restoring secrets to Vault...")
    restore_secrets(client, KV_MOUNT_PATH, secrets)
    print("✅ Vault KV restore completed.")

def list_backups():
    """List available backup files."""
    backup_dir = "backup"
    if not os.path.exists(backup_dir):
        print("❌ No backup directory found")
        return
    
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
    
    if not backup_files:
        print("❌ No backup files found")
        return
    
    print("📋 Available backup files:")
    for i, filename in enumerate(sorted(backup_files, reverse=True), 1):
        filepath = os.path.join(backup_dir, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            if "metadata" in data:
                metadata = data["metadata"]
                encrypted = metadata.get("encrypted", False)
                timestamp = metadata.get("timestamp", "Unknown")
                description = metadata.get("description", "N/A")
                print(f"  {i}. {filename}")
                print(f"     📅 {timestamp}")
                print(f"     🔐 Encrypted: {encrypted}")
                print(f"     📝 {description}")
            else:
                print(f"  {i}. {filename} (Legacy format)")
        except Exception as e:
            print(f"  {i}. {filename} (Error reading: {e})")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Restore Vault secrets from encrypted backup")
    parser.add_argument("backup_file", nargs="?", help="Path to backup file")
    parser.add_argument("--list", action="store_true", help="List available backup files")
    parser.add_argument("--master-key", help="Master key for decryption (will prompt if not provided)")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    elif args.backup_file:
        restore_vault(args.backup_file, args.master_key)
    else:
        print("❌ Usage: python scripts/restore.py <backup_file>")
        print("   Or: python scripts/restore.py --list")
        sys.exit(1)