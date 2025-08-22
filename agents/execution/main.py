"""
VolexSwarm Agentic Execution Agent - Main Entry Point
Transforms the FastAPI execution agent into an intelligent AutoGen AssistantAgent
with autonomous trade execution and order management capabilities.
"""

import sys
import os
import asyncio
import signal
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from contextlib import asynccontextmanager

# Add the project root to the path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/agents/execution')

from agentic_execution_agent import AgenticExecutionAgent
from common.logging import get_logger

logger = get_logger("agentic_execution_main")

# Global service instance
execution_service = None
start_time = None

async def scheduled_portfolio_collection():
    """Background task that collects portfolio snapshots at regular intervals."""
    while True:
        try:
            if execution_service and execution_service.agent:
                logger.info("🕐 Scheduled portfolio collection triggered")
                await execution_service.agent.store_current_portfolio_snapshot()
            else:
                logger.warning("Portfolio collection skipped - service not ready")
            
            # Wait 15 minutes (900 seconds) before next collection
            await asyncio.sleep(900)
            
        except asyncio.CancelledError:
            logger.info("Portfolio collection task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in scheduled portfolio collection: {e}")
            # Wait 5 minutes before retrying on error
            await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global execution_service, start_time
    start_time = datetime.now()
    execution_service = AgenticExecutionService()
    await execution_service.start()
    
    # Start portfolio collection scheduler
    portfolio_task = asyncio.create_task(scheduled_portfolio_collection())
    
    yield
    
    # Shutdown
    if portfolio_task:
        portfolio_task.cancel()
        try:
            await portfolio_task
        except asyncio.CancelledError:
            pass
    
    if execution_service:
        await execution_service.stop()

