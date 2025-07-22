# Monitor Agent Documentation

## 📊 **Monitor Agent - System Monitoring and Alerting**

The Monitor Agent is responsible for comprehensive system monitoring, performance tracking, anomaly detection, and alerting. It provides real-time visibility into the health and performance of all VolexSwarm agents, system resources, and trading operations. The agent continuously monitors system metrics, agent health, and trading performance to ensure optimal system operation.

---

## 🎯 **Core Responsibilities**

### **Primary Functions:**
- **System Health Monitoring**: Monitor CPU, memory, disk, and network usage
- **Agent Health Checks**: Continuously monitor all agent statuses and response times
- **Performance Tracking**: Track trading performance metrics and strategy effectiveness
- **Anomaly Detection**: Identify unusual patterns and potential issues
- **Alert Management**: Generate and manage alerts with configurable thresholds
- **Real-time Dashboard**: Provide comprehensive system overview and metrics

---

## 🏗️ **Architecture Overview**

### **Monitoring Framework:**
```
Monitor Agent
├── System Monitor
├── Agent Health Checker
├── Performance Tracker
├── Alert Manager
├── Dashboard Generator
└── Metrics Collector
```

### **Integration Points:**
- **All Agents**: Health monitoring and status checks
- **Database**: Performance data storage and retrieval
- **Vault**: Configuration and credential management
- **Trading System**: Performance metrics collection
- **Alert System**: Notification and alert management

---

## 📈 **Monitoring Components**

### **1. System Metrics Monitoring**

#### **CPU Usage Monitoring:**
```python
def get_system_metrics(self) -> SystemMetrics:
    """Get current system metrics."""
    try:
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100
        
        # Network I/O
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv,
            'packets_sent': network.packets_sent,
            'packets_recv': network.packets_recv
        }
        
        # Active connections
        active_connections = len(psutil.net_connections())
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            active_connections=active_connections,
            database_connections=0
        )
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
        raise
```

#### **Alert Thresholds:**
```json
{
    "cpu_usage": 80.0,
    "memory_usage": 85.0,
    "disk_usage": 90.0,
    "response_time": 5.0,
    "error_rate": 0.1
}
```

### **2. Agent Health Monitoring**

#### **Health Check Configuration:**
```python
async def check_agent_health(self) -> Dict[str, AgentHealth]:
    """Check health of all agents."""
    agents = {
        'research': 'http://research:8000/health',
        'signal': 'http://signal:8003/health',
        'execution': 'http://execution:8002/health',
        'backtest': 'http://backtest:8008/health',
        'strategy': 'http://strategy:8011/health',
        'optimize': 'http://optimize:8006/health',
        'meta': 'http://meta:8004/health'
    }
    
    agent_health = {}
    
    async with aiohttp.ClientSession() as session:
        for agent_name, url in agents.items():
            try:
                start_time = time.time()
                async with session.get(url, timeout=5) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        status = data.get('status', 'unknown')
                        
                        agent_health[agent_name] = AgentHealth(
                            agent_name=agent_name,
                            status=status,
                            last_heartbeat=datetime.now(),
                            response_time=response_time,
                            error_count=0,
                            uptime=0.0
                        )
                    else:
                        agent_health[agent_name] = AgentHealth(
                            agent_name=agent_name,
                            status='unhealthy',
                            last_heartbeat=datetime.now(),
                            response_time=response_time,
                            error_count=1,
                            uptime=0.0
                        )
            except Exception as e:
                logger.warning(f"Failed to check {agent_name} health: {str(e)}")
                agent_health[agent_name] = AgentHealth(
                    agent_name=agent_name,
                    status='unreachable',
                    last_heartbeat=datetime.now(),
                    response_time=5.0,
                    error_count=1,
                    uptime=0.0
                )
    
    return agent_health
```

### **3. Performance Metrics Tracking**

