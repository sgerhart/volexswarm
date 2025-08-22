"""
VolexSwarm Agentic Compliance Agent - Main Entry Point
Transforms the FastAPI compliance agent into an intelligent AutoGen AssistantAgent
with autonomous compliance monitoring and audit capabilities.
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

from agents.compliance.agentic_compliance_agent import AgenticComplianceAgent
from common.logging import get_logger

logger = get_logger("agentic_compliance_main")

class AgenticComplianceService:
    """Service wrapper for the agentic compliance agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic compliance service."""
        try:
            logger.info("Starting Agentic Compliance Service...")
            
            # Initialize the agentic compliance agent
            self.agent = AgenticComplianceAgent(llm_config=None)  # Will use default config
            await self.agent.initialize_infrastructure()
            await self.agent.initialize()  # Initialize websocket connections and other components
            
            self.running = True
            logger.info("Agentic Compliance Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Agentic Compliance Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic compliance service."""
        try:
            logger.info("Stopping Agentic Compliance Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Compliance Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Compliance Service: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        if self.agent:
            return self.agent.get_agent_status()
        else:
            return {
                "agent_type": "agentic_compliance",
                "status": "not_initialized"
            }

# Global service instance
service = AgenticComplianceService()

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
app = FastAPI(title="VolexSwarm Compliance Agent", lifespan=lifespan)



@app.get("/health")
async def health_check():
    """Health check endpoint for the Compliance Agent."""
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
        if globals().get(f'compliance_service') and globals()[f'compliance_service'].agent:
            # Get database connectivity
            try:
                agent = globals()[f'compliance_service'].agent
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
        
        return {
            "status": "healthy",
            "agent": "compliance",
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime_str,
            "connectivity": metrics,
            "agent_status": status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "compliance",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Compliance Agent", "status": "running"}

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(service.stop())

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8010) 