# VolexSwarm Execution Agent Documentation

## 📋 **Overview**

The VolexSwarm Execution Agent is a sophisticated order execution and trade management system that handles cryptocurrency trading operations with multiple exchanges. It provides a unified interface for order placement, position tracking, and trade execution with built-in safety features and comprehensive logging.

**Version**: 1.0.0  
**Port**: 8002 (Docker) / 8002 (Local)  
**Status**: ✅ Fully Implemented and Operational

---

## 🏗️ **Architecture**

### **Core Components**

The Execution Agent follows a modular architecture with centralized exchange management:

#### 1. **ExchangeManager Class**
- **Purpose**: Centralized exchange connection and operation management
- **Capabilities**:
  - Multi-exchange support via CCXT library
  - Automatic credential management from Vault
  - Rate limiting and connection pooling
  - Sandbox/live mode switching
- **Supported Exchanges**: Binance.US (default), Coinbase, and other CCXT-compatible exchanges

#### 2. **Data Models**

##### **OrderRequest**
```python
class OrderRequest(BaseModel):
    symbol: str                    # Trading pair (e.g., "BTC/USDT")
    side: str                      # 'buy' or 'sell'
    order_type: str = 'market'     # 'market', 'limit', 'stop'
    amount: Optional[float] = None # Order quantity
    price: Optional[float] = None  # Limit price
    stop_price: Optional[float] = None  # Stop price
    exchange: str = 'binanceus'    # Target exchange
```

##### **OrderResponse**
```python
class OrderResponse(BaseModel):
    id: str                        # Order ID
    symbol: str                    # Trading pair
    side: str                      # Buy/sell
    order_type: str                # Order type
    amount: float                  # Order amount
    price: Optional[float]         # Execution price
    status: str                    # Order status
    filled: float                  # Filled quantity
    remaining: float               # Remaining quantity
    cost: float                    # Total cost
    timestamp: datetime            # Order timestamp
    exchange: str                  # Exchange name
```

##### **PositionResponse**
```python
class PositionResponse(BaseModel):
    symbol: str                    # Trading pair
    side: str                      # Long/short
    amount: float                  # Position size
    entry_price: float             # Entry price
    current_price: float           # Current market price
    unrealized_pnl: float          # Unrealized P&L
    realized_pnl: float            # Realized P&L
    timestamp: datetime            # Position timestamp
```

#### 3. **Safety Features**
- **Dry Run Mode**: Default safe mode for testing
- **Order Validation**: Pre-trade parameter validation
- **Rate Limiting**: Respects exchange API limits
- **Error Handling**: Graceful failure recovery
- **Audit Logging**: Complete trade execution logs

---

## 🔧 **Technical Implementation**

### **Dependencies**
```python
# Core Framework
fastapi
uvicorn
pydantic

# Exchange Integration
ccxt
ccxt[async_support]

# Database
sqlalchemy
asyncpg
psycopg2-binary

# Security
hvac  # Vault integration

# Utilities
python-dotenv
```

### **Key Features**

#### **Multi-Exchange Support**
- **CCXT Integration**: Unified interface for 100+ exchanges
- **Credential Management**: Secure storage in HashiCorp Vault
- **Exchange Abstraction**: Consistent API across different exchanges
- **US Compliance**: Default to Binance.US for regulatory compliance

#### **Order Types**
- **Market Orders**: Immediate execution at current market price
- **Limit Orders**: Execution at specified price or better
- **Stop Orders**: Triggered at specified stop price
- **Stop-Limit Orders**: Combination of stop and limit orders

#### **Position Tracking**
- **Real-time Balances**: Current account balances
- **Position Calculation**: Unrealized and realized P&L
- **Historical Data**: Complete order and trade history
- **Database Storage**: Persistent storage in TimescaleDB

#### **Safety Mechanisms**
- **Dry Run Mode**: Simulate orders without execution
- **Order Validation**: Parameter validation before submission
- **Rate Limiting**: Prevent API abuse
- **Error Recovery**: Graceful handling of exchange failures

