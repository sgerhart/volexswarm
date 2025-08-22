# VolexSwarm Scripts

This directory contains essential scripts for managing the VolexSwarm trading system database and vault operations.

## 📁 Directory Structure

### `database/` - Database Management Scripts
Essential scripts for database operations and maintenance:

- **`setup_schema.py`** - Set up complete database schema for new deployments
- **`backup_vault.py`** - Secure Vault backup with encryption
- **`restore_vault.py`** - Restore Vault secrets from encrypted backup
- **`view_backup.py`** - View backup contents without restoring
- **`optimize.py`** - Database optimization and maintenance
- **`reset.py`** - Reset database to clean state
- **`migrate_price_data_columns.py`** - Migrate price data columns for schema updates

---

## 🔐 Vault Management

### Creating a Backup
```bash
pyenv activate volexswarm-env
python scripts/database/backup_vault.py
```

### Data Persistence
- **Database**: Automatic persistence via Docker volume `db_data:/var/lib/postgresql/data`
- **Vault**: Production mode with file storage backend to `vault_data:/vault/data`
- Both systems maintain data across container restarts

### Viewing Backup Contents
```bash
pyenv activate volexswarm-env
python scripts/database/view_backup.py
```

### Restoring from Backup
```bash
pyenv activate volexswarm-env
python scripts/database/restore_vault.py
```

---

## 🚀 Quick Start

1. **Setup Database Schema**: `python scripts/database/setup_schema.py`
2. **Test Database Connection**: `python scripts/database/test_db.py`
3. **Optimize Database**: `python scripts/database/optimize.py`

---

## 📝 Notes

- All scripts should be run with the `volexswarm-env` virtual environment
- Vault operations require the Vault container to be running
- Backup files are stored in `backup/vault/` with encryption
- Database operations require the TimescaleDB container to be running

---

## 🧹 Cleanup Summary

The following outdated script categories have been removed:
- **Test Scripts**: All agentic framework tests (incompatible with current architecture)
- **Setup Scripts**: Agent initialization scripts (superseded by agentic framework)
- **Utility Scripts**: Health endpoint scripts (no longer needed)
- **Security Scripts**: Redundant security scripts
- **Development Scripts**: Outdated development utilities
- **Data Scripts**: Historical data management scripts

Only essential database and vault management scripts remain. 