# Create FastAPI app
app = FastAPI(title="VolexSwarm Execution Agent", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for the Execution Agent."""
    from fastapi.responses import JSONResponse
    global execution_service
    try:
        if execution_service and execution_service.running:
            # Calculate actual uptime
            uptime_str = "0h 0m"
            if 'start_time' in globals() and start_time:
                uptime_delta = datetime.now() - start_time
                hours = int(uptime_delta.total_seconds() // 3600)
                minutes = int((uptime_delta.total_seconds() % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            
            # Get real metrics from the agent
            metrics = {}
            if execution_service.agent:
                # Get database connectivity
                try:
                    if hasattr(execution_service.agent, 'db_client') and execution_service.agent.db_client:
                        metrics["database"] = {"status": "connected"}
                    else:
                        metrics["database"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["database"] = {"status": "error", "error": str(e)}
                
                # Get vault connectivity  
                try:
                    if hasattr(execution_service.agent, 'vault_client') and execution_service.agent.vault_client:
                        metrics["vault"] = {"status": "connected"}
                    else:
                        metrics["vault"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["vault"] = {"status": "error", "error": str(e)}
                
                # Get websocket connectivity
                try:
                    if hasattr(execution_service.agent, 'ws_client') and execution_service.agent.ws_client:
                        # Check if websocket is connected
                        if hasattr(execution_service.agent.ws_client, 'connected') and execution_service.agent.ws_client.connected:
                            metrics["websocket"] = {"status": "connected"}
                        else:
                            metrics["websocket"] = {"status": "disconnected"}
                    else:
                        metrics["websocket"] = {"status": "not_initialized"}
                except Exception as e:
                    metrics["websocket"] = {"status": "error", "error": str(e)}
                
                # Get trade execution metrics
                try:
                    if hasattr(execution_service.agent, 'db_client') and execution_service.agent.db_client:
                        trade_count = await execution_service.agent.db_client.fetch(
                            "SELECT COUNT(*) as count FROM trades WHERE created_at > NOW() - INTERVAL '24 hours'"
                        )
                        metrics["trades_24h"] = trade_count[0]['count'] if trade_count else 0
                except Exception:
                    metrics["trades_24h"] = 0
            
            response_data = {
                "status": "healthy",
                "agent": "execution",
                "timestamp": datetime.now().isoformat(),
                "uptime": uptime_str,
                "connectivity": metrics
            }
        else:
            response_data = {
                "status": "unhealthy",
                "agent": "execution",
                "timestamp": datetime.now().isoformat(),
                "error": "Service not running"
            }
    except Exception as e:
        response_data = {
            "status": "unhealthy",
            "agent": "execution",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }
    
    return JSONResponse(content=response_data)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Execution Agent", "status": "running"}

@app.get("/api/execution/portfolio")
async def get_portfolio():
    """Get current portfolio status and positions."""
    global execution_service
    try:
        if execution_service and execution_service.agent:
            portfolio_data = await execution_service.agent.get_portfolio_status()
            return portfolio_data
        else:
            return {"error": "Service not running"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/execution/positions")
async def get_positions():
    """Get current positions with P&L."""
    global execution_service
    try:
        if execution_service and execution_service.agent:
            positions = await execution_service.agent.get_real_time_positions()
            return {"positions": positions, "timestamp": datetime.now().isoformat()}
        else:
            return {"error": "Service not running"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/execution/pnl")
async def get_portfolio_pnl():
    """Get portfolio P&L information."""
    global execution_service
    try:
        if execution_service and execution_service.agent:
            pnl_data = await execution_service.agent.get_portfolio_pnl()
            return pnl_data
        else:
            return {"error": "Service not running"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/execution/trades")
async def get_recent_trades(limit: int = 50):
    """Get recent trades from the database."""
    global execution_service
    try:
        if execution_service and execution_service.agent:
            # Query trades from database
            query = """
                SELECT 
                    t.symbol, t.side, t.quantity, t.price, t.executed_at,
                    t.fees, t.fees_currency, t.trade_metadata
                FROM trades t
                ORDER BY t.executed_at DESC
                LIMIT $1
            """
            trades = await execution_service.agent.db_client.fetch(query, limit)
            return {"trades": trades, "count": len(trades), "timestamp": datetime.now().isoformat()}
        else:
            return {"error": "Service not running"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/execution/performance")
async def get_performance():
    """Get execution performance metrics."""
    try:
        if execution_service and execution_service.agent:
            performance_data = await execution_service.agent.get_portfolio_performance()
            return performance_data
        else:
            return {"error": "Performance metrics not available"}
    except Exception as e:
        if execution_service and execution_service.agent:
            return {"error": str(e)}
        else:
            return {"error": "Service not running"}

@app.get("/api/execution/portfolio-performance")
async def get_portfolio_performance():
    """Get comprehensive portfolio performance including total return."""
    try:
        if execution_service and execution_service.agent:
            performance_data = await execution_service.agent.get_portfolio_performance()
            return performance_data
        else:
            return {"error": "Portfolio performance not available"}
    except Exception as e:
        if execution_service and execution_service.agent:
            return {"error": str(e)}
        else:
            return {"error": "Service not running"}


@app.get("/api/execution/portfolio-history")
async def get_portfolio_history(days: int = 30):
    """Get portfolio history data for charting."""
    try:
        if execution_service and execution_service.agent:
            # Get the history data (portfolio collection handled separately by scheduler)
            history_data = await execution_service.agent.get_portfolio_history("binance", days)
            return {
                "exchange": "binance",
                "days_requested": days,
                "data_points": history_data,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": "Portfolio history not available"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/execution/store-portfolio-snapshot")
async def store_portfolio_snapshot():
    """Manually trigger portfolio snapshot storage."""
    try:
        if execution_service and execution_service.agent:
            success = await execution_service.agent.store_current_portfolio_snapshot()
            return {
                "success": success,
                "message": "Portfolio snapshot stored successfully" if success else "Failed to store portfolio snapshot",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": "Execution service not available"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/execution/portfolio-collection-config")
async def get_portfolio_collection_config():
    """Get portfolio collection configuration."""
    try:
        from common.config_manager import config_manager
        config = await config_manager.get_portfolio_collection_config()
        return {
            "success": True,
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/execution/update-portfolio-collection-config")
async def update_portfolio_collection_config(updates: Dict[str, Any]):
    """Update portfolio collection configuration."""
    try:
        from common.config_manager import config_manager
        success = await config_manager.update_portfolio_collection_config(updates)
        return {
            "success": success,
            "message": "Portfolio collection config updated successfully" if success else "Failed to update config",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/execution/force-portfolio-snapshot")
async def force_portfolio_snapshot():
    """Force portfolio snapshot collection regardless of smart logic."""
    try:
        if execution_service and execution_service.agent:
            success = await execution_service.agent.store_current_portfolio_snapshot(force_collection=True)
            return {
                "success": success,
                "message": "Portfolio snapshot forced successfully" if success else "Failed to force portfolio snapshot",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": "Execution service not available"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/execution/place-order")
async def place_order(order_request: Dict[str, Any]):
    """Place a trading order."""
    try:
        if execution_service and execution_service.agent:
            # Extract order parameters
            symbol = order_request.get("symbol")
            side = order_request.get("side")  # "buy" or "sell"
            amount = order_request.get("amount")
            order_type = order_request.get("order_type", "market")
            price = order_request.get("price")
            exchange = order_request.get("exchange", "binance")
            
            # Validate required parameters
            if not all([symbol, side, amount]):
                return {"error": "Missing required parameters: symbol, side, amount"}
            
            # Execute the trade
            result = await execution_service.agent.execute_trade(
                symbol=symbol,
                side=side,
                amount=amount,
                order_type=order_type,
                price=price,
                exchange=exchange
            )
            
            # Check if the order was actually placed successfully
            # The WebSocket error doesn't mean the order failed
            order_successful = "error" not in result and "order_id" in result
            
            return {
                "success": order_successful,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "message": "Order placed successfully" if order_successful else "Order placement failed"
            }
        else:
            return {"error": "Execution service not available"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/execution/place-order-real-time")
async def place_order_real_time(order_request: Dict[str, Any]):
    """Place a real-time trading order with priority."""
    try:
        if execution_service and execution_service.agent:
            # Extract order parameters
            symbol = order_request.get("symbol")
            side = order_request.get("side")  # "buy" or "sell"
            amount = order_request.get("amount")
            priority = order_request.get("priority", "normal")
            exchange = order_request.get("exchange", "binance")
            
            # Validate required parameters
            if not all([symbol, side, amount]):
                return {"error": "Missing required parameters: symbol, side, amount"}
            
            # Execute the real-time trade
            result = await execution_service.agent.execute_trade_real_time(
                symbol=symbol,
                side=side,
                amount=amount,
                priority=priority,
                exchange=exchange
            )
            
            return {
                "success": "error" not in result,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"error": "Execution service not available"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/execution/order-status/{order_id}")
async def get_order_status(order_id: str):
    """Get the status of a specific order."""
    try:
        if execution_service and execution_service.agent:
            # For now, return simulated order status
            # TODO: Implement real order status checking
            return {
                "order_id": order_id,
                "status": "filled",
                "symbol": "BTC/USDT",
                "side": "buy",
                "amount": 0.001,
                "timestamp": datetime.now().isoformat(),
                "message": "Order status retrieved successfully"
            }
        else:
            return {"error": "Execution service not available"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/execution/trading-config")
async def get_trading_config():
    """Get current trading configuration and mode."""
    try:
        from common.config_manager import config_manager
        config = await config_manager.load_trading_config()
        
        return {
            "trading_mode": config.mode.value,
            "simulation_balance": config.simulation_balance,
            "max_simulation_risk": config.max_simulation_risk,
            "real_trading_enabled": config.real_trading_enabled,
            "simulation_accounts": config.simulation_accounts,
            "real_accounts": config.real_accounts,
            "safety_checks_enabled": config.safety_checks_enabled,
            "max_position_size": config.max_position_size,
            "emergency_stop_enabled": config.emergency_stop_enabled,
            # Portfolio Collection Settings
            "portfolio_collection_enabled": config.portfolio_collection_enabled,
            "collection_frequency_minutes": config.collection_frequency_minutes,
            "change_threshold_percent": config.change_threshold_percent,
            "max_collections_per_hour": config.max_collections_per_hour,
            "data_retention_days": config.data_retention_days,
            "enable_compression": config.enable_compression,
            # Risk Management Settings
            "max_portfolio_risk": config.max_portfolio_risk,
            "max_drawdown": config.max_drawdown,
            "daily_loss_limit": config.daily_loss_limit,
            "weekly_loss_limit": config.weekly_loss_limit,
            "monthly_loss_limit": config.monthly_loss_limit,
            "max_single_position_size": config.max_single_position_size,
            "max_sector_exposure": config.max_sector_exposure,
            "correlation_limit": config.correlation_limit,
            "leverage_limit": config.leverage_limit,
            "default_stop_loss": config.default_stop_loss,
            "default_take_profit": config.default_take_profit,
            "trailing_stop_enabled": config.trailing_stop_enabled,
            "trailing_stop_distance": config.trailing_stop_distance,
            "is_simulation": await config_manager.is_simulation_mode(),
            "is_real_trading_enabled": await config_manager.is_real_trading_enabled(),
            "is_hybrid": await config_manager.is_hybrid_mode()
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/execution/update-config")
async def update_trading_config(config_update: Dict[str, Any]):
    """Update trading configuration settings."""
    try:
        from common.config_manager import config_manager
        
        # Validate required fields
        required_fields = ['simulation_balance', 'max_simulation_risk', 'max_position_size']
        for field in required_fields:
            if field not in config_update:
                return {"error": f"Missing required field: {field}"}
        
        # Validate numeric values
        try:
            simulation_balance = float(config_update['simulation_balance'])
            max_risk = float(config_update['max_simulation_risk'])
            max_position = float(config_update['max_position_size'])
            
            if simulation_balance <= 0:
                return {"error": "Simulation balance must be positive"}
            if max_risk < 0 or max_risk > 1:
                return {"error": "Max risk must be between 0 and 1 (0-100%)"}
            if max_position < 0 or max_position > 1:
                return {"error": "Max position size must be between 0 and 1 (0-100%)"}
                
        except (ValueError, TypeError):
            return {"error": "Invalid numeric values in configuration"}
        
        # Prepare updates
        updates = {
            'simulation_balance': simulation_balance,
            'max_simulation_risk': max_risk,
            'max_position_size': max_position,
            'safety_checks_enabled': config_update.get('safety_checks_enabled', True),
            'emergency_stop_enabled': config_update.get('emergency_stop_enabled', True),
            # Portfolio Collection Settings
            'portfolio_collection_enabled': config_update.get('portfolio_collection_enabled', True),
            'collection_frequency_minutes': config_update.get('collection_frequency_minutes', 15),
            'change_threshold_percent': config_update.get('change_threshold_percent', 2.0),
            'max_collections_per_hour': config_update.get('max_collections_per_hour', 60),
            'data_retention_days': config_update.get('data_retention_days', 30),
            'enable_compression': config_update.get('enable_compression', True),
            # Risk Management Settings
            'max_portfolio_risk': config_update.get('max_portfolio_risk', 0.05),
            'max_drawdown': config_update.get('max_drawdown', 0.10),
            'daily_loss_limit': config_update.get('daily_loss_limit', 1000),
            'weekly_loss_limit': config_update.get('weekly_loss_limit', 5000),
            'monthly_loss_limit': config_update.get('monthly_loss_limit', 20000),
            'max_single_position_size': config_update.get('max_single_position_size', 0.20),
            'max_sector_exposure': config_update.get('max_sector_exposure', 0.30),
            'correlation_limit': config_update.get('correlation_limit', 0.70),
            'leverage_limit': config_update.get('leverage_limit', 1.0),
            'default_stop_loss': config_update.get('default_stop_loss', 0.05),
            'default_take_profit': config_update.get('default_take_profit', 0.15),
            'trailing_stop_enabled': config_update.get('trailing_stop_enabled', True),
            'trailing_stop_distance': config_update.get('trailing_stop_distance', 0.03)
        }
        
        # Update configuration
        success = await config_manager.update_trading_config(updates)
        
        if success:
            # Reload configuration
            new_config = await config_manager.load_trading_config()
            
            return {
                "success": True,
                "message": "Trading configuration updated successfully",
                "config": {
                    "mode": new_config.mode.value,
                    "simulation_balance": new_config.simulation_balance,
                    "max_simulation_risk": new_config.max_simulation_risk,
                    "real_trading_enabled": new_config.real_trading_enabled,
                    "simulation_accounts": new_config.simulation_accounts,
                    "real_accounts": new_config.real_accounts,
                    "safety_checks_enabled": new_config.safety_checks_enabled,
                    "max_position_size": new_config.max_position_size,
                    "emergency_stop_enabled": new_config.emergency_stop_enabled,
                    # Portfolio Collection Settings
                    "portfolio_collection_enabled": new_config.portfolio_collection_enabled,
                    "collection_frequency_minutes": new_config.collection_frequency_minutes,
                    "change_threshold_percent": new_config.change_threshold_percent,
                    "max_collections_per_hour": new_config.max_collections_per_hour,
                    "data_retention_days": new_config.data_retention_days,
                    "enable_compression": new_config.enable_compression,
                    # Risk Management Settings
                    "max_portfolio_risk": new_config.max_portfolio_risk,
                    "max_drawdown": new_config.max_drawdown,
                    "daily_loss_limit": new_config.daily_loss_limit,
                    "weekly_loss_limit": new_config.weekly_loss_limit,
                    "monthly_loss_limit": new_config.monthly_loss_limit,
                    "max_single_position_size": new_config.max_single_position_size,
                    "max_sector_exposure": new_config.max_sector_exposure,
                    "correlation_limit": new_config.correlation_limit,
                    "leverage_limit": new_config.leverage_limit,
                    "default_stop_loss": new_config.default_stop_loss,
                    "default_take_profit": new_config.default_take_profit,
                    "trailing_stop_enabled": new_config.trailing_stop_enabled,
                    "trailing_stop_distance": new_config.trailing_stop_distance
                }
            }
        else:
            return {"error": "Failed to update trading configuration"}
            
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/execution/switch-mode")
async def switch_trading_mode(mode: str = Body(..., embed=True)):
    """Switch between trading modes (simulation, real_trading, hybrid, sandbox, backtest)."""
    try:
        from common.config_manager import config_manager, TradingMode
        
        # Validate mode
        try:
            trading_mode = TradingMode(mode)
        except ValueError:
            return {"error": f"Invalid trading mode: {mode}. Valid modes: {[m.value for m in TradingMode]}"}
        
        # Update trading mode
        success = await config_manager.update_trading_config({"trading_mode": mode})
        
        if success:
            # Reload configuration
            new_config = await config_manager.load_trading_config()
            
            return {
                "success": True,
                "message": f"Trading mode switched to {mode}",
                "config": {
                    "mode": new_config.mode.value,
                    "simulation_balance": new_config.simulation_balance,
                    "max_simulation_risk": new_config.max_simulation_risk,
                    "real_trading_enabled": new_config.real_trading_enabled,
                    "simulation_accounts": new_config.simulation_accounts,
                    "real_accounts": new_config.real_accounts,
                    "safety_checks_enabled": new_config.safety_checks_enabled,
                    "max_position_size": new_config.max_position_size,
                    "emergency_stop_enabled": new_config.emergency_stop_enabled
                }
            }
        else:
            return {"error": "Failed to update trading mode"}
            
    except Exception as e:
        return {"error": str(e)}


class AgenticExecutionService:
    """Service wrapper for the agentic execution agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic execution service."""
        try:
            logger.info("Starting Agentic Execution Service...")
            
            # Initialize the agentic execution agent
            self.agent = AgenticExecutionAgent(llm_config=None)  # Will use default config
            await self.agent.initialize_infrastructure()
            
            # Initialize websocket connections and other components
            logger.info("Initializing agent websocket connections...")
            await self.agent.initialize()
            logger.info("Agent websocket connections initialized successfully")
            
            self.running = True
            logger.info("Agentic Execution Service started successfully")
                
        except Exception as e:
            logger.error(f"Failed to start Agentic Execution Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic execution service."""
        try:
            logger.info("Stopping Agentic Execution Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Execution Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Execution Service: {e}")

def main():
    """Main function to run the agentic execution service."""
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")

if __name__ == "__main__":
    # Run the main function
    main()