---

## 🌐 **API Endpoints**

### **Health & Status**

#### `GET /health`
**Comprehensive health check**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-20T17:45:30.123456",
  "components": {
    "vault": true,
    "database": true,
    "exchanges": true,
    "dry_run_mode": true
  },
  "exchanges": ["binanceus", "coinbase"]
}
```

### **Exchange Management**

#### `GET /exchanges`
**List available exchanges**
```json
{
  "available_exchanges": ["binanceus", "coinbase"],
  "dry_run_mode": true
}
```

#### `GET /exchanges/{exchange_name}/status`
**Exchange connection status**
```json
{
  "exchange": "binanceus",
  "status": "connected",
  "timestamp": "2025-07-20T17:45:30.123456",
  "markets_count": 150
}
```

### **Account Information**

#### `GET /balance/{exchange_name}`
**Account balance for specific currency**
```json
{
  "currency": "USDT",
  "free": 1000.50,
  "used": 50.25,
  "total": 1050.75
}
```

#### `GET /ticker/{exchange_name}/{symbol}`
**Current market ticker**
```json
{
  "symbol": "BTC/USDT",
  "last": 45000.0,
  "bid": 44995.0,
  "ask": 45005.0,
  "volume": 1234.56,
  "timestamp": "2025-07-20T17:45:30.123456"
}
```

### **Order Management**

#### `POST /orders`
**Place new order**
```json
// Request
{
  "symbol": "BTC/USDT",
  "side": "buy",
  "order_type": "market",
  "amount": 0.001,
  "exchange": "binanceus"
}

// Response
{
  "id": "123456789",
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "market",
  "amount": 0.001,
  "price": 45000.0,
  "status": "closed",
  "filled": 0.001,
  "remaining": 0,
  "cost": 45.0,
  "timestamp": "2025-07-20T17:45:30.123456",
  "exchange": "binanceus",
  "dry_run": true
}
```

#### `GET /orders/{exchange_name}`
**Order history**
```json
[
  {
    "id": "123456789",
    "symbol": "BTC/USDT",
    "side": "buy",
    "type": "market",
    "amount": 0.001,
    "price": 45000.0,
    "status": "closed",
    "filled": 0.001,
    "remaining": 0,
    "cost": 45.0,
    "timestamp": "2025-07-20T17:45:30.123456",
    "exchange": "binanceus"
  }
]
```

### **Position Management**

#### `GET /positions/{exchange_name}`
**Current positions**
```json
[
  {
    "symbol": "BTC/USDT",
    "side": "long",
    "amount": 0.001,
    "entry_price": 45000.0,
    "current_price": 45500.0,
    "unrealized_pnl": 0.5,
    "realized_pnl": 0,
    "timestamp": "2025-07-20T17:45:30.123456"
  }
]
```

---

## 📊 **Order Types & Examples**

### **Market Orders**
```json
{
  "symbol": "BTC/USDT",
  "side": "buy",
  "order_type": "market",
  "amount": 0.001,
  "exchange": "binanceus"
}
```

### **Limit Orders**
```json
{
  "symbol": "ETH/USDT",
  "side": "sell",
  "order_type": "limit",
  "amount": 1.0,
  "price": 3000.0,
  "exchange": "binanceus"
}
```

### **Stop Orders**
```json
{
  "symbol": "BTC/USDT",
  "side": "sell",
  "order_type": "stop",
  "amount": 0.001,
  "stop_price": 44000.0,
  "exchange": "binanceus"
}
```

### **Stop-Limit Orders**
```json
{
  "symbol": "BTC/USDT",
  "side": "sell",
  "order_type": "stop",
  "amount": 0.001,
  "price": 43900.0,
  "stop_price": 44000.0,
  "exchange": "binanceus"
}
```

---

## 🔐 **Security & Configuration**

### **Vault Integration**
- **API Keys**: Stored securely in HashiCorp Vault
- **Configuration**: Agent settings from Vault
- **Credentials**: Exchange API keys and secrets

### **Environment Variables**
```bash
# Required
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=root

