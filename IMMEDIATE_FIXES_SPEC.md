# Immediate Fixes Technical Specification

## 🚨 **CRITICAL ISSUES TO FIX FIRST**

### **Issue 1: Unhealthy Agents**

#### **Execution Agent (Port 8002) - UNHEALTHY**
**Problem**: Health check failing
**Root Cause Analysis**:
```bash
# Check execution agent logs
docker logs volexswarm-execution-1
```

**Likely Issues**:
1. **Port Mismatch**: Dockerfile uses port 8002 but health check expects different port
2. **Missing Dependencies**: CCXT or exchange credentials not properly loaded
3. **Database Connection**: TimescaleDB connection issues
4. **Vault Connection**: Unable to retrieve exchange credentials

**Fix Steps**:
```python
# 1. Check docker/execute.Dockerfile
# Ensure port matches docker-compose.yml
EXPOSE 8002

# 2. Verify health check endpoint in agents/execution/main.py
@app.get("/health")
def health_check():
    try:
        # Add proper error handling
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        exchanges_ready = len(exchanges) > 0
        
        return {
            "status": "healthy" if all([vault_healthy, db_healthy, exchanges_ready]) else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "exchanges_ready": exchanges_ready,
            "agent": "execution"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "agent": "execution"}
```

#### **Signal Agent (Port 8003) - UNHEALTHY**
**Problem**: Health check failing
**Root Cause Analysis**:
```bash
# Check signal agent logs
docker logs volexswarm-signal-1
```

**Likely Issues**:
1. **Port Mismatch**: Dockerfile vs docker-compose port configuration
2. **ML Model Loading**: Issues loading trained models
3. **OpenAI Connection**: GPT integration failing
4. **Database Connection**: TimescaleDB issues

**Fix Steps**:
```python
# 1. Check docker/signal.Dockerfile
# Ensure port matches docker-compose.yml
EXPOSE 8003

# 2. Verify health check in agents/signal/main.py
@app.get("/health")
def health_check():
    try:
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        models_loaded = len(signal_agent.models) if signal_agent else 0
        openai_available = is_openai_available()
        
        return {
            "status": "healthy" if all([vault_healthy, db_healthy]) else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "models_loaded": models_loaded,
            "openai_available": openai_available,
            "agent": "signal"
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "agent": "signal"}
```

### **Issue 2: Missing Core Agents**

#### **Risk Agent Implementation**
**Location**: `agents/risk/main.py`
**Port**: 8009

