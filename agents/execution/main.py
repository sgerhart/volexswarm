"""
VolexSwarm Execution Agent - Order Execution and Trade Management
Handles order placement, position tracking, and trade execution with CCXT integration.
"""

import sys
import os
import logging
import asyncio
import ccxt
import ccxt.async_support as ccxt_async
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import time
import json

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_exchange_credentials, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.models import Trade, Order
from common.websocket_client import AgentWebSocketClient, MessageType

# Initialize structured logger
logger = get_logger("execution")

app = FastAPI(title="VolexSwarm Execution Agent", version="1.0.0")

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
ws_client = None  # WebSocket client for real-time communication
exchanges = {}  # Exchange instances
dry_run_mode = True  # Default to dry run for safety


class OrderRequest(BaseModel):
    """Request model for order placement."""
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str = 'market'  # 'market', 'limit', 'stop'
    amount: Optional[float] = None
    price: Optional[float] = None
    stop_price: Optional[float] = None
    exchange: str = 'binanceus'  # Default to Binance.US for US compliance


class PositionResponse(BaseModel):
    """Response model for position information."""
    symbol: str
    side: str
    amount: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    timestamp: datetime


class OrderResponse(BaseModel):
    """Response model for order information."""
    id: str
    symbol: str
    side: str
    order_type: str
    amount: float
    price: Optional[float]
    status: str
    filled: float
    remaining: float
    cost: float
    timestamp: datetime
    exchange: str