#### **Trading Performance Metrics:**
```python
def get_performance_metrics(self) -> PerformanceMetrics:
    """Get trading performance metrics."""
    try:
        if not db_client:
            return PerformanceMetrics(
                total_trades=0, win_rate=0.0, total_pnl=0.0,
                sharpe_ratio=0.0, max_drawdown=0.0, avg_trade_duration=0.0,
                active_strategies=0, signal_quality=0.0
            )
        
        # Get recent trades
        recent_trades = db_client.query(Trade).filter(
            Trade.timestamp >= datetime.now() - timedelta(days=7)
        ).all()
        
        total_trades = len(recent_trades)
        
        if total_trades == 0:
            return PerformanceMetrics(
                total_trades=0, win_rate=0.0, total_pnl=0.0,
                sharpe_ratio=0.0, max_drawdown=0.0, avg_trade_duration=0.0,
                active_strategies=0, signal_quality=0.0
            )
        
        # Calculate metrics
        winning_trades = [t for t in recent_trades if t.pnl > 0]
        win_rate = len(winning_trades) / total_trades
        total_pnl = sum(t.pnl for t in recent_trades)
        
        # Calculate average trade duration
        if len(recent_trades) >= 2:
            durations = []
            for i in range(1, len(recent_trades)):
                duration = (recent_trades[i-1].timestamp - recent_trades[i].timestamp).total_seconds()
                durations.append(duration)
            avg_trade_duration = np.mean(durations) if durations else 0
        else:
            avg_trade_duration = 0
        
        # Get active strategies
        active_strategies = db_client.query(Strategy).filter(Strategy.enabled == True).count()
        
        return PerformanceMetrics(
            total_trades=total_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            sharpe_ratio=0.0,  # Would need more data for proper calculation
            max_drawdown=0.0,  # Would need equity curve for proper calculation
            avg_trade_duration=avg_trade_duration,
            active_strategies=active_strategies,
            signal_quality=0.75  # Placeholder
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return PerformanceMetrics(
            total_trades=0, win_rate=0.0, total_pnl=0.0,
            sharpe_ratio=0.0, max_drawdown=0.0, avg_trade_duration=0.0,
            active_strategies=0, signal_quality=0.0
        )
```

### **4. Alert Management**

#### **Alert Types:**
```python
class AlertType(Enum):
    """Alert types."""
    SYSTEM_HEALTH = "system_health"
    AGENT_HEALTH = "agent_health"
    TRADING_ANOMALY = "trading_anomaly"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RISK_THRESHOLD = "risk_threshold"
    DATABASE_ISSUE = "database_issue"
    VAULT_ISSUE = "vault_issue"
```

#### **Alert Levels:**
```python
class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
```

#### **Alert Generation:**
```python
def check_thresholds(self, metrics: SystemMetrics, agent_health: Dict[str, AgentHealth]) -> List[Alert]:
    """Check metrics against thresholds and generate alerts."""
    alerts = []
    
    # System metrics thresholds
    if metrics.cpu_usage > self.config.alert_thresholds['cpu_usage']:
        alerts.append(Alert(
            id=str(uuid.uuid4()),
            type=AlertType.SYSTEM_HEALTH,
            level=AlertLevel.WARNING,
            title="High CPU Usage",
            message=f"CPU usage is {metrics.cpu_usage:.1f}% (threshold: {self.config.alert_thresholds['cpu_usage']}%)",
            timestamp=datetime.now(),
            metadata={'cpu_usage': metrics.cpu_usage}
        ))
    
    if metrics.memory_usage > self.config.alert_thresholds['memory_usage']:
        alerts.append(Alert(
            id=str(uuid.uuid4()),
            type=AlertType.SYSTEM_HEALTH,
            level=AlertLevel.WARNING,
            title="High Memory Usage",
            message=f"Memory usage is {metrics.memory_usage:.1f}% (threshold: {self.config.alert_thresholds['memory_usage']}%)",
            timestamp=datetime.now(),
            metadata={'memory_usage': metrics.memory_usage}
        ))
    
    # Agent health thresholds
    for agent_name, health in agent_health.items():
        if health.status != 'healthy':
            alerts.append(Alert(
                id=str(uuid.uuid4()),
                type=AlertType.AGENT_HEALTH,
                level=AlertLevel.ERROR if health.status == 'unreachable' else AlertLevel.WARNING,
                title=f"Agent Health Issue: {agent_name}",
                message=f"Agent {agent_name} is {health.status}",
                timestamp=datetime.now(),
                metadata={'agent_name': agent_name, 'status': health.status}
            ))
        
        if health.response_time > self.config.alert_thresholds['response_time']:
            alerts.append(Alert(
                id=str(uuid.uuid4()),
                type=AlertType.PERFORMANCE_DEGRADATION,
                level=AlertLevel.WARNING,
                title=f"Slow Response: {agent_name}",
                message=f"Agent {agent_name} response time is {health.response_time:.2f}s (threshold: {self.config.alert_thresholds['response_time']}s)",
                timestamp=datetime.now(),
                metadata={'agent_name': agent_name, 'response_time': health.response_time}
            ))
    
    return alerts
```

