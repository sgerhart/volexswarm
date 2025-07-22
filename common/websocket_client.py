"""
Common WebSocket Client for Agent-to-Meta Communication
Provides real-time communication capabilities for all VolexSwarm agents.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, Callable, Set
from dataclasses import dataclass
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """WebSocket message types - matches Meta Agent definitions."""
    AGENT_STATUS = "agent_status"
    HEALTH_UPDATE = "health_update"
    TRADE_UPDATE = "trade_update"
    SIGNAL_UPDATE = "signal_update"
    TASK_PROGRESS = "task_progress"
    NOTIFICATION = "notification"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ERROR = "error"
    COMMAND = "command"
    RESPONSE = "response"

@dataclass
class WebSocketMessage:
    """Structured message for WebSocket communication."""
    type: MessageType
    data: Dict[str, Any]
    timestamp: str = None
    id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if self.id is None:
            self.id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp,
            "id": self.id
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())

class AgentWebSocketClient:
    """WebSocket client for agent-to-Meta communication."""
    
    def __init__(self, agent_name: str, meta_host: str = "meta", meta_port: int = 8004):
        self.agent_name = agent_name
        self.meta_url = f"ws://{meta_host}:{meta_port}/ws"
        self.websocket = None
        self.connected = False
        self.auto_reconnect = True
        self.reconnect_interval = 5  # seconds
        self.heartbeat_interval = 30  # seconds
        self.message_handlers: Dict[MessageType, Set[Callable]] = {}
        self.connection_handlers: Set[Callable] = set()
        self._heartbeat_task = None
        self._reconnect_task = None
        self._listen_task = None
        
        # Initialize message handlers
        for msg_type in MessageType:
            self.message_handlers[msg_type] = set()
    
    async def connect(self) -> bool:
        """Connect to Meta Agent WebSocket server."""
        try:
            logger.info(f"[{self.agent_name}] Connecting to Meta Agent at {self.meta_url}")
            
            self.websocket = await websockets.connect(
                self.meta_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            logger.info(f"[{self.agent_name}] WebSocket connected to Meta Agent")
            
            # Start background tasks
            self._start_background_tasks()
            
            # Send initial agent registration
            await self.send_agent_status({
                "agent": self.agent_name,
                "status": "connected",
                "capabilities": self._get_agent_capabilities()
            })
            
            # Notify connection handlers
            for handler in self.connection_handlers:
                try:
                    await handler(True)
                except Exception as e:
                    logger.error(f"[{self.agent_name}] Connection handler error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to connect to Meta Agent: {e}")
            self.connected = False
            
            if self.auto_reconnect:
                self._schedule_reconnect()
            
            return False
    
    async def disconnect(self):
        """Disconnect from Meta Agent."""
        logger.info(f"[{self.agent_name}] Disconnecting from Meta Agent")
        
        self.auto_reconnect = False
        self.connected = False
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._reconnect_task:
            self._reconnect_task.cancel()
        if self._listen_task:
            self._listen_task.cancel()
        
        # Close WebSocket connection
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                logger.error(f"[{self.agent_name}] Error closing WebSocket: {e}")
        
        # Notify connection handlers
        for handler in self.connection_handlers:
            try:
                await handler(False)
            except Exception as e:
                logger.error(f"[{self.agent_name}] Connection handler error: {e}")
    
    async def send_message(self, message: WebSocketMessage) -> bool:
        """Send message to Meta Agent."""
        if not self.connected or not self.websocket:
            logger.warning(f"[{self.agent_name}] Cannot send message - not connected")
            return False
        
        try:
            await self.websocket.send(message.to_json())
            logger.debug(f"[{self.agent_name}] Sent {message.type.value} message")
            return True
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Failed to send message: {e}")
            self.connected = False
            
            if self.auto_reconnect:
                self._schedule_reconnect()
            
            return False
    
    async def send_agent_status(self, status_data: Dict[str, Any]) -> bool:
        """Send agent status update to Meta Agent."""
        message = WebSocketMessage(
            type=MessageType.AGENT_STATUS,
            data={
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **status_data
            }
        )
        return await self.send_message(message)
    
    async def send_health_update(self, health_data: Dict[str, Any]) -> bool:
        """Send health status update to Meta Agent."""
        message = WebSocketMessage(
            type=MessageType.HEALTH_UPDATE,
            data={
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **health_data
            }
        )
        return await self.send_message(message)
    
    async def send_trade_update(self, trade_data: Dict[str, Any]) -> bool:
        """Send trade update to Meta Agent."""
        message = WebSocketMessage(
            type=MessageType.TRADE_UPDATE,
            data={
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **trade_data
            }
        )
        return await self.send_message(message)
    
    async def send_signal_update(self, signal_data: Dict[str, Any]) -> bool:
        """Send signal update to Meta Agent."""
        message = WebSocketMessage(
            type=MessageType.SIGNAL_UPDATE,
            data={
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **signal_data
            }
        )
        return await self.send_message(message)
    
    async def send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Send notification to Meta Agent."""
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "agent": self.agent_name,
                "timestamp": datetime.utcnow().isoformat(),
                **notification_data
            }
        )
        return await self.send_message(message)
    
    def add_message_handler(self, message_type: MessageType, handler: Callable):
        """Add handler for specific message type."""
        self.message_handlers[message_type].add(handler)
    
    def remove_message_handler(self, message_type: MessageType, handler: Callable):
        """Remove handler for specific message type."""
        self.message_handlers[message_type].discard(handler)
    
    def add_connection_handler(self, handler: Callable):
        """Add handler for connection status changes."""
        self.connection_handlers.add(handler)
    
    def remove_connection_handler(self, handler: Callable):
        """Remove connection status handler."""
        self.connection_handlers.discard(handler)
    
    def _start_background_tasks(self):
        """Start background tasks for heartbeat and message listening."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._listen_task:
            self._listen_task.cancel()
        
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._listen_task = asyncio.create_task(self._listen_loop())
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat messages."""
        while self.connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.connected and self.websocket:
                    ping_message = WebSocketMessage(
                        type=MessageType.PING,
                        data={"agent": self.agent_name}
                    )
                    await self.send_message(ping_message)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_name}] Heartbeat error: {e}")
                break
    
    async def _listen_loop(self):
        """Listen for incoming messages from Meta Agent."""
        while self.connected and self.websocket:
            try:
                message_str = await self.websocket.recv()
                message_data = json.loads(message_str)
                
                message_type = MessageType(message_data.get("type", "notification"))
                
                # Handle message with registered handlers
                for handler in self.message_handlers[message_type]:
                    try:
                        await handler(message_data)
                    except Exception as e:
                        logger.error(f"[{self.agent_name}] Message handler error: {e}")
                
                # Handle PING messages
                if message_type == MessageType.PING:
                    pong_message = WebSocketMessage(
                        type=MessageType.PONG,
                        data={"agent": self.agent_name}
                    )
                    await self.send_message(pong_message)
                
            except ConnectionClosed:
                logger.warning(f"[{self.agent_name}] WebSocket connection closed")
                self.connected = False
                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_name}] Listen loop error: {e}")
                self.connected = False
                break
        
        # Schedule reconnect if needed
        if not self.connected and self.auto_reconnect:
            self._schedule_reconnect()
    
    def _schedule_reconnect(self):
        """Schedule automatic reconnection."""
        if self._reconnect_task and not self._reconnect_task.done():
            return
        
        self._reconnect_task = asyncio.create_task(self._reconnect_loop())
    
    async def _reconnect_loop(self):
        """Automatic reconnection loop."""
        while not self.connected and self.auto_reconnect:
            try:
                logger.info(f"[{self.agent_name}] Attempting to reconnect in {self.reconnect_interval} seconds")
                await asyncio.sleep(self.reconnect_interval)
                
                if await self.connect():
                    break
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.agent_name}] Reconnection error: {e}")
    
    def _get_agent_capabilities(self) -> Dict[str, Any]:
        """Get agent-specific capabilities."""
        # Override in specific agents to provide capabilities
        return {
            "type": self.agent_name,
            "version": "1.0",
            "features": ["websocket", "real_time_updates"]
        }
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.connected and self.websocket is not None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            "agent": self.agent_name,
            "connected": self.connected,
            "meta_url": self.meta_url,
            "auto_reconnect": self.auto_reconnect
        } 