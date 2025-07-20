# VolexSwarm Scripts Documentation

This document provides a comprehensive overview of all scripts in the `scripts/` folder, their purposes, and usage instructions.

## 📁 Script Categories

### 🔧 **Initialization Scripts**
Scripts for setting up and initializing various components of the VolexSwarm system.

#### `init_vault.py`
- **Purpose**: Initialize HashiCorp Vault with KV v2 secrets engine and populate with sample secrets
- **What it does**:
  - Enables KV v2 secrets engine
  - Creates sample API keys for exchanges (Binance, Coinbase, Kraken)
  - Stores database credentials
  - Creates agent configurations for all agents
  - Verifies secrets were created correctly
- **Usage**: `python scripts/init_vault.py`
- **Prerequisites**: Vault container must be running (`docker-compose up -d vault`)

#### `init_openai.py`
- **Purpose**: Initialize OpenAI integration and test API connectivity
- **What it does**:
  - Tests OpenAI API connection
  - Validates API key configuration
  - Tests basic GPT functionality
- **Usage**: `python scripts/init_openai.py`
- **Prerequisites**: OpenAI API key configured in Vault

#### `init_meta_agent.py`
- **Purpose**: Initialize the Meta-Agent with default configurations
- **What it does**:
  - Sets up Meta-Agent configurations in Vault
  - Tests agent coordination
  - Validates natural language processing setup
- **Usage**: `python scripts/init_meta_agent.py`

#### `init_signal_agent.py`
- **Purpose**: Initialize the Signal Agent with ML model configurations
- **What it does**:
  - Sets up signal generation parameters
  - Configures technical indicators
  - Initializes ML model training settings
- **Usage**: `python scripts/init_signal_agent.py`

### 🧪 **Testing Scripts**
Scripts for testing various components and functionality of the system.

#### `test_vault.py`
- **Purpose**: Test Vault integration and secret management
- **What it tests**:
  - Vault connection and authentication
  - Secret retrieval functionality
  - API key management
  - Agent configuration retrieval
  - Secret listing capabilities
- **Usage**: `python scripts/test_vault.py`
- **Environment**: Requires `VAULT_ADDR` and `VAULT_TOKEN` environment variables

#### `test_db.py`
- **Purpose**: Test database integration and TimescaleDB functionality
- **What it tests**:
  - Database connection
  - Table creation and schema validation
  - TimescaleDB hypertables
  - Data insertion and retrieval
  - Structured logging to database
  - Database information and statistics
- **Usage**: `python scripts/test_db.py`
- **Prerequisites**: TimescaleDB container running and Vault configured

#### `test_meta_agent.py`
- **Purpose**: Comprehensive testing of Meta-Agent functionality
- **What it tests**:
  - Health check endpoints
  - System status monitoring
  - Natural language processing commands
  - Agent coordination
  - Direct API endpoints
  - WebSocket connections
- **Usage**: `python scripts/test_meta_agent.py`
- **Prerequisites**: Meta-Agent running on port 8004

#### `test_enhanced_research.py`
- **Purpose**: Test the enhanced research agent capabilities
- **What it tests**:
  - Market data collection
  - Sentiment analysis
  - News aggregation
  - Trend detection
  - Research data APIs
- **Usage**: `python scripts/test_enhanced_research.py`
- **Prerequisites**: Research agent running on port 8001

#### `test_gpt_integration.py`
- **Purpose**: Test OpenAI GPT integration and AI capabilities
- **What it tests**:
  - GPT API connectivity
  - Natural language processing
  - Market analysis generation

#### `test_encryption.py`
- **Purpose**: Test Vault backup encryption functionality
- **What it tests**:
  - AES-256-GCM encryption/decryption
  - Field-level sensitive data encryption
  - Backup file format compatibility
  - Security verification
- **Usage**: `python scripts/test_encryption.py`
- **Prerequisites**: cryptography library installed
  - Sentiment analysis
  - AI-powered insights
- **Usage**: `python scripts/test_gpt_integration.py`
- **Prerequisites**: OpenAI API key configured

#### `test_autonomous_ai.py`
- **Purpose**: Test autonomous AI decision-making capabilities
- **What it tests**:
  - Autonomous signal generation
  - ML model training and inference
  - Decision-making algorithms
  - Risk assessment
  - Performance metrics
- **Usage**: `python scripts/test_autonomous_ai.py`
- **Prerequisites**: Signal agent running and historical data available

### 📊 **Data Management Scripts**
Scripts for managing and populating data in the system.

#### `add_historical_data.py`
- **Purpose**: Add historical price data for ML training and backtesting
- **What it does**:
  - Generates realistic historical price data
  - Populates TimescaleDB with price records
  - Creates data for multiple symbols and timeframes
  - Sets up training data for ML models
- **Usage**: `python scripts/add_historical_data.py`
- **Output**: 30 days of hourly price data for BTCUSD

#### `add_test_data.py`
- **Purpose**: Add test data for development and testing
- **What it does**:
  - Creates sample strategies
  - Adds test trades and signals
  - Populates agent logs
  - Creates test portfolios
- **Usage**: `python scripts/add_test_data.py`

#### `migrate_secrets.py`
- **Purpose**: Migrate existing secrets to proper Vault structure
- **What it does**:
  - Reorganizes existing secrets
  - Updates secret paths and structure
  - Validates secret migration
  - Creates backup before migration
- **Usage**: `python scripts/migrate_secrets.py`

### 💾 **Backup and Recovery Scripts**
Scripts for backing up and restoring system data.

