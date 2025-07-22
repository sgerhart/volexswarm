# VolexSwarm Scripts

This directory contains organized scripts for managing the VolexSwarm trading system.

## 📁 Directory Structure

### `database/` - Database Management Scripts
- **`setup_schema.py`** - Set up complete database schema for new deployments
- **`backup_vault.py`** - Secure Vault backup with encryption
- **`restore_vault.py`** - Restore Vault secrets from encrypted backup
- **`view_backup.py`** - View backup contents without restoring
- **`optimize.py`** - Database optimization and maintenance
- **`reset.py`** - Reset database to clean state

### `setup/` - Initialization Scripts
- **`init_openai.py`** - Initialize OpenAI configuration
- **`init_signal_agent.py`** - Initialize signal agent
- **`init_meta_agent.py`** - Initialize meta agent
- **`init_vault.py`** - Initialize Vault secrets

### `data/` - Data Management Scripts
- **`add_historical_data.py`** - Add historical market data
- **`add_test_data.py`** - Add test data for development

### `test/` - Testing Scripts
- **`test_db.py`** - Database connection tests
- **`test_encryption.py`** - Encryption functionality tests
- **`test_autonomous_ai.py`** - Autonomous AI system tests
- **`test_enhanced_research.py`** - Enhanced research tests
- **`test_gpt_integration.py`** - GPT integration tests
- **`test_meta_agent.py`** - Meta agent tests

### `dev/` - Development Scripts
- Development and debugging utilities

### `utilities/` - Utility Scripts
- **`crypto_utils.py`** - Cryptographic utilities

### `legacy/` - Legacy Scripts (Deprecated)
- Old backup/restore scripts
- Deprecated functionality
- Migration scripts

## 🔐 Vault Management

### Creating a Backup
```bash
pyenv activate volexswarm-env
python scripts/database/backup_vault.py
```

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

## 🚀 Quick Start

1. **Setup Database Schema**: `python scripts/database/setup_schema.py`
2. **Initialize Vault**: `python scripts/setup/init_vault.py`
3. **Add API Keys**: `python scripts/setup/init_openai.py`
4. **Test Setup**: `python scripts/test/test_db.py`

## 📝 Notes

- All scripts should be run with the `volexswarm-env` virtual environment
- Vault operations require the Vault container to be running
- Backup files are stored in `backup/vault/` with encryption
- Legacy scripts are kept for reference but not recommended for use 