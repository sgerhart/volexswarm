"""
VolexSwarm Meta-Agent - Central Coordinator for Autonomous AI Trading System
Handles agent coordination, natural language interface, and workflow management.
"""

import sys
import os
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Set
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import re
import uuid
from dataclasses import dataclass, asdict
from enum import Enum

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Strategy, Trade, Signal, AgentLog

# Initialize structured logger
logger = get_logger("meta")

app = FastAPI(title="VolexSwarm Meta-Agent", version="1.0.0")

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

# Agent endpoints
AGENT_ENDPOINTS = {
    "research": "http://research:8000",
    "execution": "http://execution:8002", 
    "signal": "http://signal:8003",
    "strategy": "http://strategy:8011",
    "backtest": "http://backtest:8008",
    "optimize": "http://optimize:8006",
    "monitor": "http://monitor:8007",
    "risk": "http://risk:8009",
    "compliance": "http://compliance:8010"
}

# Enhanced WebSocket connection management
@dataclass
class WebSocketConnection:
    """Enhanced WebSocket connection with metadata."""
    id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    subscriptions: Set[str] = None
    connected_at: datetime = None
    last_ping: datetime = None
    
    def __post_init__(self):
        if self.subscriptions is None:
            self.subscriptions = set()
        if self.connected_at is None:
            self.connected_at = datetime.now()
        if self.last_ping is None:
            self.last_ping = datetime.now()

class MessageType(Enum):
    """WebSocket message types."""
    COMMAND = "command"
    AGENT_STATUS = "agent_status"
    SYSTEM_METRICS = "system_metrics"
    TRADE_UPDATE = "trade_update"
    SIGNAL_UPDATE = "signal_update"
    TASK_PROGRESS = "task_progress"
    NOTIFICATION = "notification"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ERROR = "error"

@dataclass
class WebSocketMessage:
    """Structured WebSocket message."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: datetime = None
    id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def to_json(self) -> str:
        """Convert message to JSON string."""
        message_dict = {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "id": self.id
        }
        return json.dumps(message_dict)

class WebSocketManager:
    """Enhanced WebSocket connection manager."""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> connection_ids
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_task = None
        
    async def start_heartbeat(self):
        """Start heartbeat monitoring."""
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
    
    async def stop_heartbeat(self):
        """Stop heartbeat monitoring."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to monitor connections."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                await self._ping_all_connections()
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def _ping_all_connections(self):
        """Send ping to all connections."""
        ping_message = WebSocketMessage(
            type=MessageType.PING,
            data={"timestamp": datetime.now().isoformat()}
        )
        await self.broadcast_to_all(ping_message)
    
    async def _cleanup_stale_connections(self):
        """Remove stale connections."""
        cutoff_time = datetime.now() - timedelta(seconds=self.heartbeat_interval * 3)
        stale_connections = [
            conn_id for conn_id, conn in self.connections.items()
            if conn.last_ping < cutoff_time
        ]
        
        for conn_id in stale_connections:
            await self.disconnect(conn_id)
    
    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """Add new WebSocket connection."""
        connection_id = str(uuid.uuid4())
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket,
            user_id=user_id
        )
        
        await websocket.accept()
        self.connections[connection_id] = connection
        
        # Send welcome message
        welcome_message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "message": "Connected to VolexSwarm Meta-Agent",
                "connection_id": connection_id,
                "server_time": datetime.now().isoformat()
            }
        )
        await self.send_to_connection(connection_id, welcome_message)
        
        logger.info(f"WebSocket connection established: {connection_id}")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Remove WebSocket connection."""
        if connection_id in self.connections:
            # Remove from all subscriptions
            for topic in list(self.subscriptions.keys()):
                self.subscriptions[topic].discard(connection_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            # Close WebSocket if still open
            connection = self.connections[connection_id]
            try:
                await connection.websocket.close()
            except:
                pass
            
            del self.connections[connection_id]
            logger.info(f"WebSocket connection closed: {connection_id}")
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to specific connection."""
        if connection_id in self.connections:
            try:
                connection = self.connections[connection_id]
                await connection.websocket.send_text(message.to_json())
                connection.last_ping = datetime.now()
            except Exception as e:
                logger.error(f"Failed to send message to {connection_id}: {e}")
                await self.disconnect(connection_id)
    
    async def broadcast_to_all(self, message: WebSocketMessage):
        """Broadcast message to all connections."""
        if not self.connections:
            return
        
        failed_connections = []
        for connection_id in self.connections:
            try:
                await self.send_to_connection(connection_id, message)
            except:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for conn_id in failed_connections:
            await self.disconnect(conn_id)
    
    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage):
        """Broadcast message to subscribers of a topic."""
        if topic not in self.subscriptions:
            return
        
        subscribers = list(self.subscriptions[topic])
        for connection_id in subscribers:
            await self.send_to_connection(connection_id, message)
    
    def subscribe(self, connection_id: str, topic: str):
        """Subscribe connection to a topic."""
        if connection_id in self.connections:
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(connection_id)
            
            # Add to connection's subscription list
            self.connections[connection_id].subscriptions.add(topic)
            logger.info(f"Connection {connection_id} subscribed to {topic}")
    
    def unsubscribe(self, connection_id: str, topic: str):
        """Unsubscribe connection from a topic."""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(connection_id)
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        if connection_id in self.connections:
            self.connections[connection_id].subscriptions.discard(topic)
            logger.info(f"Connection {connection_id} unsubscribed from {topic}")
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connections)
    
    def get_topic_subscribers(self, topic: str) -> int:
        """Get number of subscribers for a topic."""
        return len(self.subscriptions.get(topic, set()))

