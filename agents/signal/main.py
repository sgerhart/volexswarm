"""
VolexSwarm Agentic Signal Agent - Main Entry Point
Transforms the FastAPI signal agent into an intelligent AutoGen AssistantAgent
with autonomous signal generation and technical analysis capabilities.
"""

import sys
import os
import asyncio
import signal
from datetime import datetime
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any
from fastapi import FastAPI, BackgroundTasks

import uvicorn

# Add the current directory to the path for local imports
sys.path.append(os.path.dirname(__file__))

from agentic_signal_agent import AgenticSignalAgent
from common.logging import get_logger

logger = get_logger("agentic_signal_main")

# Global service instance
signal_service = None
start_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global signal_service, start_time
    start_time = datetime.now()
    signal_service = AgenticSignalService()
    await signal_service.start()
    yield
    # Shutdown
    if signal_service:
        await signal_service.stop()

# Create FastAPI app
app = FastAPI(title="VolexSwarm Signal Agent", lifespan=lifespan)



@app.get("/health")
@app.options("/health")
async def health_check():
    """Health check endpoint for the Signal Agent."""
    global signal_service, start_time
    try:
        if signal_service and signal_service.running:
            # Calculate actual uptime
            if start_time:
                uptime_delta = datetime.now() - start_time
                hours = int(uptime_delta.total_seconds() // 3600)
                minutes = int((uptime_delta.total_seconds() % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            else:
                uptime_str = "0h 0m"
            
            # Check connectivity to external services
            connectivity_checks = {}
            
            # Check database connectivity
            try:
                if signal_service.agent and signal_service.agent.db_client:
                    # Simple database check
                    connectivity_checks["database"] = {"status": "connected"}
                else:
                    connectivity_checks["database"] = {"status": "disconnected", "error": "DB client not initialized"}
            except Exception as e:
                connectivity_checks["database"] = {"status": "error", "error": str(e)}
            
            # Check Vault connectivity
            try:
                if signal_service.agent and signal_service.agent.vault_client:
                    connectivity_checks["vault"] = {"status": "connected"}
                else:
                    connectivity_checks["vault"] = {"status": "disconnected", "error": "Vault client not initialized"}
            except Exception as e:
                connectivity_checks["vault"] = {"status": "error", "error": str(e)}
            
            # Check OpenAI connectivity
            try:
                if signal_service.agent and signal_service.agent.openai_client:
                    connectivity_checks["openai"] = {"status": "connected"}
                else:
                    connectivity_checks["openai"] = {"status": "disconnected", "error": "OpenAI client not initialized"}
            except Exception as e:
                connectivity_checks["openai"] = {"status": "error", "error": str(e)}
            
            # Check websocket connectivity
            try:
                if (hasattr(signal_service.agent, 'ws_client') and 
                    signal_service.agent.ws_client and 
                    signal_service.agent.ws_client.is_connected):
                    connectivity_checks["websocket"] = {"status": "connected"}
                else:
                    connectivity_checks["websocket"] = {"status": "disconnected"}
            except Exception as e:
                connectivity_checks["websocket"] = {"status": "error", "error": str(e)}
            
            return {
                "status": "healthy",
                "agent": "signal",
                "timestamp": datetime.now().isoformat(),
                "uptime": uptime_str,

                "connectivity": connectivity_checks
            }
        else:
            return {
                "status": "unhealthy",
                "agent": "signal",
                "timestamp": datetime.now().isoformat(),
                "error": "Service not running"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "signal",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Signal Agent", "status": "running"}

@app.post("/generate-signal")
async def generate_signal(request: Dict[str, Any]):
    """Generate a trading signal for a given symbol."""
    try:
        if not signal_service or not signal_service.running:
            return {"error": "Signal service not running"}
        
        symbol = request.get("symbol", "BTCUSDT")
        signal_type = request.get("signal_type", "comprehensive")
        timeframe = request.get("timeframe", "1h")
        
        if not signal_service.agent:
            return {"error": "Signal agent not initialized"}
        
        signal_result = await signal_service.agent.generate_autonomous_signal(
            symbol=symbol,
            signal_type=signal_type,
            timeframe=timeframe
        )
        
        return {
            "status": "success",
            "data": signal_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating signal: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/signals/{symbol}")
async def get_signals(symbol: str, limit: int = 100):
    """Get signal history for a specific symbol."""
    try:
        if not signal_service or not signal_service.running or not signal_service.agent:
            return {"error": "Signal service not available"}
        
        signals = await signal_service.agent.get_signal_history(symbol=symbol, limit=limit)
        
        return {
            "status": "success",
            "data": signals,
            "symbol": symbol,
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting signals: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/signals")
async def get_all_signals(limit: int = 100):
    """Get all signal history."""
    try:
        if not signal_service or not signal_service.running or not signal_service.agent:
            return {"error": "Signal service not available"}
        
        signals = await signal_service.agent.get_signal_history(limit=limit)
        
        return {
            "status": "success",
            "data": signals,
            "count": len(signals),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting all signals: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/performance")
async def get_performance():
    """Get signal performance metrics."""
    try:
        if not signal_service or not signal_service.running or not signal_service.agent:
            return {"error": "Signal service not available"}
        
        metrics = await signal_service.agent.get_performance_metrics()
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/analyze/{symbol}")
async def analyze_symbol(symbol: str, timeframe: str = "1h"):
    """Perform comprehensive analysis for a symbol."""
    try:
        if not signal_service or not signal_service.running or not signal_service.agent:
            return {"error": "Signal service not available"}
        
        # Generate comprehensive signal
        signal_result = await signal_service.agent.generate_autonomous_signal(
            symbol=symbol,
            signal_type="comprehensive",
            timeframe=timeframe
        )
        
        # Get additional analysis data
        analysis_data = {
            "signal": signal_result,
            "technical_indicators": {},
            "market_conditions": {},
            "risk_assessment": {}
        }
        
        # Add technical indicators if available
        if hasattr(signal_service.agent, '_analyze_technical_indicators'):
            try:
                # This would need price data to be implemented
                analysis_data["technical_indicators"] = {
                    "status": "available",
                    "note": "Technical analysis methods available in agent"
                }
            except Exception:
                analysis_data["technical_indicators"] = {"status": "error"}
        
        return {
            "status": "success",
            "data": analysis_data,
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing symbol: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/status")
async def get_agent_status():
    """Get detailed agent status and capabilities."""
    try:
        if not signal_service or not signal_service.running or not signal_service.agent:
            return {"error": "Signal service not available"}
        
        agent_status = signal_service.agent.get_agent_status()
        
        # Add additional status information
        status_info = {
            "agent_status": agent_status,
            "service_running": signal_service.running,
            "websocket_connected": False,
            "capabilities": [
                "autonomous_signal_generation",
                "technical_analysis",
                "machine_learning_signals",
                "hybrid_signal_combining",
                "signal_caching",
                "performance_tracking",
                "ai_reasoning"
            ],
            "supported_signal_types": [
                "comprehensive",
                "technical", 
                "ml",
                "hybrid"
            ],
            "supported_timeframes": [
                "1m", "5m", "15m", "30m", "1h", "4h", "1d"
            ]
        }
        
        # Check websocket status
        if hasattr(signal_service.agent, 'ws_client') and signal_service.agent.ws_client:
            status_info["websocket_connected"] = signal_service.agent.ws_client.is_connected
        
        return {
            "status": "success",
            "data": status_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }



class AgenticSignalService:
    """Service wrapper for the agentic signal agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic signal service."""
        try:
            logger.info("Starting Agentic Signal Service...")
            
            # Initialize the agentic signal agent
            self.agent = AgenticSignalAgent()
            await self.agent.initialize_infrastructure()
            
            # Initialize websocket connection to meta agent
            if not await self.agent.initialize():
                logger.error("Failed to initialize websocket connection")
                raise Exception("Websocket initialization failed")
            
            # Initialize signal generator with dynamic configuration
            if hasattr(self.agent, 'signal_generator'):
                await self.agent.signal_generator.initialize()
            
            self.running = True
            logger.info("Agentic Signal Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Agentic Signal Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic signal service."""
        try:
            logger.info("Stopping Agentic Signal Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Signal Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Signal Service: {e}")

def main():
    """Main function to run the agentic signal service."""
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")

if __name__ == "__main__":
    # Run the main function
    main() 