# VolexSwarm System Documentation

## Overview
This document provides comprehensive information about the VolexSwarm system, including Vault structure, service ports, and access patterns.

## System Architecture

### Service Ports & Endpoints
| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| **Vault** | `8200` | Secrets management | `/vault/status` |
| **Database** | `5432` | TimescaleDB | `pg_isready` |
| **Research Agent** | `8001` | Research & analysis | `/health` |
| **Execution Agent** | `8002` | Trading execution | `/health` |
| **Signal Agent** | `8003` | Signal generation | `/health` |
| **Meta Agent** | `8004` | Agent coordination | `/health` |
| **Monitor Agent** | `8011` | System monitoring | `/health` |
| **Risk Agent** | `8009` | Risk management | `/health` |
| **Strategy Agent** | `8010` | Strategy management | `/health` |
| **Optimize Agent** | `8006` | Strategy optimization | `/health` |
| **Compliance Agent** | `8007` | Compliance checking | `/health` |
| **Backtest Agent** | `8008` | Strategy backtesting | `/health` |
| **News Sentiment** | `8024` | News analysis | `/health` |
| **Strategy Discovery** | `8025` | Strategy discovery | `/health` |
| **Realtime Data** | `8026` | Real-time data feeds | `/health` |

### Quick Access URLs
- **Vault UI**: http://localhost:8200
- **Database**: localhost:5432
- **Research Agent**: http://localhost:8001
- **Execution Agent**: http://localhost:8002
- **Signal Agent**: http://localhost:8003
- **Meta Agent**: http://localhost:8004
- **Monitor Agent**: http://localhost:8011
- **Risk Agent**: http://localhost:8009
- **Strategy Agent**: http://localhost:8010

## Vault Structure

### Vault Mount Points
- **Main Secrets Mount**: `secret/` (KV v2)
- **Access**: Root token authentication required

## Secret Paths

### 1. API Keys (`secret/api_keys/`)
**Path**: `secret/api_keys/{exchange_name}`

#### Binance US (`secret/api_keys/binance`)
```json
{
  "api_key": "YOUR_BINANCE_US_API_KEY_HERE",
  "secret_key": "YOUR_BINANCE_US_SECRET_KEY_HERE"
}
```

#### Coinbase (`secret/api_keys/coinbase`)
- Structure: TBD (check if exists)

#### Kraken (`secret/api_keys/kraken`)
- Structure: TBD (check if exists)

### 2. OpenAI Configuration (`secret/openai/`)
**Path**: `secret/openai/api_key`

```json
{
  "api_key": "sk-...YOUR_OPENAI_API_KEY_HERE..."
}
```

### 3. Agent Configurations (`secret/agents/`)
**Path**: `secret/agents/{agent_name}`

Available agents:
- `backtest`
- `execution`
- `monitor`
- `news_sentiment`
- `optimize`
- `research`
- `signal`
- `strategy`

### 4. Database Configurations (`secret/database/`, `secret/databases/`)
**Paths**: 
- `secret/database/`
- `secret/databases/`

### 5. Test Data (`secret/test/`, `secret/final_test`, `secret/test_persistence_production`)
**Paths**: Various test-related configurations

## Code Access Patterns

### Correct Vault Access Patterns

#### For Exchange API Keys:
```python
# ✅ CORRECT: Access via api_keys/{exchange}
binance_creds = vault_client.get_secret("api_keys/binance")
api_key = binance_creds.get("api_key")
secret_key = binance_creds.get("secret_key")  # Note: "secret_key" not "secret"
```

#### For OpenAI:
```python
# ✅ CORRECT: Access via openai/api_key
openai_config = vault_client.get_secret("openai/api_key")
api_key = openai_config.get("api_key")
```

#### For Agent Configs:
```python
# ✅ CORRECT: Access via agents/{agent_name}
agent_config = vault_client.get_secret("agents/execution")
```

### ❌ INCORRECT Patterns (Don't Use):
```python
# ❌ WRONG: These paths don't exist
vault_client.get_secret("binance/api_key")      # Should be "api_keys/binance"
vault_client.get_secret("binance/secret")       # Should be "api_keys/binance"
vault_client.get_secret("binanceus")            # Should be "api_keys/binance"
vault_client.get_secret("api_keys")             # Should be "api_keys/binance"
```

## Key Naming Conventions

### Exchange API Keys:
- **Path**: `secret/api_keys/{exchange_name}`
- **Keys**: 
  - `api_key` - The API key string
  - `secret_key` - The secret key string (NOT `secret`)

### OpenAI:
- **Path**: `secret/openai/api_key`
- **Keys**:
  - `api_key` - The OpenAI API key string

### Agents:
- **Path**: `secret/agents/{agent_name}`
- **Keys**: Varies by agent

## Troubleshooting

### Common Issues:
1. **"No API keys found"**: Check if using correct path (`api_keys/binance` not `binance`)
2. **"Key not found"**: Verify the key name (`secret_key` not `secret`)
3. **"Vault connection failed"**: Check Vault container health and authentication

### Debugging Commands:
```bash
# List all secrets
docker exec -it volexswarm-vault vault kv list secret/

# Get specific secret
docker exec -it volexswarm-vault vault kv get secret/api_keys/binance

# Check Vault health
docker exec -it volexswarm-vault vault status
```

## Service Testing & Validation

### Health Check Commands
```bash
# Check all services health
curl -s http://localhost:8001/health  # Research Agent
curl -s http://localhost:8002/health  # Execution Agent
curl -s http://localhost:8003/health  # Signal Agent
curl -s http://localhost:8004/health  # Meta Agent
curl -s http://localhost:8009/health  # Risk Agent
curl -s http://localhost:8010/health  # Strategy Agent
```

### Portfolio Data Testing
```bash
# Get real portfolio data from Execution Agent
curl -s http://localhost:8002/api/execution/portfolio | jq .

# Get positions
curl -s http://localhost:8002/api/execution/positions | jq .

# Get P&L
curl -s http://localhost:8002/api/execution/pnl | jq .
```

### Docker Management
```bash
# View all running services
docker ps

# View service logs
docker-compose logs execution
docker-compose logs meta

# Rebuild specific service (no-cache)
docker-compose build --no-cache execution

# Restart specific service
docker-compose restart execution

# Complete service refresh
docker-compose rm -s -f execution && docker-compose up -d execution
```

## Security Notes
- All secrets are stored encrypted in Vault
- Access requires root token authentication
- Secrets are versioned and can be rotated
- Never log or expose secret values in code

## Current System Status

### ✅ Completed Features
- **Real Data Integration**: 100% real Binance US portfolio data
- **Vault Integration**: Complete API key management working
- **Portfolio Calculation**: Accurate portfolio value calculations
- **Service Documentation**: Complete port mapping and access patterns
- **No Simulated Data**: All endpoints return real-time data

### 🔧 Current Working Endpoints
- **Execution Agent** (`:8002`): Real portfolio data, positions, P&L
- **Vault** (`:8200`): Secure credential management
- **Database** (`:5432`): TimescaleDB operational
- **All Agent Health Checks**: Available and responding

### 🚀 Next Phase Priorities
1. **Meta Agent Coordination**: Test agent orchestration with real data
2. **UI Integration**: Display real portfolio data in the dashboard
3. **Risk Management**: Integrate real portfolio data with risk calculations
4. **Strategy Execution**: Test trading strategies with live data

## Last Updated
- **Date**: 2025-08-16
- **Status**: Complete system documentation with real data integration
- **Next Review**: When new services are added or data flows change
