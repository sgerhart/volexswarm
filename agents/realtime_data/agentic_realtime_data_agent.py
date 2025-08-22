"""
Real-Time Data Hub Agent

This agent manages WebSocket connections to exchanges, aggregates real-time data streams,
and provides instant market data access to other agents in the VolexSwarm system.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from queue import PriorityQueue
import websockets
import ccxt.async_support as ccxt

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from pydantic import BaseModel
import uvicorn

from common.db import get_session
from common.models import PriceData
from common.vault import get_exchange_credentials
from agents.agentic_framework.agent_templates import BaseAgent, AgentConfig
from agents.agentic_framework.mcp_tools import MCPTool, MCPToolRegistry

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages multiple WebSocket connections to exchanges."""
    
    def __init__(self):
        self.connections = {}  # connection_key -> WebSocket connection
        self.subscriptions = {}  # connection_key -> list of subscribed channels
        self.data_handlers = {}  # channel -> handler function
        self.reconnect_attempts = {}  # connection_key -> attempt count
        self.connection_timestamps = {}  # connection_key -> connection start time
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        self.connection_timeout = 23 * 60 * 60  # 23 hours (reconnect before 24h limit)
        self.is_running = False
        self.loop = None
        
    async def connect_to_exchange(self, exchange_name: str, ws_url: str, api_key: str = None, secret: str = None):
        """Connect to an exchange WebSocket."""
        try:
            if exchange_name in self.connections:
                await self.disconnect_from_exchange(exchange_name)
            
            # Create WebSocket connection
            connection = await websockets.connect(ws_url)
            self.connections[exchange_name] = connection
            self.subscriptions[exchange_name] = []
            self.connection_timestamps[exchange_name] = time.time()
            self.reconnect_attempts[exchange_name] = 0
            
            logger.info(f"Connected to {exchange_name} WebSocket")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to {exchange_name}: {e}")
            return False
    
    async def start_listener(self, connection_key: str, data_handler: Callable):
        """Start listening for data from a stream."""
        if connection_key in self.connections:
            asyncio.create_task(self.listen_for_data(connection_key, data_handler))
            logger.info(f"Started listener for {connection_key}")
    
    async def disconnect_from_exchange(self, exchange_name: str):
        """Disconnect from an exchange WebSocket."""
        if exchange_name in self.connections:
            try:
                await self.connections[exchange_name].close()
                del self.connections[exchange_name]
                del self.subscriptions[exchange_name]
                logger.info(f"Disconnected from {exchange_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {exchange_name}: {e}")
    
    async def subscribe_to_channel(self, exchange_name: str, channel: str, symbol: str = None):
        """Subscribe to a WebSocket channel."""
        if exchange_name not in self.connections:
            logger.error(f"No connection to {exchange_name}")
            return False
        
        try:
            # Create stream name according to Binance format
            if symbol:
                stream_name = f"{symbol.lower()}@{channel}"
            else:
                stream_name = channel
            
            # Send subscription message according to Binance WebSocket API
            subscription_msg = {
                "method": "SUBSCRIBE",
                "params": [stream_name],
                "id": int(time.time() * 1000)
            }
            
            logger.info(f"Sending subscription message: {subscription_msg}")
            
            await self.connections[exchange_name].send(json.dumps(subscription_msg))
            self.subscriptions[exchange_name].append(stream_name)
            
            logger.info(f"Subscribed to {stream_name} on {exchange_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {channel} on {exchange_name}: {e}")
            return False
    
    async def listen_for_data(self, connection_key: str, data_handler: Callable):
        """Listen for data from a WebSocket stream."""
        if connection_key not in self.connections:
            return
        
        try:
            logger.info(f"Starting to listen for data from {connection_key}")
            async for message in self.connections[connection_key]:
                try:
                    data = json.loads(message)
                    logger.debug(f"Received data from {connection_key}: {data}")
                    await data_handler(connection_key, data)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {connection_key}: {message}")
                except Exception as e:
                    logger.error(f"Error processing message from {connection_key}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning(f"Connection to {connection_key} closed")
            await self.handle_reconnection(connection_key)
        except Exception as e:
            logger.error(f"Error listening to {connection_key}: {e}")
    
    async def handle_reconnection(self, connection_key: str):
        """Handle automatic reconnection."""
        if self.reconnect_attempts[connection_key] < self.max_reconnect_attempts:
            self.reconnect_attempts[connection_key] += 1
            logger.info(f"Attempting to reconnect to {connection_key} (attempt {self.reconnect_attempts[connection_key]})")
            
            await asyncio.sleep(self.reconnect_delay)
            # Reconnection logic would go here
        else:
            logger.error(f"Max reconnection attempts reached for {connection_key}")
    
    async def check_connection_timeouts(self):
        """Check for connections approaching the 24-hour limit and reconnect."""
        current_time = time.time()
        connections_to_reconnect = []
        
        for connection_key, timestamp in self.connection_timestamps.items():
            if current_time - timestamp > self.connection_timeout:
                connections_to_reconnect.append(connection_key)
                logger.info(f"Connection {connection_key} approaching 24h limit, scheduling reconnection")
        
        for connection_key in connections_to_reconnect:
            await self.reconnect_stream(connection_key)
    
    async def reconnect_stream(self, connection_key: str):
        """Reconnect a specific stream."""
        try:
            # Extract exchange and stream info from connection key
            parts = connection_key.split('_', 1)
            if len(parts) != 2:
                logger.error(f"Invalid connection key format: {connection_key}")
                return False
            
            exchange_name, stream_name = parts
            
            # Close existing connection
            if connection_key in self.connections:
                try:
                    await self.connections[connection_key].close()
                except:
                    pass
                del self.connections[connection_key]
            
            # Create new connection
            stream_url = f"wss://fstream.binance.com/ws/{stream_name}"
            connection = await websockets.connect(stream_url)
            
            # Update connection info
            self.connections[connection_key] = connection
            self.connection_timestamps[connection_key] = time.time()
            self.reconnect_attempts[connection_key] = 0
            
            logger.info(f"Successfully reconnected to stream: {stream_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to reconnect to {connection_key}: {e}")
            return False

class DataStreamAggregator:
    """Aggregates and normalizes data from multiple sources."""
    
    def __init__(self):
        self.market_data_cache = {}  # symbol -> latest data
        self.data_quality_metrics = {}  # symbol -> quality metrics
        self.latency_monitor = {}  # exchange -> latency measurements
        self.data_validators = {}  # data_type -> validation function
        self.subscribers = []  # List of callback functions for data updates
        
    def add_subscriber(self, callback: Callable):
        """Add a subscriber for data updates."""
        self.subscribers.append(callback)
    
    async def process_market_data(self, exchange_name: str, data: Dict[str, Any]):
        """Process incoming market data."""
        try:
            # Extract symbol and data type
            symbol = data.get('s', data.get('symbol', 'UNKNOWN'))
            data_type = self._determine_data_type(data)
            
            # Normalize data
            normalized_data = self._normalize_data(exchange_name, data, data_type)
            
            # Validate data
            if not self._validate_data(normalized_data, data_type):
                logger.warning(f"Invalid data from {exchange_name}: {data}")
                return
            
            # Update cache
            cache_key = f"{exchange_name}_{symbol}_{data_type}"
            self.market_data_cache[cache_key] = {
                'data': normalized_data,
                'timestamp': datetime.utcnow(),
                'exchange': exchange_name,
                'symbol': symbol,
                'data_type': data_type
            }
            
            # Update quality metrics
            self._update_quality_metrics(exchange_name, symbol, data_type)
            
            # Notify subscribers
            await self._notify_subscribers(cache_key, normalized_data)
            
            # Store in database
            await self._store_market_data(normalized_data)
            
        except Exception as e:
            logger.error(f"Error processing market data from {exchange_name}: {e}")
    
    def _determine_data_type(self, data: Dict[str, Any]) -> str:
        """Determine the type of market data based on Binance WebSocket format."""
        event_type = data.get('e', '')
        
        if event_type == 'aggTrade':
            return 'aggTrade'
        elif event_type == 'kline':
            return 'kline'
        elif event_type == '24hrTicker':
            return 'ticker'
        elif event_type == 'markPriceUpdate':
            return 'markPrice'
        elif event_type == 'miniTicker':
            return 'miniTicker'
        elif event_type == 'depth':
            return 'orderbook'
        else:
            # Fallback to old method for backward compatibility
            if 'k' in data:  # Kline/candlestick data
                return 'kline'
            elif 'b' in data and 'a' in data:  # Order book data
                return 'orderbook'
            elif 'p' in data and 'q' in data:  # Trade data
                return 'trade'
            elif 'c' in data:  # Ticker data
                return 'ticker'
            else:
                return 'unknown'
    
    def _normalize_data(self, exchange_name: str, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Normalize data from different exchanges to a common format."""
        normalized = {
            'exchange': exchange_name,
            'data_type': data_type,
            'timestamp': datetime.utcnow(),
            'raw_data': data
        }
        
        if data_type == 'aggTrade':
            # Aggregate Trade Stream data
            normalized.update({
                'symbol': data.get('s', ''),
                'aggregate_trade_id': data.get('a'),
                'price': float(data.get('p', 0)),
                'quantity': float(data.get('q', 0)),
                'first_trade_id': data.get('f'),
                'last_trade_id': data.get('l'),
                'trade_time': data.get('T'),
                'buyer_maker': data.get('m', False),
                'event_time': data.get('E')
            })
        elif data_type == 'kline':
            # Kline/Candlestick Stream data
            k = data.get('k', {})
            normalized.update({
                'symbol': k.get('s', ''),
                'open_time': k.get('t', 0),
                'close_time': k.get('T', 0),
                'open': float(k.get('o', 0)),
                'high': float(k.get('h', 0)),
                'low': float(k.get('l', 0)),
                'close': float(k.get('c', 0)),
                'volume': float(k.get('v', 0)),
                'quote_volume': float(k.get('q', 0)),
                'trades': int(k.get('n', 0)),
                'is_closed': k.get('x', False),
                'taker_buy_volume': float(k.get('V', 0)),
                'taker_buy_quote_volume': float(k.get('Q', 0)),
                'event_time': data.get('E')
            })
        elif data_type == 'ticker':
            # 24hr Ticker Stream data
            normalized.update({
                'symbol': data.get('s', ''),
                'price_change': float(data.get('p', 0)),
                'price_change_percent': float(data.get('P', 0)),
                'weighted_avg_price': float(data.get('w', 0)),
                'prev_close_price': float(data.get('x', 0)),
                'last_price': float(data.get('c', 0)),
                'last_qty': float(data.get('Q', 0)),
                'bid_price': float(data.get('b', 0)),
                'ask_price': float(data.get('a', 0)),
                'open_price': float(data.get('o', 0)),
                'high_price': float(data.get('h', 0)),
                'low_price': float(data.get('l', 0)),
                'volume': float(data.get('v', 0)),
                'quote_volume': float(data.get('q', 0)),
                'event_time': data.get('E')
            })
        elif data_type == 'markPrice':
            # Mark Price Stream data
            normalized.update({
                'symbol': data.get('s', ''),
                'mark_price': float(data.get('p', 0)),
                'index_price': float(data.get('i', 0)),
                'estimated_settle_price': float(data.get('P', 0)),
                'funding_rate': float(data.get('r', 0)),
                'next_funding_time': data.get('T'),
                'event_time': data.get('E')
            })
        elif data_type == 'miniTicker':
            # Mini Ticker Stream data
            normalized.update({
                'symbol': data.get('s', ''),
                'close_price': float(data.get('c', 0)),
                'open_price': float(data.get('o', 0)),
                'high_price': float(data.get('h', 0)),
                'low_price': float(data.get('l', 0)),
                'volume': float(data.get('v', 0)),
                'quote_volume': float(data.get('q', 0)),
                'event_time': data.get('E')
            })
        elif data_type == 'trade':
            # Legacy trade data format
            normalized.update({
                'symbol': data.get('s', ''),
                'trade_id': data.get('t', 0),
                'price': float(data.get('p', 0)),
                'quantity': float(data.get('q', 0)),
                'buyer_maker': data.get('m', False),
                'trade_time': data.get('T', 0)
            })
        
        return normalized
    
    def _validate_data(self, data: Dict[str, Any], data_type: str) -> bool:
        """Validate normalized data."""
        if data_type == 'kline':
            return all(key in data for key in ['symbol', 'open', 'high', 'low', 'close', 'volume'])
        elif data_type == 'trade':
            return all(key in data for key in ['symbol', 'price', 'quantity'])
        elif data_type == 'ticker':
            return all(key in data for key in ['symbol', 'last_price'])
        return True
    
    def _update_quality_metrics(self, exchange_name: str, symbol: str, data_type: str):
        """Update data quality metrics."""
        key = f"{exchange_name}_{symbol}_{data_type}"
        if key not in self.data_quality_metrics:
            self.data_quality_metrics[key] = {
                'total_messages': 0,
                'valid_messages': 0,
                'last_update': datetime.utcnow(),
                'latency_avg': 0
            }
        
        metrics = self.data_quality_metrics[key]
        metrics['total_messages'] += 1
        metrics['valid_messages'] += 1
        metrics['last_update'] = datetime.utcnow()
    
    async def _notify_subscribers(self, cache_key: str, data: Dict[str, Any]):
        """Notify all subscribers of new data."""
        for subscriber in self.subscribers:
            try:
                await subscriber(cache_key, data)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
    
    async def _store_market_data(self, data: Dict[str, Any]):
        """Store market data in database."""
        try:
            with get_session() as session:
                if data['data_type'] == 'kline':
                    price_data = PriceData(
                        time=datetime.fromtimestamp(data['open_time'] / 1000),
                        symbol=data['symbol'],
                        exchange=data['exchange'],
                        open=data['open'],
                        high=data['high'],
                        low=data['low'],
                        close=data['close'],
                        volume=data['volume'],
                        timeframe='1m'  # Default timeframe
                    )
                    session.add(price_data)
                    session.commit()
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
    
    def get_latest_data(self, symbol: str, data_type: str = None) -> Dict[str, Any]:
        """Get latest data for a symbol."""
        if data_type:
            cache_key = f"binanceus_{symbol}_{data_type}"
        else:
            # Return all data types for the symbol
            result = {}
            for key, value in self.market_data_cache.items():
                if symbol in key:
                    result[key] = value
            return result
        
        return self.market_data_cache.get(cache_key, {})
    
    def get_data_quality_metrics(self) -> Dict[str, Any]:
        """Get data quality metrics."""
        return self.data_quality_metrics

class RealTimeDataTools:
    """Tools for real-time data management."""
    
    def __init__(self, websocket_manager: WebSocketManager, data_aggregator: DataStreamAggregator):
        self.websocket_manager = websocket_manager
        self.data_aggregator = data_aggregator
        self.tools = {
            "connect_to_exchange": self.connect_to_exchange,
            "subscribe_to_channel": self.subscribe_to_channel,
            "get_latest_data": self.get_latest_data,
            "get_data_quality": self.get_data_quality,
            "list_connections": self.list_connections,
            "disconnect_from_exchange": self.disconnect_from_exchange,
            "get_market_summary": self.get_market_summary
        }
    
    async def connect_to_exchange(self, exchange_name: str, symbols: List[str] = None) -> Dict[str, Any]:
        """Connect to an exchange and subscribe to symbols."""
        try:
            # For now, connect without credentials (public WebSocket)
            # In production, this would get credentials from Vault
            ws_url = "wss://fstream.binance.com/ws"  # Binance Futures WebSocket Market Streams
            success = await self.websocket_manager.connect_to_exchange(exchange_name, ws_url)
            
            if not success:
                return {
                    "status": "error",
                    "message": f"Failed to connect to {exchange_name}"
                }
            
            # Subscribe to symbols if provided
            if symbols:
                for symbol in symbols:
                    # Subscribe to different data types
                    await self.websocket_manager.subscribe_to_channel(exchange_name, "aggTrade", symbol)
                    await self.websocket_manager.subscribe_to_channel(exchange_name, "kline_1m", symbol)
                    await self.websocket_manager.subscribe_to_channel(exchange_name, "24hrTicker", symbol)
                
                # Start listener for the exchange connection
                await self.websocket_manager.start_listener(exchange_name, self.data_aggregator.process_market_data)
            
            return {
                "status": "success",
                "message": f"Connected to {exchange_name}",
                "symbols": symbols or []
            }
            
        except Exception as e:
            logger.error(f"Error connecting to {exchange_name}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def subscribe_to_channel(self, exchange_name: str, channel: str, symbol: str) -> Dict[str, Any]:
        """Subscribe to a specific channel for a symbol."""
        try:
            success = await self.websocket_manager.subscribe_to_channel(exchange_name, channel, symbol)
            
            if success:
                return {
                    "status": "success",
                    "message": f"Subscribed to {channel} for {symbol} on {exchange_name}"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to subscribe to {channel} for {symbol} on {exchange_name}"
                }
                
        except Exception as e:
            logger.error(f"Error subscribing to channel: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_latest_data(self, symbol: str, data_type: str = None) -> Dict[str, Any]:
        """Get latest market data for a symbol."""
        try:
            data = self.data_aggregator.get_latest_data(symbol, data_type)
            
            if data:
                return {
                    "status": "success",
                    "symbol": symbol,
                    "data_type": data_type,
                    "data": data
                }
            else:
                return {
                    "status": "warning",
                    "message": f"No data found for {symbol}",
                    "symbol": symbol
                }
                
        except Exception as e:
            logger.error(f"Error getting latest data: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_data_quality(self) -> Dict[str, Any]:
        """Get data quality metrics."""
        try:
            metrics = self.data_aggregator.get_data_quality_metrics()
            
            return {
                "status": "success",
                "metrics": metrics,
                "summary": {
                    "total_streams": len(metrics),
                    "active_streams": sum(1 for m in metrics.values() if m['valid_messages'] > 0),
                    "avg_quality": sum(m['valid_messages'] / max(m['total_messages'], 1) for m in metrics.values()) / max(len(metrics), 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting data quality: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def list_connections(self) -> Dict[str, Any]:
        """List all active WebSocket connections."""
        try:
            connections = list(self.websocket_manager.connections.keys())
            subscriptions = self.websocket_manager.subscriptions
            
            return {
                "status": "success",
                "connections": connections,
                "subscriptions": subscriptions,
                "total_connections": len(connections)
            }
            
        except Exception as e:
            logger.error(f"Error listing connections: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def disconnect_from_exchange(self, exchange_name: str) -> Dict[str, Any]:
        """Disconnect from an exchange."""
        try:
            await self.websocket_manager.disconnect_from_exchange(exchange_name)
            
            return {
                "status": "success",
                "message": f"Disconnected from {exchange_name}"
            }
            
        except Exception as e:
            logger.error(f"Error disconnecting from {exchange_name}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_market_summary(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Get market summary for symbols."""
        try:
            if not symbols:
                # Get all symbols from cache
                symbols = list(set(key.split('_')[1] for key in self.data_aggregator.market_data_cache.keys()))
            
            summary = {}
            for symbol in symbols:
                ticker_data = self.data_aggregator.get_latest_data(symbol, 'ticker')
                if ticker_data:
                    summary[symbol] = {
                        'last_price': ticker_data.get('data', {}).get('last_price', 0),
                        'price_change': ticker_data.get('data', {}).get('price_change', 0),
                        'volume': ticker_data.get('data', {}).get('volume', 0),
                        'last_update': ticker_data.get('timestamp', datetime.utcnow()).isoformat()
                    }
            
            return {
                "status": "success",
                "summary": summary,
                "total_symbols": len(summary)
            }
            
        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

class AgenticRealTimeDataAgent:
    """Real-Time Data Hub Agent for managing WebSocket connections and data streams."""
    
    def __init__(self):
        # Initialize WebSocket manager and data aggregator
        self.websocket_manager = WebSocketManager()
        self.data_aggregator = DataStreamAggregator()
        self.tools = RealTimeDataTools(self.websocket_manager, self.data_aggregator)
        
        # Initialize infrastructure clients
        self.db_client = None
        self.vault_client = None
        self.ws_client = None
        
        # Set up data handler
        self.data_aggregator.add_subscriber(self._handle_data_update)
        
        # Initialize infrastructure connections
        self._initialize_infrastructure()
        
        # Start WebSocket listeners
        self._start_websocket_listeners()
        
        logger.info("Real-Time Data Hub Agent initialized successfully")
    
    def _initialize_infrastructure(self):
        """Initialize infrastructure connections (database, vault, websocket)."""
        try:
            # Initialize database client
            from common.db import get_db_client
            self.db_client = get_db_client()
            logger.info("Database client initialized")
            
            # Initialize vault client
            from common.vault import get_vault_client
            self.vault_client = get_vault_client()
            logger.info("Vault client initialized")
            
            # Initialize websocket client
            from common.websocket_client import AgentWebSocketClient
            self.ws_client = AgentWebSocketClient(
                agent_name="realtime_data"
            )
            logger.info("WebSocket client initialized")
            
            # Connect to websocket
            asyncio.create_task(self._connect_websocket())
            
        except Exception as e:
            logger.error(f"Error initializing infrastructure: {e}")
    
    async def _connect_websocket(self):
        """Connect to websocket server."""
        try:
            if self.ws_client:
                await self.ws_client.connect()
                logger.info("WebSocket connected successfully")
        except Exception as e:
            logger.error(f"Error connecting to websocket: {e}")

    def _start_websocket_listeners(self):
        """Start WebSocket listeners for all connections."""
        for connection_key in self.websocket_manager.connections:
            asyncio.create_task(
                self.websocket_manager.listen_for_data(
                    connection_key, 
                    self.data_aggregator.process_market_data
                )
            )
        
        # Start background task to check connection timeouts
        asyncio.create_task(self._connection_timeout_checker())
    
    async def _connection_timeout_checker(self):
        """Background task to check and reconnect connections approaching 24h limit."""
        while True:
            try:
                await self.websocket_manager.check_connection_timeouts()
                # Check every hour
                await asyncio.sleep(60 * 60)
            except Exception as e:
                logger.error(f"Error in connection timeout checker: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _handle_data_update(self, cache_key: str, data: Dict[str, Any]):
        """Handle data updates from the aggregator."""
        logger.debug(f"Data update for {cache_key}: {data.get('data_type', 'unknown')}")
        # Additional processing can be added here

# Global agent instance
realtime_agent = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI."""
    global realtime_agent
    # Startup
    realtime_agent = AgenticRealTimeDataAgent()
    logger.info("Real-Time Data Hub Agent started")
    yield
    # Shutdown
    logger.info("Real-Time Data Hub Agent shutting down")

# FastAPI application
app = FastAPI(title="Real-Time Data Hub", version="1.0.0", lifespan=lifespan)



# Pydantic models for API requests
class ConnectionRequest(BaseModel):
    exchange_name: str
    symbols: Optional[List[str]] = None

class SubscriptionRequest(BaseModel):
    exchange_name: str
    channel: str
    symbol: str

class DataRequest(BaseModel):
    symbol: str
    data_type: Optional[str] = None

class DisconnectRequest(BaseModel):
    exchange_name: str

# API endpoints
@app.post("/connect")
async def connect_to_exchange(request: ConnectionRequest):
    """Connect to an exchange WebSocket."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await realtime_agent.tools.connect_to_exchange(
        request.exchange_name, 
        request.symbols
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.post("/subscribe")
async def subscribe_to_channel(request: SubscriptionRequest):
    """Subscribe to a WebSocket channel."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await realtime_agent.tools.subscribe_to_channel(
        request.exchange_name,
        request.channel,
        request.symbol
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.post("/data")
async def get_latest_data(request: DataRequest):
    """Get latest market data."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await realtime_agent.tools.get_latest_data(
        request.symbol,
        request.data_type
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.get("/quality")
async def get_data_quality():
    """Get data quality metrics."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return await realtime_agent.tools.get_data_quality()

@app.get("/connections")
async def list_connections():
    """List all active connections."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return await realtime_agent.tools.list_connections()

@app.get("/connections/status")
async def get_connection_status():
    """Get detailed connection status including timestamps and timeouts."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        connections_info = {}
        current_time = time.time()
        
        for connection_key, timestamp in realtime_agent.websocket_manager.connection_timestamps.items():
            age_hours = (current_time - timestamp) / 3600
            remaining_hours = 24 - age_hours
            
            connections_info[connection_key] = {
                "connected_since": datetime.fromtimestamp(timestamp).isoformat(),
                "age_hours": round(age_hours, 2),
                "remaining_hours": round(remaining_hours, 2),
                "needs_reconnect": remaining_hours < 1,  # Reconnect if less than 1 hour remaining
                "status": "active" if connection_key in realtime_agent.websocket_manager.connections else "disconnected"
            }
        
        return {
            "status": "success",
            "connections": connections_info,
            "total_connections": len(connections_info),
            "connections_needing_reconnect": len([c for c in connections_info.values() if c["needs_reconnect"]])
        }
        
    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/disconnect")
async def disconnect_from_exchange(request: DisconnectRequest):
    """Disconnect from an exchange."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    result = await realtime_agent.tools.disconnect_from_exchange(
        request.exchange_name
    )
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    
    return result

@app.get("/summary")
async def get_market_summary(symbols: str = None):
    """Get market summary."""
    if not realtime_agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    symbol_list = symbols.split(',') if symbols else None
    return await realtime_agent.tools.get_market_summary(symbol_list)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check infrastructure connectivity
        connectivity = {}
        
        # Check database connectivity
        try:
            if realtime_agent and hasattr(realtime_agent, 'db_client') and realtime_agent.db_client:
                connectivity["database"] = {"status": "connected"}
            else:
                connectivity["database"] = {"status": "disconnected"}
        except Exception as e:
            connectivity["database"] = {"status": "error", "error": str(e)}
        
        # Check vault connectivity
        try:
            if realtime_agent and hasattr(realtime_agent, 'vault_client') and realtime_agent.vault_client:
                connectivity["vault"] = {"status": "connected"}
            else:
                connectivity["vault"] = {"status": "disconnected"}
        except Exception as e:
            connectivity["vault"] = {"status": "error", "error": str(e)}
        
        # Check websocket connectivity
        try:
            if realtime_agent and hasattr(realtime_agent, 'ws_client') and realtime_agent.ws_client and realtime_agent.ws_client.connected:
                connectivity["websocket"] = {"status": "connected"}
            else:
                connectivity["websocket"] = {"status": "disconnected"}
        except Exception as e:
            connectivity["websocket"] = {"status": "error", "error": str(e)}
        
        # Check exchange connections
        exchange_connections = 0
        if realtime_agent and realtime_agent.websocket_manager:
            exchange_connections = len(realtime_agent.websocket_manager.connections)
        
        return {
            "status": "healthy",
            "agent": "RealTimeDataAgent",
            "timestamp": datetime.utcnow().isoformat(),
            "connectivity": connectivity,
            "exchange_connections": exchange_connections
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "RealTimeDataAgent",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8026) 