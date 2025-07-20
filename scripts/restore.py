import hvac
import json
import os
import sys

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

def restore_vault(backup_path):
    if not os.path.exists(backup_path):
        print(f"❌ Backup file does not exist: {backup_path}")
        return

    with open(backup_path, "r") as f:
        secrets = json.load(f)

    client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

    if not client.is_authenticated():
        print("❌ Vault authentication failed.")
        return

    print(f"♻️ Restoring secrets from {backup_path}...")
    restore_secrets(client, KV_MOUNT_PATH, secrets)
    print("✅ Vault KV restore completed.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Usage: python scripts/restore_vault_kv.py <backup_file>")
        sys.exit(1)

    restore_vault(sys.argv[1])