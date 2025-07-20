#!/bin/bash

echo "🔄 Backing up volexswarm volumes..."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backup/$TIMESTAMP"
mkdir -p "$BACKUP_DIR"


# Vault data (volume copy – only if persistent Vault is used)
echo "📦 Backing up Vault data..."
docker cp volexswarm-vault:/vault/data "$BACKUP_DIR/vault_data"

echo "✅ Backup complete: $BACKUP_DIR"