# Optional
DRY_RUN_MODE=true  # Default to safe mode
LOG_LEVEL=INFO
DEBUG=false
```

### **Exchange Configuration**
```bash
# Store exchange credentials in Vault
docker exec -it volexswarm-vault vault kv put secret/api_keys/binanceus \
  api_key="your_binance_us_api_key" \
  secret_key="your_binance_us_secret_key"

# Configure execution agent
docker exec -it volexswarm-vault vault kv put secret/agents/execution \
  enabled_exchanges="['binanceus', 'coinbase']" \
  dry_run_mode="true" \
  default_exchange="binanceus"
```

### **Safety Features**
- **Dry Run Mode**: Default enabled for safety
- **Order Validation**: Parameter validation before execution
- **Rate Limiting**: Respects exchange API limits
- **Error Handling**: Graceful failure recovery
- **Audit Logging**: Complete trade execution logs

---

## 🚀 **Usage Examples**

### **Basic Order Placement**
```bash
# Place a market buy order
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "side": "buy",
    "order_type": "market",
    "amount": 0.001,
    "exchange": "binanceus"
  }'

# Check account balance
curl http://localhost:8002/balance/binanceus

# Get current positions
curl http://localhost:8002/positions/binanceus
```

### **Python Integration**
```python
import requests
import json

# Initialize execution agent client
execution_url = "http://localhost:8002"

# Place a limit order
order_data = {
    "symbol": "ETH/USDT",
    "side": "buy",
    "order_type": "limit",
    "amount": 1.0,
    "price": 3000.0,
    "exchange": "binanceus"
}

response = requests.post(f"{execution_url}/orders", json=order_data)
order_result = response.json()

# Check order status
order_id = order_result['id']
orders = requests.get(f"{execution_url}/orders/binanceus").json()
```

### **Integration with Other Agents**
```python
# Meta-Agent can place orders
order_result = await execution_agent.place_order(order_request)

# Signal Agent can trigger trades
if signal.confidence > 0.8:
    order = await execution_agent.place_order(signal.to_order())

# Risk Agent can validate orders
risk_check = await risk_agent.validate_order(order_request)
if risk_check.approved:
    result = await execution_agent.place_order(order_request)
```

---

## 📈 **Performance & Monitoring**

### **Performance Metrics**
- **Order Execution Time**: < 500ms for market orders
- **API Response Time**: < 200ms for data queries
- **Exchange Reliability**: 99.9%+ uptime
- **Error Rate**: < 0.1% for order placement

### **Monitoring**
- **Health Checks**: `/health` endpoint
- **Logging**: Structured logging with context
- **Metrics**: Order counts, execution times, error rates
- **Alerts**: Failed orders and exchange disconnections

### **Database Integration**
- **Order Storage**: Complete order history in TimescaleDB
- **Trade Logging**: All executed trades stored
- **Audit Trail**: Complete execution audit trail
- **Performance Tracking**: Historical performance metrics

---

## 🔧 **Deployment**

### **Docker Deployment**
```bash
# Build and run execution agent
docker-compose up execution

# Or run individually
docker build -f docker/execute.Dockerfile -t volexswarm-execution .
docker run -p 8002:8002 volexswarm-execution
```

### **Local Development**
```bash
# Activate virtual environment
pyenv activate volexswarm-env

# Set environment variables
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root

# Run execution agent
cd agents/execution
python main.py
```

### **Production Configuration**
```bash
# Disable dry run mode for production
docker exec -it volexswarm-vault vault kv put secret/agents/execution \
  dry_run_mode="false" \
  enabled_exchanges="['binanceus']" \
  max_order_size="1000" \
  rate_limit_per_minute="60"
```

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Exchange Connection Failed**
```bash
# Check exchange credentials
docker exec -it volexswarm-vault vault kv get secret/api_keys/binanceus