```python
"""
VolexSwarm Risk Agent - Risk Management and Position Sizing
Handles risk assessment, position sizing, and risk controls.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import numpy as np

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Trade, Portfolio

# Initialize structured logger
logger = get_logger("risk")

app = FastAPI(title="VolexSwarm Risk Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients
vault_client = None
db_client = None

# Risk parameters
MAX_POSITION_SIZE = 0.1  # 10% of portfolio per position
MAX_DAILY_LOSS = 0.05    # 5% max daily loss
MAX_DRAWDOWN = 0.15      # 15% max drawdown
STOP_LOSS = 0.02         # 2% stop loss
TAKE_PROFIT = 0.04       # 4% take profit


class RiskRequest(BaseModel):
    """Request model for risk assessment."""
    symbol: str
    action: str  # 'buy' or 'sell'
    amount: float
    current_price: float
    portfolio_value: float
    current_positions: List[Dict[str, Any]] = []


class RiskResponse(BaseModel):
    """Response model for risk assessment."""
    approved: bool
    recommended_amount: float
    risk_level: str  # 'low', 'medium', 'high'
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_metrics: Dict[str, Any]
    reason: str


class RiskManager:
    """Risk management and position sizing."""
    
    def __init__(self):
        self.max_position_size = MAX_POSITION_SIZE
        self.max_daily_loss = MAX_DAILY_LOSS
        self.max_drawdown = MAX_DRAWDOWN
        self.stop_loss = STOP_LOSS
        self.take_profit = TAKE_PROFIT
    
    def calculate_position_size(self, portfolio_value: float, symbol: str, 
                              current_positions: List[Dict[str, Any]]) -> float:
        """Calculate optimal position size using Kelly Criterion."""
        # Basic Kelly Criterion implementation
        win_rate = 0.55  # Assume 55% win rate
        avg_win = 0.04   # 4% average win
        avg_loss = 0.02  # 2% average loss
        
        kelly_fraction = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
        kelly_fraction = max(0, min(kelly_fraction, self.max_position_size))
        
        # Check correlation with existing positions
        correlation_penalty = self._calculate_correlation_penalty(symbol, current_positions)
        kelly_fraction *= (1 - correlation_penalty)
        
        return kelly_fraction * portfolio_value
    
    def _calculate_correlation_penalty(self, symbol: str, positions: List[Dict[str, Any]]) -> float:
        """Calculate correlation penalty for position sizing."""
        # Simplified correlation calculation
        crypto_positions = [p for p in positions if p.get('asset_type') == 'crypto']
        if len(crypto_positions) > 0:
            return 0.2  # 20% penalty for crypto correlation
        return 0.0
    
    def assess_risk(self, request: RiskRequest) -> RiskResponse:
        """Assess risk for a proposed trade."""
        try:
            # Calculate recommended position size
            recommended_amount = self.calculate_position_size(
                request.portfolio_value, 
                request.symbol, 
                request.current_positions
            )
            
            # Check if trade is within limits
            position_size_ratio = request.amount / request.portfolio_value
            approved = position_size_ratio <= self.max_position_size
            
            # Calculate risk metrics
            risk_metrics = {
                "position_size_ratio": position_size_ratio,
                "max_allowed_ratio": self.max_position_size,
                "portfolio_exposure": self._calculate_portfolio_exposure(request.current_positions),
                "daily_pnl": self._get_daily_pnl(),
                "current_drawdown": self._get_current_drawdown()
            }
            
            # Determine risk level
            risk_level = self._determine_risk_level(risk_metrics)
            
            # Calculate stop loss and take profit
            stop_loss = request.current_price * (1 - self.stop_loss) if request.action == 'buy' else None
            take_profit = request.current_price * (1 + self.take_profit) if request.action == 'buy' else None
            
            reason = "Trade approved within risk limits" if approved else "Position size exceeds maximum allowed"
            
            return RiskResponse(
                approved=approved,
                recommended_amount=recommended_amount,
                risk_level=risk_level,
                stop_loss=stop_loss,
                take_profit=take_profit,
                risk_metrics=risk_metrics,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return RiskResponse(
                approved=False,
                recommended_amount=0.0,
                risk_level="high",
                risk_metrics={},
                reason=f"Risk assessment error: {str(e)}"
            )
    
    def _calculate_portfolio_exposure(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate total portfolio exposure."""
        total_exposure = sum(abs(p.get('value', 0)) for p in positions)
        return total_exposure
    
    def _get_daily_pnl(self) -> float:
        """Get daily P&L (placeholder)."""
        return 0.0  # TODO: Implement actual P&L calculation
    
    def _get_current_drawdown(self) -> float:
        """Get current drawdown (placeholder)."""
        return 0.0  # TODO: Implement actual drawdown calculation
    
    def _determine_risk_level(self, metrics: Dict[str, Any]) -> str:
        """Determine risk level based on metrics."""
        position_ratio = metrics.get('position_size_ratio', 0)
        portfolio_exposure = metrics.get('portfolio_exposure', 0)
        
        if position_ratio > 0.05 or portfolio_exposure > 0.5:
            return "high"
        elif position_ratio > 0.02 or portfolio_exposure > 0.3:
            return "medium"
        else:
            return "low"


# Global risk manager
risk_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize the risk agent on startup."""
    global vault_client, db_client, risk_manager
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized successfully")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized successfully")
        
        # Initialize risk manager
        risk_manager = RiskManager()
        logger.info("Risk manager initialized successfully")
        
        logger.info("Risk agent initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize risk agent", exception=e)
        raise


@app.get("/health")
def health_check():
    """Health check for risk agent."""
    try:
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        risk_manager_ready = risk_manager is not None
        
        overall_healthy = vault_healthy and db_healthy and risk_manager_ready
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "risk_manager_ready": risk_manager_ready,
            "agent": "risk"
        }
    except Exception as e:
        logger.error("Health check failed", exception=e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "agent": "risk"
        }


@app.post("/risk/assess")
def assess_risk(request: RiskRequest):
    """Assess risk for a proposed trade."""
    try:
        if not risk_manager:
            raise HTTPException(status_code=500, detail="Risk manager not initialized")
        
        return risk_manager.assess_risk(request)
        
    except Exception as e:
        logger.error("Risk assessment failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/risk/limits")
def get_risk_limits():
    """Get current risk limits."""
    try:
        if not risk_manager:
            raise HTTPException(status_code=500, detail="Risk manager not initialized")
        
        return {
            "max_position_size": risk_manager.max_position_size,
            "max_daily_loss": risk_manager.max_daily_loss,
            "max_drawdown": risk_manager.max_drawdown,
            "stop_loss": risk_manager.stop_loss,
            "take_profit": risk_manager.take_profit
        }
        
    except Exception as e:
        logger.error("Failed to get risk limits", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risk/limits")
def update_risk_limits(limits: Dict[str, Any]):
    """Update risk limits."""
    try:
        if not risk_manager:
            raise HTTPException(status_code=500, detail="Risk manager not initialized")
        
        # Update risk limits
        if 'max_position_size' in limits:
            risk_manager.max_position_size = limits['max_position_size']
        if 'max_daily_loss' in limits:
            risk_manager.max_daily_loss = limits['max_daily_loss']
        if 'max_drawdown' in limits:
            risk_manager.max_drawdown = limits['max_drawdown']
        if 'stop_loss' in limits:
            risk_manager.stop_loss = limits['stop_loss']
        if 'take_profit' in limits:
            risk_manager.take_profit = limits['take_profit']
        
        logger.info("Risk limits updated", {"limits": limits})
        return {"message": "Risk limits updated successfully"}
        
    except Exception as e:
        logger.error("Failed to update risk limits", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8009)
```