class ExchangeManager:
    """Manages exchange connections and operations."""
    
    def __init__(self):
        self.exchanges = {}
        self.rate_limits = {}
        self.last_request_time = {}
        
    async def initialize_exchanges(self):
        """Initialize exchange connections."""
        try:
            # Get exchange credentials from Vault
            exchanges_config = get_agent_config("execution")
            enabled_exchanges = exchanges_config.get("enabled_exchanges", ["binanceus"])
            
            for exchange_name in enabled_exchanges:
                try:
                    credentials = get_exchange_credentials(exchange_name)
                    if not credentials:
                        logger.warning(f"No credentials found for {exchange_name}")
                        continue
                    
                    # Initialize exchange
                    exchange_class = getattr(ccxt_async, exchange_name)
                    exchange = exchange_class({
                        'apiKey': credentials.get('api_key'),
                        'secret': credentials.get('secret_key'),
                        'sandbox': dry_run_mode,  # Use sandbox in dry run mode
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'spot',  # Default to spot trading
                        }
                    })
                    
                    # Test connection
                    await exchange.load_markets()
                    logger.info(f"Successfully connected to {exchange_name}")
                    
                    self.exchanges[exchange_name] = exchange
                    self.rate_limits[exchange_name] = exchange.rateLimit
                    self.last_request_time[exchange_name] = 0
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {exchange_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize exchanges: {str(e)}")
    
    async def close_exchanges(self):
        """Close all exchange connections."""
        for exchange_name, exchange in self.exchanges.items():
            try:
                await exchange.close()
                logger.info(f"Closed connection to {exchange_name}")
            except Exception as e:
                logger.error(f"Error closing {exchange_name}: {str(e)}")
    
    async def get_balance(self, exchange_name: str, currency: str = 'USDT') -> Dict[str, Any]:
        """Get account balance for a specific currency."""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise HTTPException(status_code=400, detail=f"Exchange {exchange_name} not available")
            
            balance = await exchange.fetch_balance()
            return {
                'currency': currency,
                'free': balance.get(currency, {}).get('free', 0),
                'used': balance.get(currency, {}).get('used', 0),
                'total': balance.get(currency, {}).get('total', 0)
            }
        except Exception as e:
            logger.error(f"Error fetching balance from {exchange_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch balance: {str(e)}")
    
    async def get_ticker(self, exchange_name: str, symbol: str) -> Dict[str, Any]:
        """Get current ticker for a symbol."""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise HTTPException(status_code=400, detail=f"Exchange {exchange_name} not available")
            
            ticker = await exchange.fetch_ticker(symbol)
            return {
                'symbol': symbol,
                'last': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['baseVolume'],
                'timestamp': datetime.fromtimestamp(ticker['timestamp'] / 1000)
            }
        except Exception as e:
            logger.error(f"Error fetching ticker from {exchange_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch ticker: {str(e)}")
    
    async def place_order(self, exchange_name: str, order_request: OrderRequest) -> Dict[str, Any]:
        """Place an order on the exchange."""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise HTTPException(status_code=400, detail=f"Exchange {exchange_name} not available")
            
            # Validate order parameters
            if order_request.order_type == 'limit' and not order_request.price:
                raise HTTPException(status_code=400, detail="Price required for limit orders")
            
            if order_request.order_type == 'stop' and not order_request.stop_price:
                raise HTTPException(status_code=400, detail="Stop price required for stop orders")
            
            # Prepare order parameters
            order_params = {
                'symbol': order_request.symbol,
                'type': order_request.order_type,
                'side': order_request.side,
            }
            
            if order_request.amount:
                order_params['amount'] = order_request.amount
            
            if order_request.price:
                order_params['price'] = order_request.price
            
            if order_request.stop_price:
                order_params['stopPrice'] = order_request.stop_price
            
            # Place order
            if dry_run_mode:
                # Simulate order placement in dry run mode
                logger.info(f"DRY RUN: Would place order: {order_params}")
                return {
                    'id': f"dry_run_{int(time.time())}",
                    'symbol': order_request.symbol,
                    'side': order_request.side,
                    'type': order_request.order_type,
                    'amount': order_request.amount,
                    'price': order_request.price,
                    'status': 'closed',
                    'filled': order_request.amount or 0,
                    'remaining': 0,
                    'cost': (order_request.amount or 0) * (order_request.price or 0),
                    'timestamp': datetime.now(),
                    'exchange': exchange_name,
                    'dry_run': True
                }
            else:
                order = await exchange.create_order(**order_params)
                return {
                    'id': order['id'],
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'type': order['type'],
                    'amount': order['amount'],
                    'price': order.get('price'),
                    'status': order['status'],
                    'filled': order.get('filled', 0),
                    'remaining': order.get('remaining', 0),
                    'cost': order.get('cost', 0),
                    'timestamp': datetime.fromtimestamp(order['timestamp'] / 1000),
                    'exchange': exchange_name,
                    'dry_run': False
                }
                
        except Exception as e:
            logger.error(f"Error placing order on {exchange_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to place order: {str(e)}")
    
    async def get_positions(self, exchange_name: str) -> List[Dict[str, Any]]:
        """Get current positions."""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise HTTPException(status_code=400, detail=f"Exchange {exchange_name} not available")
            
            # Get balance to find positions
            balance = await exchange.fetch_balance()
            positions = []
            
            for currency, balance_info in balance.items():
                if balance_info['total'] > 0 and currency != 'USDT':
                    # Get current price for PnL calculation
                    try:
                        ticker = await exchange.fetch_ticker(f"{currency}/USDT")
                        current_price = ticker['last']
                        
                        positions.append({
                            'symbol': f"{currency}/USDT",
                            'side': 'long' if balance_info['total'] > 0 else 'short',
                            'amount': balance_info['total'],
                            'entry_price': 0,  # Would need to track from trade history
                            'current_price': current_price,
                            'unrealized_pnl': 0,  # Would need to calculate from entry
                            'realized_pnl': 0,
                            'timestamp': datetime.now()
                        })
                    except:
                        # Skip if we can't get price for this currency
                        continue
            
            return positions
            
        except Exception as e:
            logger.error(f"Error fetching positions from {exchange_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {str(e)}")
    
    async def get_order_history(self, exchange_name: str, symbol: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise HTTPException(status_code=400, detail=f"Exchange {exchange_name} not available")
            
            orders = await exchange.fetch_orders(symbol, limit=limit)
            
            return [{
                'id': order['id'],
                'symbol': order['symbol'],
                'side': order['side'],
                'type': order['type'],
                'amount': order['amount'],
                'price': order.get('price'),
                'status': order['status'],
                'filled': order.get('filled', 0),
                'remaining': order.get('remaining', 0),
                'cost': order.get('cost', 0),
                'timestamp': datetime.fromtimestamp(order['timestamp'] / 1000),
                'exchange': exchange_name
            } for order in orders]
            
        except Exception as e:
            logger.error(f"Error fetching order history from {exchange_name}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch order history: {str(e)}")


# Global exchange manager
exchange_manager = ExchangeManager()


async def health_monitor_loop():
    """Background task to send periodic health updates to Meta Agent."""
    while True:
        try:
            if ws_client and ws_client.is_connected:
                # Gather health metrics
                health_data = {
                    "status": "healthy",
                    "dry_run_mode": dry_run_mode,
                    "db_connected": db_client is not None,
                    "vault_connected": vault_client is not None,
                    "exchange_count": len(exchanges),
                    "last_health_check": datetime.utcnow().isoformat()
                }
                
                await ws_client.send_health_update(health_data)
                logger.debug("Sent health update to Meta Agent")
            
            # Wait 30 seconds before next health update
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Health monitor error: {e}")
            await asyncio.sleep(30)  # Continue monitoring even if there's an error


@app.on_event("startup")
async def startup_event():
    """Initialize the execution agent on startup."""
    global vault_client, db_client, ws_client, dry_run_mode
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized")
        
        # Initialize WebSocket client for real-time communication
        ws_client = AgentWebSocketClient("execution")
        await ws_client.connect()
        logger.info("WebSocket client connected to Meta Agent")
        
        # Load agent configuration
        config = get_agent_config("execution")
        if config is None:
            # Fallback configuration if not found in Vault
            config = {
                "dry_run_mode": True,
                "default_exchange": "binanceus",
                "max_order_size": 100.0,
                "risk_limit": 0.02
            }
            logger.warning("No configuration found in Vault, using fallback configuration")
        
        dry_run_mode = config.get("dry_run_mode", True)
        logger.info(f"Execution agent started in {'DRY RUN' if dry_run_mode else 'LIVE'} mode")
        
        # Initialize exchanges
        await exchange_manager.initialize_exchanges()
        logger.info("Exchange connections initialized")
        
        # Start health monitoring background task
        asyncio.create_task(health_monitor_loop())
        
    except Exception as e:
        logger.error(f"Failed to initialize execution agent: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    try:
        await exchange_manager.close_exchanges()
        logger.info("Execution agent shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Check Vault connection
        vault_health = vault_client.health_check() if vault_client else False
        
        # Check database connection
        db_health = db_health_check() if db_client else False
        
        # Check exchange connections
        exchange_health = len(exchange_manager.exchanges) > 0
        
        return {
            "status": "healthy" if all([vault_health, db_health, exchange_health]) else "unhealthy",
            "timestamp": datetime.now(),
            "components": {
                "vault": vault_health,
                "database": db_health,
                "exchanges": exchange_health,
                "dry_run_mode": dry_run_mode
            },
            "exchanges": list(exchange_manager.exchanges.keys())
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }


@app.get("/balance/{exchange_name}")
async def get_balance(exchange_name: str, currency: str = 'USDT'):
    """Get account balance for a specific exchange and currency."""
    return await exchange_manager.get_balance(exchange_name, currency)


@app.get("/ticker/{exchange_name}/{symbol}")
async def get_ticker(exchange_name: str, symbol: str):
    """Get current ticker for a symbol."""
    return await exchange_manager.get_ticker(exchange_name, symbol)


@app.post("/orders")
async def place_order(order_request: OrderRequest):
    """Place an order on the specified exchange."""
    order_result = await exchange_manager.place_order(order_request.exchange, order_request)
    
    # Log the order
    logger.info(f"Order placed: {order_result}")
    
    # Store in database if not dry run
    if not dry_run_mode and db_client:
        try:
            # Store order
            order = Order(
                order_id=order_result['id'],
                symbol=order_result['symbol'],
                side=order_result['side'],
                order_type=order_result['type'],
                quantity=order_result['amount'],
                price=order_result['price'],
                status=order_result['status'],
                filled_quantity=order_result['filled'],
                remaining_quantity=order_result['remaining'],
                cost=order_result['cost'],
                created_at=order_result['timestamp']
            )
            db_client.add(order)
            
            # Store trade if order is filled
            if order_result['status'] == 'closed' or order_result['filled'] > 0:
                trade = Trade(
                    symbol=order_result['symbol'],
                    side=order_result['side'],
                    quantity=order_result['amount'],
                    price=order_result['price'],
                    executed_at=order_result['timestamp'],
                    trade_id=order_result['id'],
                    order_id=order_result['id'],
                    exchange=order_result['exchange'],
                    order_type=order_result['type'],
                    status=order_result['status']
                )
                db_client.add(trade)
            
            db_client.commit()
        except Exception as e:
            logger.error(f"Failed to store order/trade in database: {str(e)}")
    
    # Broadcast trade update via WebSocket
    if ws_client and ws_client.is_connected:
        trade_data = {
            "order_id": order_result['id'],
            "symbol": order_result['symbol'],
            "side": order_result['side'],
            "quantity": order_result['amount'],
            "price": order_result['price'],
            "status": order_result['status'],
            "filled": order_result['filled'],
            "cost": order_result['cost'],
            "timestamp": order_result['timestamp'],
            "exchange": order_request.exchange,
            "dry_run": dry_run_mode
        }
        asyncio.create_task(ws_client.send_trade_update(trade_data))
        logger.debug(f"Broadcasted trade update for {order_result['symbol']} via WebSocket")
    
    return order_result


@app.get("/positions/{exchange_name}")
async def get_positions(exchange_name: str):
    """Get current positions for an exchange."""
    return await exchange_manager.get_positions(exchange_name)


@app.get("/orders/{exchange_name}")
async def get_order_history(exchange_name: str, symbol: Optional[str] = None, limit: int = 100):
    """Get order history for an exchange."""
    return await exchange_manager.get_order_history(exchange_name, symbol, limit)


@app.get("/exchanges")
def get_available_exchanges():
    """Get list of available exchanges."""
    return {
        "available_exchanges": list(exchange_manager.exchanges.keys()),
        "dry_run_mode": dry_run_mode
    }


@app.get("/exchanges/{exchange_name}/status")
async def get_exchange_status(exchange_name: str):
    """Get status of a specific exchange."""
    try:
        exchange = exchange_manager.exchanges.get(exchange_name)
        if not exchange:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange_name} not found")
        
        # Test connection by fetching markets
        await exchange.load_markets()
        
        return {
            "exchange": exchange_name,
            "status": "connected",
            "timestamp": datetime.now(),
            "markets_count": len(exchange.markets)
        }
    except Exception as e:
        return {
            "exchange": exchange_name,
            "status": "disconnected",
            "timestamp": datetime.now(),
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
