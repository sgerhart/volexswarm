"""
VolexSwarm Agentic Backtest Agent - Main Entry Point
Transforms the FastAPI backtest agent into an intelligent AutoGen AssistantAgent
with autonomous backtesting and strategy validation capabilities.
"""

import sys
import os
import asyncio
import signal
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, BackgroundTasks

import uvicorn
from contextlib import asynccontextmanager

# Add the current directory to the path for local imports
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/agents/backtest')

from agents.backtest.agentic_backtest_agent import AgenticBacktestAgent
from common.logging import get_logger

logger = get_logger("agentic_backtest_main")

# Global service instance
backtest_service = None
start_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global backtest_service, start_time

    start_time = datetime.now()
    backtest_service = AgenticBacktestService()
    await backtest_service.start()
    yield
    # Shutdown
    if backtest_service:
        await backtest_service.stop()

# Create FastAPI app
app = FastAPI(title="VolexSwarm Backtest Agent", lifespan=lifespan)



@app.get("/health")
async def health_check():
    """Health check endpoint for the Backtest Agent."""
    global backtest_service
    try:
        if backtest_service and backtest_service.running:
            # Calculate actual uptime
            uptime_str = "0h 0m"
            if 'start_time' in globals() and start_time:
                uptime_delta = datetime.now() - start_time
                hours = int(uptime_delta.total_seconds() // 3600)
                minutes = int((uptime_delta.total_seconds() % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            
            # Get real metrics from the agent
            metrics = {}
            if globals().get(f'backtest_service') and globals()[f'backtest_service'].agent:
                # Get database connectivity
                try:
                    agent = globals()[f'backtest_service'].agent
                    if hasattr(agent, 'db_client') and agent.db_client:
                        metrics["database"] = {"status": "connected"}
                    else:
                        metrics["database"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["database"] = {"status": "error", "error": str(e)}
                
                # Get vault connectivity  
                try:
                    if hasattr(agent, 'vault_client') and agent.vault_client:
                        metrics["vault"] = {"status": "connected"}
                    else:
                        metrics["vault"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["vault"] = {"status": "error", "error": str(e)}
                
                # Get websocket connectivity
                try:
                    if hasattr(agent, 'ws_client') and agent.ws_client and agent.ws_client.connected:
                        metrics["websocket"] = {"status": "connected"}
                    else:
                        metrics["websocket"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["websocket"] = {"status": "error", "error": str(e)}
            
            return {
                "status": "healthy",
                "agent": "backtest",
                "timestamp": datetime.now().isoformat(),
                "uptime": uptime_str,
                "connectivity": metrics
            }
        else:
            return {
                "status": "unhealthy",
                "agent": "backtest",
                "timestamp": datetime.now().isoformat(),
                "error": "Service not running"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "backtest",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Backtest Agent", "status": "running"}

class AgenticBacktestService:
    """Service wrapper for the agentic backtest agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic backtest service."""
        try:
            logger.info("Starting Agentic Backtest Service...")
            
            # Initialize the agentic backtest agent
            self.agent = AgenticBacktestAgent()
            await self.agent.initialize_infrastructure()
            
            self.running = True
            logger.info("Agentic Backtest Service started successfully")
                
        except Exception as e:
            logger.error(f"Failed to start Agentic Backtest Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic backtest service."""
        try:
            logger.info("Stopping Agentic Backtest Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Backtest Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Backtest Service: {e}")

def main():
    """Main function to run the agentic backtest service."""
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8006, log_level="info")

if __name__ == "__main__":
    # Run the main function
    main()