---

## 🔧 **API Endpoints**

### **1. Health Check**
```http
GET /health
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00",
    "components": {
        "vault": true,
        "database": true,
        "monitoring": true
    }
}
```

### **2. System Metrics**
```http
GET /metrics/system
```

**Response:**
```json
{
    "timestamp": "2024-01-01T00:00:00",
    "cpu_usage": 15.2,
    "memory_usage": 45.8,
    "disk_usage": 67.3,
    "network_io": {
        "bytes_sent": 1024000,
        "bytes_recv": 2048000,
        "packets_sent": 1000,
        "packets_recv": 2000
    },
    "active_connections": 25,
    "database_connections": 5
}
```

### **3. Performance Metrics**
```http
GET /metrics/performance
```

**Response:**
```json
{
    "total_trades": 150,
    "win_rate": 0.65,
    "total_pnl": 1250.50,
    "sharpe_ratio": 1.45,
    "max_drawdown": 0.08,
    "avg_trade_duration": 3600,
    "active_strategies": 3,
    "signal_quality": 0.75,
    "timestamp": "2024-01-01T00:00:00"
}
```

### **4. Agent Health**
```http
GET /agents/health
```

**Response:**
```json
{
    "agents": {
        "research": {
            "status": "healthy",
            "last_heartbeat": "2024-01-01T00:00:00",
            "response_time": 0.15,
            "error_count": 0,
            "uptime": 86400
        },
        "signal": {
            "status": "healthy",
            "last_heartbeat": "2024-01-01T00:00:00",
            "response_time": 0.22,
            "error_count": 0,
            "uptime": 86400
        },
        "execution": {
            "status": "unhealthy",
            "last_heartbeat": "2024-01-01T00:00:00",
            "response_time": 5.5,
            "error_count": 3,
            "uptime": 86400
        }
    },
    "timestamp": "2024-01-01T00:00:00"
}
```

### **5. Alerts**
```http
GET /alerts?level=warning&acknowledged=false&limit=50
```

**Response:**
```json
{
    "alerts": [
        {
            "id": "alert-123",
            "type": "system_health",
            "level": "warning",
            "title": "High CPU Usage",
            "message": "CPU usage is 85.2% (threshold: 80.0%)",
            "timestamp": "2024-01-01T00:00:00",
            "acknowledged": false,
            "metadata": {
                "cpu_usage": 85.2
            }
        }
    ],
    "count": 1,
    "timestamp": "2024-01-01T00:00:00"
}
```

### **6. Acknowledge Alert**
```http
POST /alerts/{alert_id}/acknowledge
```

**Response:**
```json
{
    "alert_id": "alert-123",
    "status": "acknowledged",
    "timestamp": "2024-01-01T00:00:00"
}
```

### **7. Clear Old Alerts**
```http
POST /alerts/clear?days=7
```

**Response:**
```json
{
    "status": "cleared",
    "days": 7,
    "timestamp": "2024-01-01T00:00:00"
}
```

### **8. Dashboard**
```http
GET /dashboard
```

**Response:**
```json
{
    "system": {
        "cpu_usage": 15.2,
        "memory_usage": 45.8,
        "disk_usage": 67.3,
        "active_connections": 25
    },
    "performance": {
        "total_trades": 150,
        "win_rate": 0.65,
        "total_pnl": 1250.50,
        "active_strategies": 3
    },
    "alerts": {
        "recent": [
            {
                "level": "warning",
                "title": "High CPU Usage",
                "timestamp": "2024-01-01T00:00:00"
            }
        ],
        "unacknowledged_count": 2
    },
    "timestamp": "2024-01-01T00:00:00"
}
```

---

## 📊 **Monitoring Metrics**

### **System Metrics:**
- **CPU Usage**: Current CPU utilization percentage
- **Memory Usage**: Current memory utilization percentage
- **Disk Usage**: Current disk space utilization percentage
- **Network I/O**: Bytes sent/received and packet counts
- **Active Connections**: Number of active network connections
- **Database Connections**: Number of active database connections

### **Performance Metrics:**
- **Total Trades**: Number of trades executed
- **Win Rate**: Percentage of profitable trades
- **Total PnL**: Total profit and loss
- **Sharpe Ratio**: Risk-adjusted return measure
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Average Trade Duration**: Average trade holding period
- **Active Strategies**: Number of currently active strategies
- **Signal Quality**: Overall signal accuracy measure

