# VolexSwarm

A modular autonomous AI system for crypto trading using a team of Python agents, each running in Docker containers with secure credential management via HashiCorp Vault.

## Architecture

VolexSwarm consists of multiple specialized agents that work together to execute crypto trading strategies:

- **Research Agent**: Market research, data collection, and analysis
- **Signal Agent**: Technical analysis and signal generation
- **Strategy Agent**: Strategy development and backtesting
- **Execution Agent**: Order execution and trade management
- **Risk Agent**: Risk assessment and position sizing
- **Monitor Agent**: System monitoring and alerting
- **Optimize Agent**: Strategy optimization and parameter tuning
- **Meta Agent**: Coordination and decision making
- **Compliance Agent**: Regulatory compliance and reporting
- **Backtest Agent**: Historical strategy testing

## Security

All API keys, credentials, and sensitive configuration are stored securely in HashiCorp Vault using KV v2 secrets engine under the `secret/` path. The system uses environment variables `VAULT_ADDR` and `VAULT_TOKEN` for authentication.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- HashiCorp Vault (included in docker-compose.yml)

### 1. Start the Infrastructure

```bash
# Start Vault and database
docker-compose up -d vault db
```

### 2. Initialize Vault

```bash
# Access Vault CLI
docker exec -it volexswarm-vault vault login root

# Enable KV v2 secrets engine
docker exec -it volexswarm-vault vault secrets enable -path=secret kv-v2

# Store your first secret (example: Binance API credentials)
docker exec -it volexswarm-vault vault kv put secret/api_keys/binance \
  api_key="your_binance_api_key" \
  secret_key="your_binance_secret_key"

# Store agent configuration
docker exec -it volexswarm-vault vault kv put secret/agents/research \
  data_sources="['binance', 'coinbase']" \
  update_interval="300" \
  max_requests_per_minute="60"
```

### 3. Set Environment Variables

Create a `.env` file in the root directory:

```env
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=root
```

### 4. Start an Agent

```bash
# Start the research agent
docker-compose up research
```

## Vault Integration

### Secret Structure

The Vault integration uses the following secret structure:

```
secret/
├── api_keys/
│   ├── binance/
│   │   ├── api_key
│   │   └── secret_key
│   ├── coinbase/
│   │   ├── api_key
│   │   └── secret_key
│   └── ...
├── databases/
│   └── default/
│       ├── host
│       ├── port
│       ├── database
│       ├── username
│       └── password
└── agents/
    ├── research/
    ├── signal/
    ├── strategy/
    └── ...
```

### Using the Vault Client

All agents can use the Vault client from `common/vault.py`:

```python
from common.vault import get_api_key, get_exchange_credentials, get_agent_config

# Get API key for a specific exchange
api_key = get_api_key("binance", "api_key")

# Get all credentials for an exchange
credentials = get_exchange_credentials("binance")

# Get agent configuration
config = get_agent_config("research")
```

### Available Functions

- `get_secret(path, mount_point='secret')`: Get any secret by path
- `get_api_key(exchange, key_type='api_key')`: Get specific API key
- `get_exchange_credentials(exchange)`: Get all exchange credentials
- `get_database_credentials(db_name='default')`: Get database credentials
- `get_agent_config(agent_name)`: Get agent configuration
- `list_secrets(path='')`: List available secrets
- `health_check()`: Check Vault connection status

## Agent Development

### Creating a New Agent

1. Create a new directory in `agents/`
2. Create `main.py` with FastAPI app
3. Import and use the Vault client
4. Create a Dockerfile in `docker/`
5. Add service to `docker-compose.yml`

### Example Agent Structure

```python
from fastapi import FastAPI
from common.vault import get_vault_client, get_agent_config

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # Initialize Vault client
    vault_client = get_vault_client()
    
    # Load configuration
    config = get_agent_config("your_agent_name")
    
    # Initialize your agent logic here
```

## API Endpoints

Each agent exposes REST API endpoints:

- `GET /`: Health check
- `GET /health`: Detailed health status
- `GET /config`: Agent configuration
- `GET /exchanges`: Available exchanges
- `GET /exchanges/{exchange}/status`: Exchange connection status

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root

# Run an agent locally
cd agents/research
python main.py
```

### Testing

```bash
# Test Vault connection
python -c "from common.vault import get_vault_client; print(get_vault_client().health_check())"
```

## Configuration

### Environment Variables

- `VAULT_ADDR`: Vault server address (default: http://localhost:8200)
- `VAULT_TOKEN`: Vault authentication token (required)

### Agent Configuration

Store agent-specific configuration in Vault:

```bash
# Example: Configure research agent
docker exec -it volexswarm-vault vault kv put secret/agents/research \
  data_sources="['binance', 'coinbase']" \
  update_interval="300" \
  max_requests_per_minute="60" \
  enabled_pairs="['BTC/USDT', 'ETH/USDT']"
```

## Monitoring

### Health Checks

Each agent provides health check endpoints:

```bash
# Check agent health
curl http://localhost:8001/health

# Check Vault connection
curl http://localhost:8001/vault/secrets
```

### Logs

Agent logs are stored in `logs/agents/` directory.

## Security Best Practices

1. **Never commit secrets**: All credentials are stored in Vault
2. **Use environment variables**: Configure Vault connection via env vars
3. **Rotate tokens regularly**: Update Vault tokens periodically
4. **Limit permissions**: Use least-privilege access for Vault tokens
5. **Monitor access**: Log and monitor Vault access patterns

## Troubleshooting

### Common Issues

1. **Vault connection failed**: Check `VAULT_ADDR` and `VAULT_TOKEN`
2. **Secret not found**: Verify secret path and Vault permissions
3. **Agent startup failure**: Check Vault health and agent configuration

### Debug Commands

```bash
# Check Vault status
docker exec -it volexswarm-vault vault status

# List secrets
docker exec -it volexswarm-vault vault kv list secret/

# Test secret retrieval
docker exec -it volexswarm-vault vault kv get secret/api_keys/binance
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here]