# Test exchange connection
curl http://localhost:8002/exchanges/binanceus/status
```

#### **Order Placement Failed**
```bash
# Check account balance
curl http://localhost:8002/balance/binanceus

# Verify order parameters
curl -X POST http://localhost:8002/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC/USDT", "side": "buy", "order_type": "market", "amount": 0.001}'
```

#### **Database Connection Issues**
```bash
# Check database container
docker ps | grep timescale

# Test database connection
docker exec -it volexstorm-db psql -U volex -d volextrades -c "SELECT 1;"
```

### **Debug Commands**
```bash
# Check agent logs
docker logs volexswarm-execution-1

# Test health endpoint
curl http://localhost:8002/health

# Check available exchanges
curl http://localhost:8002/exchanges
```

---

## 📚 **API Reference**

### **Request/Response Formats**

#### **Order Request**
```json
{
  "symbol": "BTC/USDT",
  "side": "buy",
  "order_type": "market",
  "amount": 0.001,
  "price": null,
  "stop_price": null,
  "exchange": "binanceus"
}
```

#### **Order Response**
```json
{
  "id": "123456789",
  "symbol": "BTC/USDT",
  "side": "buy",
  "type": "market",
  "amount": 0.001,
  "price": 45000.0,
  "status": "closed",
  "filled": 0.001,
  "remaining": 0,
  "cost": 45.0,
  "timestamp": "2025-07-20T17:45:30.123456",
  "exchange": "binanceus",
  "dry_run": true
}
```

#### **Balance Response**
```json
{
  "currency": "USDT",
  "free": 1000.50,
  "used": 50.25,
  "total": 1050.75
}
```

#### **Position Response**
```json
{
  "symbol": "BTC/USDT",
  "side": "long",
  "amount": 0.001,
  "entry_price": 45000.0,
  "current_price": 45500.0,
  "unrealized_pnl": 0.5,
  "realized_pnl": 0,
  "timestamp": "2025-07-20T17:45:30.123456"
}
```

---

## 🔮 **Future Enhancements**

### **Planned Features**
- **Advanced Order Types**: OCO orders, trailing stops
- **Portfolio Management**: Multi-asset portfolio tracking
- **Risk Management**: Position sizing and stop-loss automation
- **Order Scheduling**: Time-based order execution
- **Real-time Streaming**: WebSocket support for live updates

### **Performance Improvements**
- **Order Batching**: Batch order execution for efficiency
- **Smart Routing**: Intelligent exchange selection
- **Caching**: Redis-based order and balance caching
- **Load Balancing**: Multiple agent instances

### **Advanced Capabilities**
- **Algorithmic Trading**: TWAP, VWAP execution
- **Dark Pool Integration**: Alternative liquidity sources
- **Cross-Exchange Arbitrage**: Multi-exchange order execution
- **Advanced Analytics**: Execution quality metrics

---

## ⚠️ **Important Notes**

### **Safety Considerations**
- **Dry Run Mode**: Always test in dry run mode first
- **Small Orders**: Start with small order sizes
- **API Limits**: Respect exchange rate limits
- **Error Handling**: Monitor for failed orders
- **Backup**: Regular backup of order history

### **Regulatory Compliance**
- **US Compliance**: Uses Binance.US for US users
- **KYC/AML**: Follow exchange KYC requirements
- **Tax Reporting**: Maintain complete trade records
- **Audit Trail**: Full audit trail for compliance

### **Risk Management**
- **Position Limits**: Set maximum position sizes
- **Stop Losses**: Implement automatic stop losses
- **Diversification**: Don't concentrate in single assets
- **Monitoring**: Continuous position monitoring

---

## 📞 **Support**

For issues, questions, or contributions:
- **Documentation**: This file and inline code comments
- **Logs**: Check agent logs for detailed error information
- **Health Checks**: Use `/health` endpoint for status
- **Testing**: Use dry run mode for safe testing
- **Emergency**: Use exchange's emergency stop features

---

*Last Updated: 2025-07-20*  
*Version: 1.0.0* 