#### `backup.py`
- **Purpose**: Create encrypted backups of Vault secrets
- **What it does**:
  - Recursively fetches all KV secrets from Vault
  - **Encrypts sensitive fields** (API keys, passwords, tokens) using AES-256-GCM
  - Uses PBKDF2 key derivation for security
  - Creates timestamped backup files with metadata
  - Supports both encrypted and unencrypted backups
- **Usage**: 
  - `python scripts/backup.py` (encrypted backup - prompts for master key)
  - `python scripts/backup.py --master-key "your_key"` (encrypted backup with provided key)
  - `python scripts/backup.py --no-encrypt` (unencrypted backup)
- **Security**: Prompts for master key once to encrypt all sensitive data
- **Output**: `backup/vault_kv_backup_YYYYMMDD_HHMMSS.json`

#### `restore.py`
- **Purpose**: Restore Vault secrets from encrypted backup files
- **What it does**:
  - Loads backup files with metadata
  - **Decrypts sensitive data** using master key
  - Supports both new (encrypted) and legacy backup formats
  - Restores secrets to Vault with error handling
  - Lists available backup files
- **Usage**:
  - `python scripts/restore.py <backup_file>` (restore specific backup)
  - `python scripts/restore.py --list` (list available backups)
  - `python scripts/restore.py <backup_file> --master-key <key>` (provide key directly)
- **Security**: Prompts for master key if not provided
- **Compatibility**: Works with both encrypted and legacy backup formats

#### `crypto_utils.py`
- **Purpose**: Cryptographic utilities for backup encryption/decryption
- **What it provides**:
  - `VaultBackupCrypto` class for AES-256-GCM encryption
  - Field-level encryption for sensitive data
  - PBKDF2 key derivation for security
  - Backup format compatibility
- **Security Features**:
  - AES-256-GCM authenticated encryption
  - 100,000 PBKDF2 iterations
  - Random nonce generation
  - Automatic sensitive field detection

#### `backup.sh`
- **Purpose**: Shell script wrapper for backup operations
- **What it does**:
  - Sets environment variables
  - Runs backup script
  - Handles errors
- **Usage**: `./scripts/backup.sh`

#### `restore.sh`
- **Purpose**: Shell script wrapper for restore operations
- **What it does**:
  - Sets environment variables
  - Runs restore script
  - Validates input
- **Usage**: `./scripts/restore.sh <backup_file>`

### 📚 **Documentation and Explanation Scripts**
Scripts that generate documentation and explain system capabilities.

#### `ai_ml_capabilities_explanation.py`
- **Purpose**: Generate comprehensive documentation of AI/ML capabilities
- **What it does**:
  - Documents ML model architectures
  - Explains feature engineering
  - Describes training processes
  - Shows performance metrics
  - Provides usage examples
- **Usage**: `python scripts/ai_ml_capabilities_explanation.py`
- **Output**: Detailed AI/ML documentation

#### `continuous_monitoring_explanation.py`
- **Purpose**: Document continuous monitoring and alerting capabilities
- **What it does**:
  - Explains monitoring architecture
  - Documents alert channels
  - Shows performance tracking
  - Describes anomaly detection
- **Usage**: `python scripts/continuous_monitoring_explanation.py`
- **Output**: Monitoring system documentation

#### `demo_autonomous_system.py`
- **Purpose**: Demonstrate autonomous trading system capabilities
- **What it does**:
  - Shows end-to-end trading workflow
  - Demonstrates autonomous decision making
  - Illustrates agent coordination
  - Provides real-time examples
- **Usage**: `python scripts/demo_autonomous_system.py`
- **Output**: Interactive demonstration

## 🚀 **Usage Workflow**

### Initial Setup
1. **Start Infrastructure**: `docker-compose up -d vault db`
2. **Initialize Vault**: `python scripts/init_vault.py`
3. **Test Vault**: `python scripts/test_vault.py`
4. **Test Database**: `python scripts/test_db.py`

### Development Testing
1. **Add Test Data**: `python scripts/add_historical_data.py`
2. **Test Agents**: `python scripts/test_meta_agent.py`
3. **Test AI**: `python scripts/test_autonomous_ai.py`
4. **Test Research**: `python scripts/test_enhanced_research.py`

### Production Deployment
1. **Backup Current State**: `python scripts/backup.py`
2. **Migrate Secrets**: `python scripts/migrate_secrets.py`
3. **Test All Components**: Run all test scripts
4. **Generate Documentation**: Run explanation scripts

## 🔧 **Environment Variables**

Most scripts require these environment variables:
- `VAULT_ADDR`: Vault server address (default: http://localhost:8200)
- `VAULT_TOKEN`: Vault authentication token (default: root for development)
- `OPENAI_API_KEY`: OpenAI API key for AI features

## 📝 **Notes**

- All scripts are designed to be run from the project root directory
- Scripts automatically add the parent directory to Python path
- Most scripts include error handling and detailed logging
- Test scripts provide clear pass/fail indicators
- Backup scripts create timestamped files to prevent overwrites
- Documentation scripts generate markdown output

## 🐛 **Troubleshooting**

### Common Issues
1. **Vault Connection**: Ensure Vault container is running and accessible
2. **Database Connection**: Check TimescaleDB container and credentials
3. **Environment Variables**: Verify all required env vars are set
4. **Dependencies**: Ensure all Python packages are installed in virtual environment

### Debug Commands
```bash
# Check container status
docker-compose ps

# Check Vault logs
docker logs volexswarm-vault

# Check database logs
docker logs volexstorm-db

# Test individual components
python scripts/test_vault.py
python scripts/test_db.py
``` 