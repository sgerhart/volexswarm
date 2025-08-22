"""
VolexSwarm Agentic Monitor Agent - Main Entry Point
Transforms the FastAPI monitor agent into an intelligent AutoGen AssistantAgent
with autonomous system monitoring and health management capabilities.
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
sys.path.append(os.path.dirname(__file__))

from agents.monitor.agentic_monitor_agent import AgenticMonitorAgent
from common.logging import get_logger

logger = get_logger("agentic_monitor_main")

class AgenticMonitorService:
    """Service wrapper for the agentic monitor agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic monitor service."""
        try:
            logger.info("Starting Agentic Monitor Service...")
            
            # Initialize the agentic monitor agent
            self.agent = AgenticMonitorAgent()
            await self.agent.initialize_infrastructure()
            
            self.running = True
            logger.info("Agentic Monitor Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Agentic Monitor Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic monitor service."""
        try:
            logger.info("Stopping Agentic Monitor Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Monitor Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Monitor Service: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        if self.agent:
            return self.agent.get_agent_status()
        else:
            return {
                "agent_type": "agentic_monitor",
                "status": "not_initialized"
            }

# Global service instance
service = AgenticMonitorService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        await service.start()
    except Exception as e:
        logger.error(f"Failed to start service in lifespan: {e}")
    yield
    # Shutdown
    try:
        await service.stop()
    except Exception as e:
        logger.error(f"Failed to stop service in lifespan: {e}")

# Create FastAPI app
app = FastAPI(title="VolexSwarm Monitor Agent", lifespan=lifespan)



@app.get("/health")
async def health_check():
    """Health check endpoint for the Monitor Agent."""
    try:
        status = service.get_status()
        
        # Calculate actual uptime
        uptime_str = "0h 0m"
        if 'start_time' in globals() and start_time:
            uptime_delta = datetime.now() - start_time
            hours = int(uptime_delta.total_seconds() // 3600)
            minutes = int((uptime_delta.total_seconds() % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"
        
        # Get real metrics from the agent
        metrics = {}
        if service and service.agent:
            # Get database connectivity
            try:
                agent = service.agent
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
            "agent": "monitor",
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime_str,
            "connectivity": metrics,
            "agent_status": status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "monitor",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Monitor Agent", "status": "running"}

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(service.stop())

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8008)
