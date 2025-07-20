
import hvac
import json
import os
from datetime import datetime
from crypto_utils import encrypt_sensitive_fields, VaultBackupCrypto

# Vault Configuration
VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "root")
KV_MOUNT_PATH = "secret"  # default for dev mode
BACKUP_DIR = "backup"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FILE = f"{BACKUP_DIR}/vault_kv_backup_{TIMESTAMP}.json"

def get_all_kv_secrets(client, mount_point, path=""):
    """Recursively fetch all KV secrets from Vault."""
    try:
        response = client.secrets.kv.v2.list_secrets(mount_point=mount_point, path=path)
        secrets = response["data"]["keys"]
    except hvac.exceptions.InvalidPath:
        return {}
    except Exception as e:
        print(f"Error listing secrets at path '{path}': {e}")
        return {}

    kv_data = {}
    for secret in secrets:
        full_path = f"{path}{secret}"
        if secret.endswith('/'):
            # Recursively fetch nested secrets
            kv_data[full_path] = get_all_kv_secrets(client, mount_point, full_path)
        else:
            try:
                secret_data = client.secrets.kv.v2.read_secret_version(
                    mount_point=mount_point,
                    path=full_path,
                    raise_on_deleted_version=True  # suppress deprecation warning
                )
                kv_data[full_path] = secret_data["data"]["data"]
            except Exception as e:
                print(f"Error reading secret {full_path}: {e}")

    return kv_data

def backup_vault(encrypt_sensitive=True, master_key=None):
    """
    Backup Vault secrets with optional encryption of sensitive data.
    
    Args:
        encrypt_sensitive: If True, encrypt sensitive fields like API keys
        master_key: Optional master key (will prompt if not provided and encryption enabled)
    """
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

    if not client.is_authenticated():
        print("❌ Vault authentication failed.")
        return

    print("🔐 Fetching secrets from Vault...")
    secrets = get_all_kv_secrets(client, KV_MOUNT_PATH)

    if encrypt_sensitive:
        print("🔒 Encrypting sensitive data...")
        try:
            # Create a single crypto instance to avoid multiple prompts
            crypto = VaultBackupCrypto(master_key)
            secrets = encrypt_sensitive_fields(secrets, crypto_instance=crypto)
            print("✅ Sensitive data encrypted successfully")
        except Exception as e:
            print(f"⚠️  Warning: Failed to encrypt sensitive data: {e}")
            print("   Proceeding with unencrypted backup...")
    
    # Add backup metadata
    backup_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "vault_addr": VAULT_ADDR,
            "encrypted": encrypt_sensitive,
            "version": "2.0",
            "description": "VolexSwarm Vault backup with encrypted sensitive data"
        },
        "secrets": secrets
    }

    print(f"💾 Saving backup to {BACKUP_FILE}...")
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        json.dump(backup_data, f, indent=4)

    print("✅ Vault KV backup completed!")
    if encrypt_sensitive:
        print("🔐 Backup contains encrypted sensitive data")
        print("   Store your master key securely - you'll need it to restore!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup Vault secrets with encryption")
    parser.add_argument("--no-encrypt", action="store_true", 
                       help="Skip encryption of sensitive data (not recommended)")
    parser.add_argument("--master-key", help="Master key for encryption (will prompt if not provided)")
    
    args = parser.parse_args()
    
    backup_vault(encrypt_sensitive=not args.no_encrypt, master_key=args.master_key)