#### **Compliance Agent Implementation**
**Location**: `agents/compliance/main.py`
**Port**: 8010

```python
"""
VolexSwarm Compliance Agent - Regulatory Compliance and Audit
Handles trade logging, audit trails, and regulatory compliance.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Trade, Order, AgentLog

# Initialize structured logger
logger = get_logger("compliance")

app = FastAPI(title="VolexSwarm Compliance Agent", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global clients
vault_client = None
db_client = None


class TradeLog(BaseModel):
    """Trade log entry."""
    trade_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    agent: str
    strategy: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ComplianceCheck(BaseModel):
    """Compliance check request."""
    trade_data: Dict[str, Any]
    user_id: Optional[str] = None
    risk_level: str = "medium"


class ComplianceResponse(BaseModel):
    """Compliance check response."""
    approved: bool
    checks_passed: List[str]
    checks_failed: List[str]
    warnings: List[str]
    audit_trail: Dict[str, Any]


class ComplianceManager:
    """Compliance and audit management."""
    
    def __init__(self):
        self.audit_log = []
        self.compliance_rules = {
            "max_trade_size": 100000,  # $100k max trade size
            "daily_trade_limit": 100,   # 100 trades per day
            "wash_trading_detection": True,
            "market_manipulation_detection": True
        }
    
    def log_trade(self, trade: TradeLog):
        """Log a trade for audit purposes."""
        try:
            audit_entry = {
                "timestamp": datetime.now().isoformat(),
                "trade_id": trade.trade_id,
                "symbol": trade.symbol,
                "side": trade.side,
                "quantity": trade.quantity,
                "price": trade.price,
                "agent": trade.agent,
                "strategy": trade.strategy,
                "metadata": trade.metadata
            }
            
            self.audit_log.append(audit_entry)
            
            # Store in database
            if db_client:
                # TODO: Implement database storage
                pass
            
            logger.info("Trade logged for audit", {"trade_id": trade.trade_id})
            
        except Exception as e:
            logger.error("Failed to log trade", {"error": str(e)})
    
    def check_compliance(self, request: ComplianceCheck) -> ComplianceResponse:
        """Perform compliance checks on a trade."""
        try:
            checks_passed = []
            checks_failed = []
            warnings = []
            
            trade_data = request.trade_data
            
            # Check trade size
            trade_value = trade_data.get('quantity', 0) * trade_data.get('price', 0)
            if trade_value <= self.compliance_rules['max_trade_size']:
                checks_passed.append("trade_size_limit")
            else:
                checks_failed.append("trade_size_limit")
                warnings.append(f"Trade size ${trade_value:,.2f} exceeds limit ${self.compliance_rules['max_trade_size']:,.2f}")
            
            # Check daily trade limit
            daily_trades = self._get_daily_trade_count()
            if daily_trades < self.compliance_rules['daily_trade_limit']:
                checks_passed.append("daily_trade_limit")
            else:
                checks_failed.append("daily_trade_limit")
                warnings.append(f"Daily trade limit exceeded: {daily_trades}/{self.compliance_rules['daily_trade_limit']}")
            
            # Check for wash trading
            if self.compliance_rules['wash_trading_detection']:
                if not self._detect_wash_trading(trade_data):
                    checks_passed.append("wash_trading_check")
                else:
                    checks_failed.append("wash_trading_check")
                    warnings.append("Potential wash trading detected")
            
            # Check for market manipulation
            if self.compliance_rules['market_manipulation_detection']:
                if not self._detect_market_manipulation(trade_data):
                    checks_passed.append("market_manipulation_check")
                else:
                    checks_failed.append("market_manipulation_check")
                    warnings.append("Potential market manipulation detected")
            
            # Overall approval
            approved = len(checks_failed) == 0
            
            audit_trail = {
                "timestamp": datetime.now().isoformat(),
                "user_id": request.user_id,
                "risk_level": request.risk_level,
                "trade_data": trade_data,
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
                "warnings": warnings,
                "approved": approved
            }
            
            return ComplianceResponse(
                approved=approved,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                warnings=warnings,
                audit_trail=audit_trail
            )
            
        except Exception as e:
            logger.error("Compliance check failed", {"error": str(e)})
            return ComplianceResponse(
                approved=False,
                checks_passed=[],
                checks_failed=["compliance_check_error"],
                warnings=[f"Compliance check error: {str(e)}"],
                audit_trail={}
            )
    
    def _get_daily_trade_count(self) -> int:
        """Get daily trade count (placeholder)."""
        return len([log for log in self.audit_log 
                   if datetime.fromisoformat(log['timestamp']).date() == datetime.now().date()])
    
    def _detect_wash_trading(self, trade_data: Dict[str, Any]) -> bool:
        """Detect wash trading (placeholder)."""
        # Simplified wash trading detection
        return False  # TODO: Implement actual detection
    
    def _detect_market_manipulation(self, trade_data: Dict[str, Any]) -> bool:
        """Detect market manipulation (placeholder)."""
        # Simplified market manipulation detection
        return False  # TODO: Implement actual detection
    
    def generate_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report."""
        try:
            # Filter audit log for date range
            filtered_logs = [
                log for log in self.audit_log
                if start_date <= datetime.fromisoformat(log['timestamp']) <= end_date
            ]
            
            report = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_trades": len(filtered_logs),
                "total_volume": sum(log['quantity'] * log['price'] for log in filtered_logs),
                "compliance_issues": [],
                "audit_trail": filtered_logs
            }
            
            return report
            
        except Exception as e:
            logger.error("Failed to generate report", {"error": str(e)})
            return {"error": str(e)}


# Global compliance manager
compliance_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize the compliance agent on startup."""
    global vault_client, db_client, compliance_manager
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized successfully")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized successfully")
        
        # Initialize compliance manager
        compliance_manager = ComplianceManager()
        logger.info("Compliance manager initialized successfully")
        
        logger.info("Compliance agent initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize compliance agent", exception=e)
        raise


@app.get("/health")
def health_check():
    """Health check for compliance agent."""
    try:
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        compliance_manager_ready = compliance_manager is not None
        
        overall_healthy = vault_healthy and db_healthy and compliance_manager_ready
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "compliance_manager_ready": compliance_manager_ready,
            "agent": "compliance"
        }
    except Exception as e:
        logger.error("Health check failed", exception=e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "agent": "compliance"
        }


@app.post("/compliance/check")
def check_compliance(request: ComplianceCheck):
    """Perform compliance check on trade."""
    try:
        if not compliance_manager:
            raise HTTPException(status_code=500, detail="Compliance manager not initialized")
        
        return compliance_manager.check_compliance(request)
        
    except Exception as e:
        logger.error("Compliance check failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compliance/log")
def log_trade(trade: TradeLog):
    """Log a trade for audit purposes."""
    try:
        if not compliance_manager:
            raise HTTPException(status_code=500, detail="Compliance manager not initialized")
        
        compliance_manager.log_trade(trade)
        return {"message": "Trade logged successfully"}
        
    except Exception as e:
        logger.error("Failed to log trade", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/compliance/report")
def generate_report(start_date: str, end_date: str):
    """Generate compliance report."""
    try:
        if not compliance_manager:
            raise HTTPException(status_code=500, detail="Compliance manager not initialized")
        
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        
        return compliance_manager.generate_report(start, end)
        
    except Exception as e:
        logger.error("Failed to generate report", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8010)
```

