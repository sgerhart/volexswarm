#!/bin/bash

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "❌ Usage: ./restore.sh <backup-folder-path>"
  exit 1
fi

echo "♻️ Restoring volexswarm environment from $BACKUP_DIR..."


# Restore Vault
echo "📥 Restoring Vault..."
docker cp "$BACKUP_DIR/vault_data" volexswarm-vault:/vault/data

echo "✅ Restore complete."

