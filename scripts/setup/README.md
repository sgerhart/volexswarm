# VolexSwarm Setup Scripts

This directory contains scripts for setting up and initializing the VolexSwarm system.

## Quick Start

After starting the containers with `docker-compose up -d`, run the system initialization script:

```bash
# Make sure you're in the project root directory
cd /path/to/volexswarm

# Run the comprehensive system initialization
python scripts/setup/init_system.py
```

## Scripts Overview

### `init_system.py` - Comprehensive System Initialization
**Purpose**: Automatically sets up Vault and database when containers restart.

**What it does**:
- Waits for Vault and Database containers to be ready
- Initializes Vault with KV v2 secrets engine
- Adds sample API keys (binance, coinbase, kraken)
- Adds agent configurations for all agents
- Sets up database schema
- Verifies system health

**Usage**:
```bash
python scripts/setup/init_system.py
```

**When to use**:
- After starting containers for the first time
- After restarting containers (Vault and DB lose data on restart)
- When setting up a new environment

### `init_vault.py` - Vault Initialization
**Purpose**: Sets up Vault with sample secrets and configurations.

**What it does**:
- Enables KV v2 secrets engine
- Creates sample API keys
- Adds agent configurations
- Verifies secrets were created correctly

**Usage**:
```bash
PYTHONPATH=/path/to/volexswarm python scripts/setup/init_vault.py
```

### `add_api_keys.py` - Add Real API Keys
**Purpose**: Replace sample API keys with real ones.

**Usage**:
```bash
python scripts/setup/add_api_keys.py
```

### `init_openai.py` - OpenAI Configuration
**Purpose**: Set up OpenAI API configuration in Vault.

**Usage**:
```bash
python scripts/setup/init_openai.py
```

## Persistence Issue

**Important**: Vault and Database containers lose their data when restarted because they use temporary storage. This is why you need to run the initialization script after each restart.

### Solution
The `init_system.py` script automatically handles this by:
1. Detecting when containers are ready
2. Re-initializing Vault with all necessary secrets
3. Setting up the database schema
4. Verifying everything is working

### Manual Steps (if needed)
If you need to manually restore data:

1. **Vault**:
   ```bash
   export VAULT_ADDR=http://localhost:8200
   export VAULT_TOKEN=root
   vault secrets enable -path=secret kv-v2
   vault kv put secret/api_keys/binance api_key="your_key" secret_key="your_secret"
   # ... add other secrets
   ```

2. **Database**:
   ```bash
   python scripts/database/setup_schema.py
   ```

## Troubleshooting

### Vault Connection Issues
- Make sure Vault container is running: `docker-compose ps vault`
- Check Vault logs: `docker-compose logs vault`
- Verify Vault is accessible: `curl http://localhost:8200/v1/sys/health`

### Database Connection Issues
- Make sure DB container is running: `docker-compose ps db`
- Check DB logs: `docker-compose logs db`
- Verify DB is accessible: `docker exec volexstorm-db psql -U volex -d volextrades -c "SELECT 1;"`

### Agent Health Issues
- Check agent logs: `docker-compose logs <agent-name>`
- Verify agent health: `curl http://localhost:<port>/health`
- Make sure Vault and DB are properly initialized first

## Automation

To automatically run initialization when containers restart, you can:

1. Add to your startup script:
   ```bash
   #!/bin/bash
   docker-compose up -d
   sleep 30  # Wait for containers to start
   python scripts/setup/init_system.py
   ```

2. Use Docker's restart policies and health checks (advanced)

## Next Steps

After running the initialization script:

1. Replace sample API keys with real ones
2. Access the WebUI at http://localhost:8005
3. Monitor agent status in the Agent Management interface
4. Configure trading strategies and parameters 