### **Issue 3: Redis Implementation**

#### **Add Redis to docker-compose.yml**
```yaml
# Add to docker-compose.yml
redis:
  image: redis:7-alpine
  container_name: volexswarm-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  restart: unless-stopped
  command: redis-server --appendonly yes

# Add to volumes section
volumes:
  redis_data:
```

#### **Create Redis Client**
**Location**: `common/redis_client.py`

```python
"""
Redis Client for VolexSwarm
Provides caching and real-time messaging capabilities.
"""

import os
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List
import redis.asyncio as redis
from datetime import datetime, timedelta

from .logging import get_logger

logger = get_logger("redis")

class VolexSwarmRedisClient:
    """Redis client for VolexSwarm with caching and messaging."""
    
    def __init__(self):
        self.redis_client = None
        self.pubsub = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Redis client."""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.pubsub = self.redis_client.pubsub()
            logger.info("Redis client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.redis_client = None
    
    async def is_available(self) -> bool:
        """Check if Redis is available."""
        try:
            if self.redis_client:
                await self.redis_client.ping()
                return True
            return False
        except Exception:
            return False
    
    # Caching methods
    async def set_cache(self, key: str, value: Any, ttl: int = 300):
        """Set cache value with TTL."""
        try:
            if self.redis_client:
                serialized_value = json.dumps(value, default=str)
                await self.redis_client.setex(key, ttl, serialized_value)
                logger.debug(f"Cache set: {key}")
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value."""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None
    
    async def delete_cache(self, key: str):
        """Delete cache value."""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
                logger.debug(f"Cache deleted: {key}")
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
    
    # Pub/Sub methods
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel."""
        try:
            if self.redis_client:
                serialized_message = json.dumps(message, default=str)
                await self.redis_client.publish(channel, serialized_message)
                logger.debug(f"Published to {channel}: {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
    
    async def subscribe(self, channel: str):
        """Subscribe to channel."""
        try:
            if self.pubsub:
                await self.pubsub.subscribe(channel)
                logger.info(f"Subscribed to channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
    
    async def unsubscribe(self, channel: str):
        """Unsubscribe from channel."""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe(channel)
                logger.info(f"Unsubscribed from channel: {channel}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")
    
    async def get_message(self, timeout: float = 1.0) -> Optional[Dict[str, Any]]:
        """Get message from subscribed channels."""
        try:
            if self.pubsub:
                message = await self.pubsub.get_message(timeout=timeout)
                if message and message['type'] == 'message':
                    return json.loads(message['data'])
            return None
        except Exception as e:
            logger.error(f"Failed to get message: {e}")
            return None
    
    # Session storage
    async def set_session(self, session_id: str, data: Dict[str, Any], ttl: int = 3600):
        """Set session data."""
        key = f"session:{session_id}"
        await self.set_cache(key, data, ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        key = f"session:{session_id}"
        return await self.get_cache(key)
    
    async def delete_session(self, session_id: str):
        """Delete session data."""
        key = f"session:{session_id}"
        await self.delete_cache(key)
    
    # Rate limiting
    async def check_rate_limit(self, key: str, limit: int, window: int = 60) -> bool:
        """Check rate limit."""
        try:
            if self.redis_client:
                current = await self.redis_client.get(key)
                if current and int(current) >= limit:
                    return False
                
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, window)
                await pipe.execute()
                return True
            return True
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True


# Global Redis client instance
redis_client = None


def get_redis_client() -> VolexSwarmRedisClient:
    """Get global Redis client instance."""
    global redis_client
    if redis_client is None:
        redis_client = VolexSwarmRedisClient()
    return redis_client


async def is_redis_available() -> bool:
    """Check if Redis is available."""
    client = get_redis_client()
    return await client.is_available()
```