### **Agent Health Metrics:**
- **Status**: Agent health status (healthy, unhealthy, unreachable)
- **Response Time**: Agent response time in seconds
- **Error Count**: Number of recent errors
- **Uptime**: Agent uptime in seconds
- **Last Heartbeat**: Last successful health check timestamp

---

## ⚙️ **Configuration**

### **Monitoring Configuration (Vault Configuration):**
```json
{
    "check_interval": 30,
    "alert_thresholds": {
        "cpu_usage": 80.0,
        "memory_usage": 85.0,
        "disk_usage": 90.0,
        "response_time": 5.0,
        "error_rate": 0.1
    },
    "enabled_checks": [
        "system_health",
        "agent_health",
        "trading_anomaly",
        "performance_metrics"
    ],
    "alert_retention_days": 7,
    "max_alerts": 1000,
    "dashboard_refresh_interval": 30
}
```

---

## 🔄 **Monitoring Workflow**

### **Continuous Monitoring Loop:**
```
System Metrics Collection → Agent Health Checks → Performance Analysis → Alert Generation
         ↓                        ↓                        ↓                ↓
    CPU, Memory, Disk      Agent Status Check      Trading Metrics    Threshold Check
```

### **Alert Management Workflow:**
```
Alert Generation → Alert Storage → Alert Notification → Alert Acknowledgment → Alert Cleanup
      ↓                ↓                ↓                    ↓                    ↓
Threshold Check    Store Alert    Send Notification    User Acknowledgment    Remove Old Alerts
```

---

## 🧪 **Testing Strategy**

### **Unit Tests:**
- System metrics collection
- Agent health checking
- Performance calculation
- Alert generation and management

### **Integration Tests:**
- End-to-end monitoring workflow
- Agent communication testing
- Alert system integration
- Dashboard data generation

### **Performance Tests:**
- Monitoring loop performance
- Memory usage optimization
- Alert processing speed
- Dashboard response times

---

## 🚀 **Implementation Priority**

### **Phase 1: Core Monitoring (Week 1)**
- [x] System metrics collection
- [x] Agent health monitoring
- [x] Basic alert system
- [x] Performance tracking

### **Phase 2: Advanced Features (Week 2)**
- [x] Alert management
- [x] Dashboard generation
- [x] Performance metrics
- [x] API endpoints

### **Phase 3: Integration & Optimization (Week 3)**
- [x] Agent integration
- [x] Performance optimization
- [x] Comprehensive testing
- [x] Documentation

---

## 🎯 **Success Metrics**

### **Monitoring Goals:**
- **System Coverage**: 100% agent and system monitoring
- **Alert Accuracy**: < 1% false positive rate
- **Response Time**: < 30 seconds for critical alerts
- **Uptime Monitoring**: > 99.9% monitoring availability

### **Performance Goals:**
- **Metrics Collection**: < 1 second per metric
- **Health Check**: < 5 seconds for all agents
- **Dashboard Generation**: < 2 seconds for complete dashboard
- **Alert Processing**: < 1 second for alert generation

---

## 🔮 **Future Enhancements**

### **Advanced Monitoring Features:**
- **Machine Learning Anomaly Detection**: AI-powered anomaly detection
- **Predictive Monitoring**: Predictive failure detection
- **Custom Dashboards**: User-configurable monitoring dashboards
- **Advanced Analytics**: Deep performance analysis
- **Real-time Visualization**: Live system visualization

### **Integration Enhancements:**
- **External Monitoring Tools**: Integration with Prometheus, Grafana
- **Notification Systems**: Email, Slack, SMS notifications
- **Log Aggregation**: Centralized log monitoring
- **Performance Profiling**: Detailed performance analysis
- **Capacity Planning**: Resource usage forecasting

---

## 📋 **Implementation Checklist**

### **Core Implementation:**
- [x] System metrics collection
- [x] Agent health monitoring
- [x] Performance tracking
- [x] Alert management
- [x] Dashboard generation
- [x] API endpoints
- [x] Database integration
- [x] Vault configuration
- [x] Docker containerization

### **Testing & Validation:**
- [x] Unit tests
- [x] Integration tests
- [x] Performance tests
- [x] Alert system tests
- [x] End-to-end testing

### **Documentation:**
- [x] API documentation
- [x] Configuration guide
- [x] Monitoring setup guide
- [x] Alert management guide
- [x] Troubleshooting guide

---

**The Monitor Agent is essential for system reliability and should be implemented early to ensure comprehensive system monitoring and alerting.** 📊 