# Global WebSocket manager
ws_manager = WebSocketManager()

class CommandRequest(BaseModel):
    """Request model for natural language commands."""
    command: str


class CommandType(Enum):
    """Types of natural language commands."""
    ANALYZE = "analyze"
    TRADE = "trade"
    STATUS = "status"
    CONFIGURE = "configure"
    MONITOR = "monitor"
    HELP = "help"


@dataclass
class ParsedCommand:
    """Parsed natural language command."""
    command_type: CommandType
    symbol: Optional[str] = None
    action: Optional[str] = None
    confidence_threshold: Optional[float] = None
    amount: Optional[float] = None
    timeframe: Optional[str] = None
    strategy: Optional[str] = None
    parameters: Dict[str, Any] = None


class NaturalLanguageProcessor:
    """Process natural language commands into structured actions."""
    
    def __init__(self):
        self.command_patterns = {
            CommandType.ANALYZE: [
                r"analyze\s+(\w+)",
                r"check\s+(\w+)",
                r"what's\s+(\w+)\s+doing",
                r"how\s+is\s+(\w+)"
            ],
            CommandType.TRADE: [
                r"buy\s+(\w+)",
                r"sell\s+(\w+)",
                r"trade\s+(\w+)",
                r"execute\s+(\w+)",
                r"if\s+confident.*(\w+)"
            ],
            CommandType.STATUS: [
                r"status",
                r"how\s+are\s+we\s+doing",
                r"what's\s+the\s+status",
                r"show\s+me\s+the\s+status"
            ],
            CommandType.CONFIGURE: [
                r"configure\s+(\w+)",
                r"set\s+(\w+)",
                r"change\s+(\w+)"
            ],
            CommandType.MONITOR: [
                r"monitor\s+(\w+)",
                r"watch\s+(\w+)",
                r"track\s+(\w+)"
            ]
        }
    
    def parse_command(self, text: str) -> ParsedCommand:
        """Parse natural language command into structured format."""
        text = text.lower().strip()
        
        # Check for help command first
        if any(word in text for word in ["help", "what can you do", "commands"]):
            return ParsedCommand(command_type=CommandType.HELP)
        
        # Check for status commands
        if any(word in text for word in ["status", "how are we doing", "what's the status"]):
            return ParsedCommand(command_type=CommandType.STATUS)
        
        # Check for analyze commands
        for pattern in self.command_patterns[CommandType.ANALYZE]:
            match = re.search(pattern, text)
            if match:
                symbol = match.group(1).upper()
                return ParsedCommand(
                    command_type=CommandType.ANALYZE,
                    symbol=symbol,
                    parameters=self._extract_parameters(text)
                )
        
        # Check for trade commands
        for pattern in self.command_patterns[CommandType.TRADE]:
            match = re.search(pattern, text)
            if match:
                symbol = match.group(1).upper()
                action = "buy" if "buy" in text else "sell" if "sell" in text else "auto"
                return ParsedCommand(
                    command_type=CommandType.TRADE,
                    symbol=symbol,
                    action=action,
                    confidence_threshold=self._extract_confidence(text),
                    amount=self._extract_amount(text),
                    parameters=self._extract_parameters(text)
                )
        
        # Check for configure commands
        for pattern in self.command_patterns[CommandType.CONFIGURE]:
            match = re.search(pattern, text)
            if match:
                setting = match.group(1)
                return ParsedCommand(
                    command_type=CommandType.CONFIGURE,
                    strategy=setting,
                    parameters=self._extract_parameters(text)
                )
        
        # Check for monitor commands
        for pattern in self.command_patterns[CommandType.MONITOR]:
            match = re.search(pattern, text)
            if match:
                symbol = match.group(1).upper()
                return ParsedCommand(
                    command_type=CommandType.MONITOR,
                    symbol=symbol,
                    parameters=self._extract_parameters(text)
                )
        
        # Default to help if no pattern matches
        return ParsedCommand(command_type=CommandType.HELP)
    
    def _extract_confidence(self, text: str) -> Optional[float]:
        """Extract confidence threshold from text."""
        confidence_match = re.search(r"(\d+)%?\s*confident", text)
        if confidence_match:
            return float(confidence_match.group(1)) / 100
        return None
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text."""
        amount_match = re.search(r"\$?(\d+(?:\.\d+)?)", text)
        if amount_match:
            return float(amount_match.group(1))
        return None
    
    def _extract_parameters(self, text: str) -> Dict[str, Any]:
        """Extract additional parameters from text."""
        params = {}
        
        # Extract timeframe
        timeframe_match = re.search(r"(\d+[hmd])", text)
        if timeframe_match:
            params["timeframe"] = timeframe_match.group(1)
        
        # Extract risk level
        if "high risk" in text or "aggressive" in text:
            params["risk_level"] = "high"
        elif "low risk" in text or "conservative" in text:
            params["risk_level"] = "low"
        else:
            params["risk_level"] = "medium"
        
        return params


class AgentCoordinator:
    """Coordinate communication between autonomous AI agents."""
    
    def __init__(self):
        self.nlp = NaturalLanguageProcessor()
        self.session = None
        self.active_monitors = {}
        self.agent_status_task = None
        self.system_metrics_task = None
    
    async def initialize(self):
        """Initialize HTTP session for agent communication."""
        self.session = aiohttp.ClientSession()
        # Start background tasks for real-time data streaming
        self.agent_status_task = asyncio.create_task(self._stream_agent_status())
        self.system_metrics_task = asyncio.create_task(self._stream_system_metrics())
    
    async def close(self):
        """Close HTTP session and background tasks."""
        if self.agent_status_task:
            self.agent_status_task.cancel()
        if self.system_metrics_task:
            self.system_metrics_task.cancel()
        if self.session:
            await self.session.close()
    
    async def _stream_agent_status(self):
        """Background task to stream agent status updates."""
        while True:
            try:
                status = await self.get_system_status()
                message = WebSocketMessage(
                    type=MessageType.AGENT_STATUS,
                    data=status
                )
                await ws_manager.broadcast_to_topic("agent_status", message)
                await asyncio.sleep(10)  # Update every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent status streaming error: {e}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _stream_system_metrics(self):
        """Background task to stream system metrics."""
        while True:
            try:
                # Get system metrics (placeholder - implement actual metrics collection)
                metrics = {
                    "cpu_usage": 45.2,
                    "memory_usage": 62.8,
                    "disk_usage": 23.1,
                    "network_io": {"in": 1024000, "out": 512000},
                    "active_connections": ws_manager.get_connection_count(),
                    "timestamp": datetime.now().isoformat()
                }
                
                message = WebSocketMessage(
                    type=MessageType.SYSTEM_METRICS,
                    data=metrics
                )
                await ws_manager.broadcast_to_topic("system_metrics", message)
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"System metrics streaming error: {e}")
                await asyncio.sleep(30)
    
    async def get_agent_health(self, agent_name: str) -> Dict[str, Any]:
        """Get health status of a specific agent."""
        try:
            if agent_name not in AGENT_ENDPOINTS:
                return {"status": "unknown", "error": f"Agent {agent_name} not found"}
            
            url = f"{AGENT_ENDPOINTS[agent_name]}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        try:
            # Check all agents
            agent_status = {}
            for agent_name in AGENT_ENDPOINTS.keys():
                agent_status[agent_name] = await self.get_agent_health(agent_name)
            
            # Check database
            db_healthy = db_health_check() if db_client else False
            
            # Check Vault
            vault_healthy = vault_client.health_check() if vault_client else False
            
            # Determine overall status
            all_agents_healthy = all(
                status.get("status") == "healthy" 
                for status in agent_status.values()
            )
            
            overall_status = "healthy" if all_agents_healthy and db_healthy and vault_healthy else "unhealthy"
            
            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "agents": agent_status,
                "database": {"status": "healthy" if db_healthy else "unhealthy"},
                "vault": {"status": "healthy" if vault_healthy else "unhealthy"},
                "websocket_connections": ws_manager.get_connection_count(),
                "autonomous_mode": True
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def analyze_symbol(self, symbol: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze a symbol using research and signal agents."""
        try:
            results = {}
            
            # Get market data from research agent
            research_url = f"{AGENT_ENDPOINTS['research']}/market-data/{symbol}"
            async with self.session.get(research_url) as response:
                if response.status == 200:
                    results["market_data"] = await response.json()
                else:
                    results["market_data"] = {"error": f"Research agent error: {response.status}"}
            
            # Get autonomous signal from signal agent
            signal_url = f"{AGENT_ENDPOINTS['signal']}/signals/generate"
            async with self.session.post(f"{signal_url}?symbol={symbol}") as response:
                if response.status == 200:
                    results["signal"] = await response.json()
                else:
                    results["signal"] = {"error": f"Signal agent error: {response.status}"}
            
            # Get autonomous insights
            insights_url = f"{AGENT_ENDPOINTS['signal']}/autonomous/insights/{symbol}"
            async with self.session.get(insights_url) as response:
                if response.status == 200:
                    results["insights"] = await response.json()
                else:
                    results["insights"] = {"error": f"Insights error: {response.status}"}
            
            # Get technical indicators
            indicators_url = f"{AGENT_ENDPOINTS['signal']}/indicators/{symbol}"
            async with self.session.get(indicators_url) as response:
                if response.status == 200:
                    results["indicators"] = await response.json()
                else:
                    results["indicators"] = {"error": f"Indicators error: {response.status}"}
            
            return {
                "agent": "meta",
                "symbol": symbol,
                "analysis": results,
                "timestamp": datetime.now().isoformat(),
                "autonomous": True
            }
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    async def execute_trade(self, symbol: str, action: str, confidence_threshold: float = 0.7, 
                          amount: Optional[float] = None) -> Dict[str, Any]:
        """Execute a trade using autonomous decision making."""
        try:
            # Step 1: Get autonomous decision
            decision_url = f"{AGENT_ENDPOINTS['signal']}/autonomous/decide"
            params = {"symbol": symbol, "current_balance": amount or 10000}
            async with self.session.post(decision_url, params=params) as response:
                if response.status != 200:
                    return {"error": f"Decision failed: {response.status}"}
                
                decision_data = await response.json()
                decision = decision_data.get("decision", {})
            
            # Step 2: Check if decision meets confidence threshold
            if decision.get("confidence", 0) < confidence_threshold:
                return {
                    "agent": "meta",
                    "symbol": symbol,
                    "action": "hold",
                    "reason": f"Confidence {decision.get('confidence', 0):.1%} below threshold {confidence_threshold:.1%}",
                    "decision": decision,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Step 3: Execute trade if decision is to trade
            if decision.get("action") in ["buy", "sell"]:
                trade_url = f"{AGENT_ENDPOINTS['execution']}/orders"
                trade_params = {
                    "symbol": symbol,
                    "side": decision["action"],
                    "quantity": 0.001,  # Small test quantity
                    "order_type": "market"
                }
                
                async with self.session.post(trade_url, params=trade_params) as response:
                    if response.status == 200:
                        trade_data = await response.json()
                        
                        # Broadcast trade update
                        trade_message = WebSocketMessage(
                            type=MessageType.TRADE_UPDATE,
                            data={
                                "symbol": symbol,
                                "action": "executed",
                                "trade": trade_data,
                                "decision": decision
                            }
                        )
                        await ws_manager.broadcast_to_topic("trade_updates", trade_message)
                        
                        return {
                            "agent": "meta",
                            "symbol": symbol,
                            "action": "executed",
                            "trade": trade_data,
                            "decision": decision,
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {"error": f"Trade execution failed: {response.status}"}
            
            return {
                "agent": "meta",
                "symbol": symbol,
                "action": decision.get("action", "hold"),
                "reason": decision.get("reason", "No action taken"),
                "decision": decision,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Trade execution failed: {str(e)}"}
    
    async def start_monitoring(self, symbol: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start autonomous monitoring of a symbol."""
        try:
            monitor_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Store monitoring configuration
            self.active_monitors[monitor_id] = {
                "symbol": symbol,
                "started_at": datetime.now(),
                "parameters": parameters or {},
                "active": True
            }
            
            # Start background monitoring task
            asyncio.create_task(self._monitor_symbol(monitor_id, symbol, parameters))
            
            return {
                "agent": "meta",
                "monitor_id": monitor_id,
                "symbol": symbol,
                "status": "started",
                "message": f"Started autonomous monitoring of {symbol}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Failed to start monitoring: {str(e)}"}
    
    async def _monitor_symbol(self, monitor_id: str, symbol: str, parameters: Dict[str, Any] = None):
        """Background task to monitor a symbol."""
        try:
            while self.active_monitors.get(monitor_id, {}).get("active", False):
                # Get autonomous decision
                decision_url = f"{AGENT_ENDPOINTS['signal']}/autonomous/decide"
                params = {"symbol": symbol, "current_balance": 10000}
                
                async with self.session.post(decision_url, params=params) as response:
                    if response.status == 200:
                        decision_data = await response.json()
                        decision = decision_data.get("decision", {})
                        
                        # Broadcast monitoring update
                        monitor_message = WebSocketMessage(
                            type=MessageType.TASK_PROGRESS,
                            data={
                                "type": "monitor_update",
                                "monitor_id": monitor_id,
                                "symbol": symbol,
                                "decision": decision
                            }
                        )
                        await ws_manager.broadcast_to_topic("task_progress", monitor_message)
                        
                        # Check if action should be taken
                        if decision.get("confidence", 0) > 0.8:  # High confidence threshold for monitoring
                            # Execute trade
                            trade_result = await self.execute_trade(symbol, decision.get("action", "hold"))
                            
                            # Notify via WebSocket
                            alert_message = WebSocketMessage(
                                type=MessageType.NOTIFICATION,
                                data={
                                    "type": "monitor_alert",
                                    "monitor_id": monitor_id,
                                    "symbol": symbol,
                                    "decision": decision,
                                    "trade_result": trade_result,
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                            await ws_manager.broadcast_to_topic("notifications", alert_message)
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
        except Exception as e:
            logger.error(f"Monitoring failed for {symbol}: {e}")
            self.active_monitors[monitor_id]["active"] = False


# Global coordinator
coordinator = None


@app.on_event("startup")
async def startup_event():
    """Initialize the meta agent on startup."""
    global vault_client, db_client, coordinator
    
    try:
        with logger.log_operation("meta_agent_startup"):
            # Initialize Vault client
            vault_client = get_vault_client()
            logger.info("Vault client initialized successfully")
            
            # Initialize database client
            db_client = get_db_client()
            logger.info("Database client initialized successfully")
            
            # Initialize agent coordinator
            coordinator = AgentCoordinator()
            await coordinator.initialize()
            logger.info("Agent coordinator initialized successfully")
            
            # Start WebSocket manager heartbeat
            await ws_manager.start_heartbeat()
            logger.info("WebSocket manager started successfully")
            
            logger.info("Meta agent initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize meta agent", exception=e)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global coordinator
    if coordinator:
        await coordinator.close()
    await ws_manager.stop_heartbeat()


@app.get("/health")
def health_check():
    """Health check for meta agent."""
    try:
        vault_healthy = vault_client.health_check() if vault_client else False
        db_healthy = db_health_check() if db_client else False
        coordinator_ready = coordinator is not None
        websocket_healthy = ws_manager.get_connection_count() >= 0
        
        overall_healthy = vault_healthy and db_healthy and coordinator_ready and websocket_healthy
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "vault_connected": vault_healthy,
            "database_connected": db_healthy,
            "coordinator_ready": coordinator_ready,
            "websocket_connections": ws_manager.get_connection_count(),
            "agent": "meta"
        }
    except Exception as e:
        logger.error("Health check failed", exception=e)
        return {
            "status": "unhealthy",
            "error": str(e),
            "agent": "meta"
        }


@app.get("/status")
async def get_system_status():
    """Get overall system status."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        return await coordinator.get_system_status()
        
    except Exception as e:
        logger.error("Failed to get system status", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/command")
async def process_command(request: CommandRequest):
    """Process natural language command."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        with logger.log_operation("process_command", {"command": request.command}):
            # Parse command
            parsed = coordinator.nlp.parse_command(request.command)
            
            # Execute based on command type
            if parsed.command_type == CommandType.HELP:
                return {
                    "agent": "meta",
                    "command": request.command,
                    "response": {
                        "type": "help",
                        "message": "Available commands: analyze <symbol>, trade <symbol>, status, monitor <symbol>",
                        "examples": [
                            "analyze BTCUSD",
                            "trade BTCUSD if confident",
                            "status",
                            "monitor ETHUSD"
                        ]
                    }
                }
            
            elif parsed.command_type == CommandType.STATUS:
                status = await coordinator.get_system_status()
                return {
                    "agent": "meta",
                    "command": request.command,
                    "response": status
                }
            
            elif parsed.command_type == CommandType.ANALYZE:
                if not parsed.symbol:
                    raise HTTPException(status_code=400, detail="Symbol required for analysis")
                
                analysis = await coordinator.analyze_symbol(parsed.symbol, parsed.parameters)
                return {
                    "agent": "meta",
                    "command": request.command,
                    "response": analysis
                }
            
            elif parsed.command_type == CommandType.TRADE:
                if not parsed.symbol:
                    raise HTTPException(status_code=400, detail="Symbol required for trading")
                
                trade_result = await coordinator.execute_trade(
                    parsed.symbol, 
                    parsed.action or "auto",
                    parsed.confidence_threshold or 0.7,
                    parsed.amount
                )
                return {
                    "agent": "meta",
                    "command": request.command,
                    "response": trade_result
                }
            
            elif parsed.command_type == CommandType.MONITOR:
                if not parsed.symbol:
                    raise HTTPException(status_code=400, detail="Symbol required for monitoring")
                
                monitor_result = await coordinator.start_monitoring(parsed.symbol, parsed.parameters)
                return {
                    "agent": "meta",
                    "command": request.command,
                    "response": monitor_result
                }
            
            else:
                return {
                    "agent": "meta",
                    "command": request.command,
                    "response": {
                        "type": "unknown",
                        "message": f"Unknown command type: {parsed.command_type}"
                    }
                }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process command", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint for real-time updates."""
    connection_id = await ws_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = MessageType(message_data.get("type", "command"))
            
            if message_type == MessageType.COMMAND:
                # Process command and send response
                command = message_data.get("data", {}).get("command", "")
                result = await process_command(CommandRequest(command=command))
                
                response_message = WebSocketMessage(
                    type=MessageType.COMMAND,
                    data=result
                )
                await ws_manager.send_to_connection(connection_id, response_message)
            
            elif message_type == MessageType.SUBSCRIBE:
                # Subscribe to topic
                topic = message_data.get("data", {}).get("topic", "")
                if topic:
                    ws_manager.subscribe(connection_id, topic)
                    
                    ack_message = WebSocketMessage(
                        type=MessageType.NOTIFICATION,
                        data={"message": f"Subscribed to {topic}"}
                    )
                    await ws_manager.send_to_connection(connection_id, ack_message)
            
            elif message_type == MessageType.UNSUBSCRIBE:
                # Unsubscribe from topic
                topic = message_data.get("data", {}).get("topic", "")
                if topic:
                    ws_manager.unsubscribe(connection_id, topic)
                    
                    ack_message = WebSocketMessage(
                        type=MessageType.NOTIFICATION,
                        data={"message": f"Unsubscribed from {topic}"}
                    )
                    await ws_manager.send_to_connection(connection_id, ack_message)
            
            elif message_type == MessageType.PONG:
                # Update last ping time
                if connection_id in ws_manager.connections:
                    ws_manager.connections[connection_id].last_ping = datetime.now()
            
            # Update connection's last activity
            if connection_id in ws_manager.connections:
                ws_manager.connections[connection_id].last_ping = datetime.now()
            
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        await ws_manager.disconnect(connection_id)


@app.get("/websocket/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": ws_manager.get_connection_count(),
        "topics": {
            topic: ws_manager.get_topic_subscribers(topic) 
            for topic in ws_manager.subscriptions.keys()
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/agents/{agent_name}/health")
async def get_agent_health(agent_name: str):
    """Get health status of a specific agent."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        return await coordinator.get_agent_health(agent_name)
        
    except Exception as e:
        logger.error("Failed to get agent health", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze/{symbol}")
async def analyze_symbol(symbol: str):
    """Analyze a symbol using all agents."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        return await coordinator.analyze_symbol(symbol)
        
    except Exception as e:
        logger.error("Failed to analyze symbol", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/trade/{symbol}")
async def trade_symbol(symbol: str, action: str = "auto", confidence: float = 0.7, amount: Optional[float] = None):
    """Execute a trade for a symbol."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        return await coordinator.execute_trade(symbol, action, confidence, amount)
        
    except Exception as e:
        logger.error("Failed to trade symbol", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/monitor/{symbol}")
async def start_symbol_monitoring(symbol: str):
    """Start monitoring a symbol."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        return await coordinator.start_monitoring(symbol)
        
    except Exception as e:
        logger.error("Failed to start monitoring", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitors")
async def get_active_monitors():
    """Get list of active monitors."""
    try:
        if not coordinator:
            raise HTTPException(status_code=500, detail="Coordinator not initialized")
        
        return {
            "agent": "meta",
            "monitors": coordinator.active_monitors,
            "count": len(coordinator.active_monitors)
        }
        
    except Exception as e:
        logger.error("Failed to get monitors", {"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004) 