### **Issue 4: Update Meta-Agent**

#### **Add Risk and Compliance Endpoints**
```python
# Update AGENT_ENDPOINTS in agents/meta/main.py
AGENT_ENDPOINTS = {
    "research": "http://research:8000",
    "execution": "http://execution:8002", 
    "signal": "http://signal:8003",
    "risk": "http://risk:8009",
    "compliance": "http://compliance:8010"
}
```

#### **Add Risk and Compliance Methods**
```python
# Add to AgentCoordinator class in agents/meta/main.py

async def check_risk(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
    """Check risk for a trade."""
    try:
        risk_url = f"{AGENT_ENDPOINTS['risk']}/risk/assess"
        async with self.session.post(risk_url, json=trade_request) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": f"Risk check failed: {response.status}"}
    except Exception as e:
        return {"error": f"Risk check failed: {str(e)}"}

async def check_compliance(self, trade_request: Dict[str, Any]) -> Dict[str, Any]:
    """Check compliance for a trade."""
    try:
        compliance_url = f"{AGENT_ENDPOINTS['compliance']}/compliance/check"
        async with self.session.post(compliance_url, json=trade_request) as response:
            if response.status == 200:
                return await response.json()
            else:
                return {"error": f"Compliance check failed: {response.status}"}
    except Exception as e:
        return {"error": f"Compliance check failed: {str(e)}"}
```

