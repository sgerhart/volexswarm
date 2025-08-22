# VolexSwarm API Reference

## 🌐 **API Overview**

VolexSwarm provides a comprehensive API ecosystem through its distributed agent architecture. Each agent exposes specific endpoints for its functionality, while the Meta Agent serves as the central API gateway for system-wide operations.

## 🔑 **Authentication**

All API endpoints require authentication via JWT tokens obtained through the Meta Agent's security endpoints.

```bash
# Get JWT token
curl -X POST http://localhost:8004/security/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  http://localhost:8004/api/status
```

## 📡 **Meta Agent API (Port 8004)**

The Meta Agent serves as the central coordination point and provides system-wide APIs.

### **System Status**
```http
GET /health
GET /api/status
GET /api/agents
GET /api/agents/health
```

### **Task Management**
```http
POST /api/task
GET /api/tasks
GET /api/task/{task_id}
POST /api/task/autogen
```

### **WebSocket Statistics**
```http
GET /websocket/stats
POST /websocket/reset
```

### **WebSocket Connection**
```http
WS /ws
```

## 🔬 **Research Agent API (Port 8001)**

Market research and data collection capabilities.

### **Health & Status**
```http
GET /health
GET /
```

### **Market Research**
```http
POST /api/research/market-analysis
POST /api/research/symbol-analysis
GET /api/research/historical-data
```

## 📊 **Signal Agent API (Port 8003)**

Technical analysis and trading signal generation.

### **Health & Status**
```http
GET /health
GET /
```

### **Signal Generation**
```http
POST /generate-signal
GET /signals/{symbol}
GET /signals
GET /performance
GET /analyze/{symbol}
GET /status
```

## ⚡ **Execution Agent API (Port 8002)**

Trade execution and order management.

### **Health & Status**
```http
GET /health
GET /
```

### **Trade Execution**
```http
POST /api/execution/execute-trade
POST /api/execution/place-order
GET /api/execution/orders
GET /api/execution/trades
```

## 🛡️ **Risk Agent API (Port 8009)**

Risk assessment and position management.

### **Health & Status**
```http
GET /health
```

### **Risk Management**
```http
POST /api/risk/assess
POST /api/risk/position-size
POST /api/risk/stop-loss
POST /api/risk/portfolio
POST /api/risk/circuit-breaker
POST /api/risk/drawdown-protection
GET /api/risk/status
```

## 🎯 **Strategy Agent API (Port 8011)**

Strategy management and optimization.

### **Health & Status**
```http
GET /health
GET /
```

### **Strategy Management**
```http
POST /api/strategy/create
GET /api/strategy/list
POST /api/strategy/backtest
POST /api/strategy/optimize
```

## 📈 **Backtest Agent API (Port 8006)**

Strategy backtesting and validation.

### **Health & Status**
```http
GET /health
GET /
```

### **Backtesting**
```http
POST /api/backtest/run
GET /api/backtest/results
POST /api/backtest/optimize
```

## 🔧 **Optimize Agent API (Port 8007)**

Strategy parameter optimization.

### **Health & Status**
```http
GET /health
GET /
```

### **Optimization**
```http
POST /api/optimize/strategy
POST /api/optimize/parameters
GET /api/optimize/status
```

## 📰 **News Sentiment Agent API (Port 8024)**

News analysis and sentiment scoring.

### **Health & Status**
```http
GET /health
GET /
```

### **News Analysis**
```http
POST /api/news/analyze
GET /api/news/sentiment
POST /api/news/scan
```

## 🔍 **Strategy Discovery Agent API (Port 8025)**

AI-powered strategy discovery and testing.

### **Health & Status**
```http
GET /health
```

### **Strategy Discovery**
```http
POST /discover_strategies
POST /create_sandbox_test
POST /run_sandbox_test
POST /analyze_correlations
POST /explain/strategy_results
POST /explain/market_conditions
POST /explain/performance_metrics
POST /explain/user_summary
```

### **Strategy Management**
```http
POST /strategy/evaluate_promotion
POST /strategy/promote
POST /strategy/lifecycle
POST /strategy/monitor
POST /strategy/deactivate
```

### **Credential Management**
```http
POST /credentials/manage
GET /credentials/list
```

## 📡 **Real-Time Data Agent API (Port 8026)**

Live market data streaming and management.

### **Health & Status**
```http
GET /health
```

### **Data Management**
```http
POST /connect
POST /subscribe
POST /data
GET /quality
GET /connections
GET /connections/status
POST /disconnect
GET /summary
```

## 📊 **Monitor Agent API (Port 8008)**

System monitoring and health checks.

### **Health & Status**
```http
GET /health
GET /
```

### **Monitoring**
```http
GET /api/monitor/status
GET /api/monitor/metrics
GET /api/monitor/alerts
```

## ✅ **Compliance Agent API (Port 8010)**

Regulatory compliance and audit.

### **Health & Status**
```http
GET /health
GET /
```

### **Compliance**
```http
POST /api/compliance/check
GET /api/compliance/status
POST /api/compliance/audit
```

## 🔌 **WebSocket Endpoints**

### **Meta Agent WebSocket (Port 8005)**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8005');

// Subscribe to updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channel: 'agent_status_update'
}));

// Listen for updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## 📋 **Common Response Format**

All APIs return responses in a consistent format:

```json
{
  "status": "success|error",
  "data": { ... },
  "message": "Optional message",
  "timestamp": "2025-01-26T10:00:00Z"
}
```

## 🚨 **Error Handling**

### **HTTP Status Codes**
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

### **Error Response Format**
```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  },
  "timestamp": "2025-01-26T10:00:00Z"
}
```

## 📊 **Rate Limiting**

- **Default Limit**: 100 requests per minute per IP
- **Burst Limit**: 200 requests per minute per IP
- **Headers**: Rate limit information included in response headers

## 🔒 **Security Headers**

All API responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000`

## 📚 **API Testing**

### **Using curl**
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test with authentication
curl -H "Authorization: Bearer <JWT_TOKEN>" \
  http://localhost:8004/api/agents
```

### **Using Postman**
1. Import the collection
2. Set base URL to `http://localhost:8004`
3. Set Authorization header with JWT token
4. Test endpoints

## 🔍 **API Discovery**

### **OpenAPI Documentation**
- **Meta Agent**: http://localhost:8004/docs
- **Individual Agents**: http://localhost:PORT/docs (where PORT is the agent's port)

### **Health Check Endpoints**
All agents provide health check endpoints:
- `GET /health` - Agent health status
- `GET /` - Basic agent information

---

**Last Updated**: 2025-01-26  
**Version**: 7.1 (Consolidated API Reference Edition)
