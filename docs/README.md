# VolexSwarm Documentation

## 🚀 **What is VolexSwarm?**

VolexSwarm is a sophisticated **multi-agent AI trading system** built on an agentic AI framework that transforms traditional FastAPI services into intelligent, autonomous AutoGen agents. The system operates as a distributed, containerized architecture with centralized coordination through a Meta Agent.

## 🏗️ **System Architecture**

### **Core Components**
- **Vault** (Port 8200) - Secure credential and secret management
- **TimescaleDB** (Port 5432) - High-performance time-series database
- **Meta Agent** (Port 8004) - System coordination and orchestration
- **15 Trading Agents** - Research, Strategy, Signal, Risk, Execution, etc.

### **Agent Overview**
```
┌─────────────────────────────────────────────────────────────────┐
│                        TRADING AGENTS                          │
├─────────────────────────────────────────────────────────────────┤
│ Research │ Strategy │ Signal │ Risk │ Execution │ Compliance   │
│ (8001)   │ (8011)  │ (8003) │(8009)│  (8002)  │   (8010)     │
├─────────────────────────────────────────────────────────────────┤
│ Monitor  │ Optimize│Backtest│ News │ Strategy │ Real-Time    │
│ (8008)   │ (8007) │ (8006) │(8024)│Discovery │   Data       │
│          │         │        │      │ (8025)   │  (8026)      │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start**

### **1. Prerequisites**
- Docker and Docker Compose
- Python 3.11+ with pyenv
- Virtual environment: `volexswarm-env`

### **2. Clone and Setup**
```bash
git clone <repository>
cd volexswarm
pyenv activate volexswarm-env
```

### **3. Deploy System**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### **4. Access Points**
- **Meta Agent API**: http://localhost:8004
- **Meta Agent WebSocket**: ws://localhost:8005
- **Vault**: http://localhost:8200
- **Database**: localhost:5432

## 📚 **Documentation Structure**

### **Essential Guides**
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture and design
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Step-by-step deployment instructions
- **[API_REFERENCE.md](API_REFERENCE.md)** - All agent API endpoints
- **[DATABASE.md](DATABASE.md)** - Database schema and management

### **Archived Documentation**
- **[archive/](archive/)** - Historical phase completion summaries

## 🔧 **Key Features**

### **AI-Powered Trading**
- **AutoGen Framework**: Multi-agent AI coordination
- **Intelligent Decision Making**: Autonomous trading decisions
- **Strategy Discovery**: AI-powered strategy optimization
- **Real-Time Processing**: Live market data and signal generation

### **Production Ready**
- **Security**: Vault-based credential management
- **Scalability**: Containerized microservices architecture
- **Monitoring**: Comprehensive agent health monitoring
- **Reliability**: Fault tolerance and self-healing capabilities

## 🎯 **Use Cases**

### **Trading Operations**
- Real-time market analysis and signal generation
- Automated trade execution and risk management
- Portfolio optimization and strategy backtesting
- News sentiment analysis and market intelligence

### **System Management**
- Agent coordination and task orchestration
- Performance monitoring and optimization
- Compliance monitoring and audit trails
- System health monitoring and alerts

## 🚨 **Getting Help**

### **Health Checks**
```bash
# Check all agents
curl http://localhost:8004/api/agents/health

# Check specific agent
curl http://localhost:8001/health
```

### **Common Issues**
- **Port conflicts**: Ensure ports 8001-8026 are available
- **Database connection**: Check TimescaleDB container status
- **Vault access**: Verify Vault token and permissions

## 📈 **System Status**

- **✅ All 15 Trading Agents**: Operational and healthy
- **✅ Infrastructure**: Vault, TimescaleDB, Docker
- **✅ Security**: Production-ready credential management
- **✅ Performance**: Real-time processing capabilities

---

**Last Updated**: 2025-01-26  
**Version**: 7.1 (Simplified Documentation Edition)  
**Status**: Production Ready - All Systems Operational 