### **Issue 5: Create Dockerfiles**

#### **Risk Agent Dockerfile**
**Location**: `docker/risk.Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY ./common /app/common

# Copy agent code
COPY ./agents/risk /app/agents/risk

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8009

# Run the application
CMD ["python", "agents/risk/main.py"]
```

#### **Compliance Agent Dockerfile**
**Location**: `docker/compliance.Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY ./common /app/common

# Copy agent code
COPY ./agents/compliance /app/agents/compliance

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8010

# Run the application
CMD ["python", "agents/compliance/main.py"]
```

## 🚀 **Implementation Steps**

### **Step 1: Fix Current Issues (Day 1)**
1. Debug execution agent health issues
2. Debug signal agent health issues
3. Fix port configuration mismatches
4. Test all existing agent communications

### **Step 2: Add Missing Infrastructure (Day 2)**
1. Add Redis service to docker-compose.yml
2. Create common/redis_client.py
3. Test Redis connectivity

### **Step 3: Implement Missing Agents (Day 3-4)**
1. Create Risk Agent (agents/risk/main.py)
2. Create Compliance Agent (agents/compliance/main.py)
3. Create Dockerfiles for both agents
4. Add agents to docker-compose.yml

### **Step 4: Update System Integration (Day 5)**
1. Update Meta-Agent to include new endpoints
2. Test complete agent communication
3. Verify all agents are healthy
4. Test end-to-end trading pipeline

### **Step 5: Testing and Validation (Day 6-7)**
1. Test risk management functionality
2. Test compliance checking
3. Test Redis caching
4. Validate complete system operation

## 📋 **Success Criteria**

After completing these fixes:
- [ ] All agents show as HEALTHY in `docker ps`
- [ ] Risk Agent responds to risk assessment requests
- [ ] Compliance Agent responds to compliance checks
- [ ] Redis is running and accessible
- [ ] Meta-Agent can coordinate all agents
- [ ] Complete trading pipeline works end-to-end
- [ ] No critical errors in agent logs

This will give you a solid foundation to build upon for the advanced features in the roadmap. 