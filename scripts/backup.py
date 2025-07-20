
import hvac
import json
import os
from datetime import datetime

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

def backup_vault():
    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

    if not client.is_authenticated():
        print("❌ Vault authentication failed.")
        return

    print("🔐 Fetching secrets from Vault...")
    secrets = get_all_kv_secrets(client, KV_MOUNT_PATH)

    print(f"💾 Saving backup to {BACKUP_FILE}...")
    os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
    with open(BACKUP_FILE, "w") as f:
        json.dump(secrets, f, indent=4)

    print("✅ Vault KV backup completed!")

if __name__ == "__main__":
    backup_vault()
