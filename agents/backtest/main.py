"""
VolexSwarm Backtest Agent - Historical Strategy Testing and Optimization
Handles backtesting, performance analysis, and strategy optimization.
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
import pandas as pd
import numpy as np
from dataclasses import dataclass
import json
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.websocket_client import AgentWebSocketClient, MessageType
from common.logging import get_logger
from common.models import Backtest, Strategy, Trade, PriceData, PerformanceMetrics

# Initialize structured logger
logger = get_logger("backtest")

app = FastAPI(title="VolexSwarm Backtest Agent", version="1.0.0")

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
exchanges = {}  # Exchange instances for data fetching


class BacktestRequest(BaseModel):
    """Request model for backtest execution."""
    strategy_name: str
    symbols: List[str]
    start_date: str  # ISO format: YYYY-MM-DD
    end_date: str    # ISO format: YYYY-MM-DD
    initial_balance: float = 10000.0
    parameters: Optional[Dict[str, Any]] = None
    timeframe: str = "1h"


class BacktestResult(BaseModel):
    """Response model for backtest results."""
    backtest_id: int
    strategy_name: str
    symbols: List[str]
    start_date: str
    end_date: str
    initial_balance: float
    final_balance: float
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    average_win: float
    average_loss: float
    profit_factor: float
    status: str
    created_at: datetime


@dataclass
class TradeRecord:
    """Internal trade record for backtesting."""
    timestamp: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    price: float
    cost: float
    pnl: float = 0.0


@dataclass
class Position:
    """Internal position tracking for backtesting."""
    symbol: str
    quantity: float
    entry_price: float
    unrealized_pnl: float = 0.0


class BacktestEngine:
    """Core backtesting engine for strategy evaluation."""
    
    def __init__(self):
        self.positions = {}  # Current positions
        self.trades = []     # Trade history
        self.balance = 0.0   # Current balance
        self.initial_balance = 0.0
        self.equity_curve = []  # Portfolio value over time
        self.price_data = {}  # Historical price data
        
    def initialize(self, initial_balance: float):
        """Initialize the backtest engine."""
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        
    def load_price_data(self, symbol: str, start_date: str, end_date: str, timeframe: str = "1h") -> bool:
        """Load historical price data for a symbol."""
        try:
            # Convert dates
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            
            # Query database for price data
            if db_client:
                query = db_client.query(PriceData).filter(
                    PriceData.symbol == symbol,
                    PriceData.time >= start_dt,
                    PriceData.time <= end_dt,
                    PriceData.timeframe == timeframe
                ).order_by(PriceData.time)
                
                data = query.all()
                
                if data:
                    # Convert to pandas DataFrame
                    df = pd.DataFrame([{
                        'timestamp': row.time,
                        'open': row.open,
                        'high': row.high,
                        'low': row.low,
                        'close': row.close,
                        'volume': row.volume
                    } for row in data])
                    
                    self.price_data[symbol] = df
                    logger.info(f"Loaded {len(data)} price records for {symbol}")
                    return True
                else:
                    logger.warning(f"No price data found for {symbol}")
                    return False
            else:
                logger.error("Database client not available")
                return False
                
        except Exception as e:
            logger.error(f"Error loading price data for {symbol}: {str(e)}")
            return False
    
    def execute_trade(self, timestamp: datetime, symbol: str, side: str, quantity: float, price: float) -> bool:
        """Execute a trade in the backtest."""
        try:
            cost = quantity * price
            
            if side == 'buy':
                if cost > self.balance:
                    logger.warning(f"Insufficient balance for buy order: {cost} > {self.balance}")
                    return False
                
                # Update balance
                self.balance -= cost
                
                # Update position
                if symbol in self.positions:
                    # Add to existing position
                    pos = self.positions[symbol]
                    total_quantity = pos.quantity + quantity
                    total_cost = (pos.quantity * pos.entry_price) + cost
                    pos.entry_price = total_cost / total_quantity
                    pos.quantity = total_quantity
                else:
                    # Create new position
                    self.positions[symbol] = Position(symbol, quantity, price)
                    
            elif side == 'sell':
                if symbol not in self.positions or self.positions[symbol].quantity < quantity:
                    logger.warning(f"Insufficient position for sell order: {symbol}")
                    return False
                
                # Update balance
                self.balance += cost
                
                # Update position
                pos = self.positions[symbol]
                pos.quantity -= quantity
                
                # Calculate PnL
                pnl = (price - pos.entry_price) * quantity
                
                # Remove position if fully sold
                if pos.quantity <= 0:
                    del self.positions[symbol]
                
                # Record trade
                trade = TradeRecord(
                    timestamp=timestamp,
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
                    cost=cost,
                    pnl=pnl
                )
                self.trades.append(trade)
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return False
    
    def update_positions(self, timestamp: datetime, current_prices: Dict[str, float]):
        """Update unrealized PnL for current positions."""
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
    
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value."""
        portfolio_value = self.balance
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                portfolio_value += position.quantity * current_prices[symbol]
            else:
                # Use entry price if current price not available
                portfolio_value += position.quantity * position.entry_price
        
        return portfolio_value
    
    def run_backtest(self, strategy_func, symbols: List[str], start_date: str, end_date: str, 
                    timeframe: str = "1h", parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Run a complete backtest."""
        try:
            # Load price data for all symbols
            for symbol in symbols:
                if not self.load_price_data(symbol, start_date, end_date, timeframe):
                    raise Exception(f"Failed to load price data for {symbol}")
            
            # Get common time range
            all_timestamps = set()
            for symbol in symbols:
                if symbol in self.price_data:
                    all_timestamps.update(self.price_data[symbol]['timestamp'].tolist())
            
            timestamps = sorted(list(all_timestamps))
            
            # Initialize strategy
            if parameters:
                strategy_func.initialize(parameters)
            
            # Run backtest
            for timestamp in timestamps:
                # Get current prices
                current_prices = {}
                for symbol in symbols:
                    if symbol in self.price_data:
                        symbol_data = self.price_data[symbol]
                        current_data = symbol_data[symbol_data['timestamp'] == timestamp]
                        if not current_data.empty:
                            current_prices[symbol] = current_data.iloc[0]['close']
                
                # Update positions
                self.update_positions(timestamp, current_prices)
                
                # Get strategy signals
                signals = strategy_func.generate_signals(timestamp, current_prices, self.positions, self.balance)
                
                # Execute signals
                for signal in signals:
                    self.execute_trade(
                        timestamp=timestamp,
                        symbol=signal['symbol'],
                        side=signal['side'],
                        quantity=signal['quantity'],
                        price=current_prices.get(signal['symbol'], 0)
                    )
                
                # Record equity curve
                portfolio_value = self.calculate_portfolio_value(current_prices)
                self.equity_curve.append({
                    'timestamp': timestamp,
                    'portfolio_value': portfolio_value,
                    'balance': self.balance
                })
            
            # Calculate performance metrics
            metrics = self.calculate_performance_metrics()
            
            return {
                'trades': self.trades,
                'equity_curve': self.equity_curve,
                'final_balance': self.balance,
                'positions': self.positions,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Error running backtest: {str(e)}")
            raise
    
    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        try:
            if not self.equity_curve:
                return {}
            
            # Basic metrics
            initial_value = self.initial_balance
            final_value = self.equity_curve[-1]['portfolio_value']
            total_return = (final_value - initial_value) / initial_value
            
            # Calculate returns
            returns = []
            for i in range(1, len(self.equity_curve)):
                prev_value = self.equity_curve[i-1]['portfolio_value']
                curr_value = self.equity_curve[i]['portfolio_value']
                returns.append((curr_value - prev_value) / prev_value)
            
            # Sharpe ratio (assuming risk-free rate of 0)
            if returns:
                avg_return = np.mean(returns)
                std_return = np.std(returns)
                sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Maximum drawdown
            peak = initial_value
            max_drawdown = 0
            for point in self.equity_curve:
                value = point['portfolio_value']
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
            
            # Trade statistics
            winning_trades = [t for t in self.trades if t.pnl > 0]
            losing_trades = [t for t in self.trades if t.pnl < 0]
            
            win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
            total_trades = len(self.trades)
            
            avg_win = np.mean([t.pnl for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([abs(t.pnl) for t in losing_trades]) if losing_trades else 0
            
            profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf') if avg_win > 0 else 0
            
            return {
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'average_win': avg_win,
                'average_loss': avg_loss,
                'profit_factor': profit_factor,
                'final_balance': final_value,
                'initial_balance': initial_value
            }
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics: {str(e)}")
            return {}


class DataManager:
    """Manages historical data collection and storage."""
    
    def __init__(self):
        self.exchanges = {}
        
    async def initialize_exchanges(self):
        """Initialize exchange connections for data fetching."""
        try:
            # Get exchange credentials from Vault
            exchanges_config = get_agent_config("backtest")
            enabled_exchanges = exchanges_config.get("enabled_exchanges", ["binanceus"])
            
            for exchange_name in enabled_exchanges:
                try:
                    # Initialize exchange (read-only for data fetching)
                    exchange_class = getattr(ccxt_async, exchange_name)
                    exchange = exchange_class({
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'spot',
                        }
                    })
                    
                    await exchange.load_markets()
                    self.exchanges[exchange_name] = exchange
                    logger.info(f"Initialized {exchange_name} for data fetching")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize {exchange_name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Failed to initialize exchanges: {str(e)}")
    
    async def fetch_historical_data(self, exchange_name: str, symbol: str, timeframe: str, 
                                  start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch historical data from exchange."""
        try:
            exchange = self.exchanges.get(exchange_name)
            if not exchange:
                raise Exception(f"Exchange {exchange_name} not available")
            
            # Convert dates to timestamps
            start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
            end_ts = int(datetime.fromisoformat(end_date).timestamp() * 1000)
            
            # Fetch OHLCV data
            ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, start_ts, limit=1000)
            
            # Convert to our format
            data = []
            for candle in ohlcv:
                data.append({
                    'timestamp': datetime.fromtimestamp(candle[0] / 1000),
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            raise
    
    async def store_price_data(self, exchange_name: str, symbol: str, timeframe: str, data: List[Dict[str, Any]]):
        """Store price data in database."""
        try:
            if not db_client:
                logger.error("Database client not available")
                return
            
            for record in data:
                price_data = PriceData(
                    time=record['timestamp'],
                    symbol=symbol,
                    exchange=exchange_name,
                    open=record['open'],
                    high=record['high'],
                    low=record['low'],
                    close=record['close'],
                    volume=record['volume'],
                    timeframe=timeframe
                )
                db_client.add(price_data)
            
            db_client.commit()
            logger.info(f"Stored {len(data)} price records for {symbol}")
            
        except Exception as e:
            logger.error(f"Error storing price data: {str(e)}")
            db_client.rollback()


# Global instances
backtest_engine = BacktestEngine()
data_manager = DataManager()


async def health_monitor_loop():
    """Background task to send periodic health updates to Meta Agent."""
    while True:
        try:
            if ws_client and ws_client.is_connected:
                # Gather health metrics
                health_data = {
                    "status": "healthy",
                    "db_connected": db_client is not None,
                    "vault_connected": vault_client is not None,
                    "backtest_engine_active": True,
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
    """Initialize the backtest agent on startup."""
    global vault_client, db_client, ws_client
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized")
        
        # Initialize WebSocket client for real-time communication
        ws_client = AgentWebSocketClient("backtest")
        await ws_client.connect()
        logger.info("WebSocket client connected to Meta Agent")
        
        # Start health monitoring background task
        asyncio.create_task(health_monitor_loop())
        
        # Initialize data manager
        await data_manager.initialize_exchanges()
        logger.info("Backtest agent initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize backtest agent: {str(e)}")
        raise


@app.get("/health")
def health_check():
    """Health check endpoint."""
    try:
        # Check Vault connection
        vault_health = vault_client.health_check() if vault_client else False
        
        # Check database connection
        db_health = db_health_check() if db_client else False
        
        # Check exchange connections
        exchange_health = len(data_manager.exchanges) > 0
        
        return {
            "status": "healthy" if all([vault_health, db_health, exchange_health]) else "unhealthy",
            "timestamp": datetime.now(),
            "components": {
                "vault": vault_health,
                "database": db_health,
                "exchanges": exchange_health
            },
            "exchanges": list(data_manager.exchanges.keys())
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(),
            "error": str(e)
        }


@app.post("/backtest/run")
async def run_backtest(request: BacktestRequest):
    """Run a backtest for a strategy."""
    try:
        # Validate request
        if not request.symbols:
            raise HTTPException(status_code=400, detail="At least one symbol required")
        
        # Create backtest record
        backtest = Backtest(
            name=f"Backtest_{request.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_date=datetime.fromisoformat(request.start_date),
            end_date=datetime.fromisoformat(request.end_date),
            symbols=request.symbols,
            parameters=request.parameters or {},
            status="running"
        )
        
        if db_client:
            db_client.add(backtest)
            db_client.commit()
            backtest_id = backtest.id
        else:
            backtest_id = int(time.time())
        
        # Run backtest in background
        background_tasks.add_task(
            execute_backtest,
            backtest_id,
            request.strategy_name,
            request.symbols,
            request.start_date,
            request.end_date,
            request.initial_balance,
            request.parameters,
            request.timeframe
        )
        
        return {
            "backtest_id": backtest_id,
            "status": "started",
            "message": "Backtest started successfully"
        }
        
    except Exception as e:
        logger.error(f"Error starting backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def execute_backtest(backtest_id: int, strategy_name: str, symbols: List[str], 
                          start_date: str, end_date: str, initial_balance: float,
                          parameters: Dict[str, Any], timeframe: str):
    """Execute backtest in background."""
    try:
        # Initialize backtest engine
        backtest_engine.initialize(initial_balance)
        
        # For now, use a simple moving average strategy as example
        # In a real implementation, this would load the actual strategy
        class SimpleMAStrategy:
            def __init__(self):
                self.short_window = 10
                self.long_window = 30
                self.positions = {}
            
            def initialize(self, params):
                self.short_window = params.get('short_window', 10)
                self.long_window = params.get('long_window', 30)
            
            def generate_signals(self, timestamp, current_prices, positions, balance):
                signals = []
                # Simple moving average crossover logic
                # This is a placeholder - real implementation would be more sophisticated
                return signals
        
        strategy = SimpleMAStrategy()
        if parameters:
            strategy.initialize(parameters)
        
        # Run backtest
        results = backtest_engine.run_backtest(
            strategy, symbols, start_date, end_date, timeframe, parameters
        )
        
        # Store results
        if db_client:
            backtest = db_client.query(Backtest).filter(Backtest.id == backtest_id).first()
            if backtest:
                backtest.status = "completed"
                backtest.results = results['metrics']
                backtest.trades = [vars(trade) for trade in results['trades']]
                db_client.commit()
        
        logger.info(f"Backtest {backtest_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error executing backtest {backtest_id}: {str(e)}")
        if db_client:
            backtest = db_client.query(Backtest).filter(Backtest.id == backtest_id).first()
            if backtest:
                backtest.status = "failed"
                db_client.commit()


@app.get("/backtest/{backtest_id}")
async def get_backtest_results(backtest_id: int):
    """Get backtest results."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        backtest = db_client.query(Backtest).filter(Backtest.id == backtest_id).first()
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        return {
            "backtest_id": backtest.id,
            "strategy_name": backtest.name,
            "symbols": backtest.symbols,
            "start_date": backtest.start_date.isoformat(),
            "end_date": backtest.end_date.isoformat(),
            "parameters": backtest.parameters,
            "results": backtest.results,
            "status": backtest.status,
            "created_at": backtest.created_at
        }
        
    except Exception as e:
        logger.error(f"Error getting backtest results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/list")
async def list_backtests(limit: int = 50):
    """List recent backtests."""
    try:
        if not db_client:
            raise HTTPException(status_code=500, detail="Database not available")
        
        backtests = db_client.query(Backtest).order_by(Backtest.created_at.desc()).limit(limit).all()
        
        return [{
            "backtest_id": bt.id,
            "name": bt.name,
            "symbols": bt.symbols,
            "start_date": bt.start_date.isoformat(),
            "end_date": bt.end_date.isoformat(),
            "status": bt.status,
            "created_at": bt.created_at
        } for bt in backtests]
        
    except Exception as e:
        logger.error(f"Error listing backtests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/data/fetch")
async def fetch_historical_data(exchange: str, symbol: str, timeframe: str = "1h", 
                               start_date: str = None, end_date: str = None):
    """Fetch and store historical data."""
    try:
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()
        
        # Fetch data
        data = await data_manager.fetch_historical_data(exchange, symbol, timeframe, start_date, end_date)
        
        # Store data
        await data_manager.store_price_data(exchange, symbol, timeframe, data)
        
        return {
            "message": f"Successfully fetched {len(data)} records for {symbol}",
            "symbol": symbol,
            "exchange": exchange,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "records_count": len(data)
        }
        
    except Exception as e:
        logger.error(f"Error fetching historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/symbols/{exchange}")
async def get_available_symbols(exchange: str):
    """Get available symbols for an exchange."""
    try:
        exchange_instance = data_manager.exchanges.get(exchange)
        if not exchange_instance:
            raise HTTPException(status_code=404, detail=f"Exchange {exchange} not found")
        
        markets = exchange_instance.markets
        symbols = [market for market in markets.keys() if '/USDT' in market]
        
        return {
            "exchange": exchange,
            "symbols": symbols[:100],  # Limit to first 100
            "total_count": len(symbols)
        }
        
    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
