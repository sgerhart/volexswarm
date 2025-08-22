"""
VolexSwarm Agentic Research Agent - Main Entry Point
Transforms the FastAPI research agent into an intelligent AutoGen AssistantAgent
with autonomous research capabilities and market analysis.
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

# Add the project root to the path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/agents/research')

from agentic_research_agent import AgenticResearchAgent
from common.logging import get_logger

logger = get_logger("agentic_research_main")

# Global service instance
research_service = None
start_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global research_service, start_time
    start_time = datetime.now()
    research_service = AgenticResearchService()
    await research_service.start()
    yield
    # Shutdown
    if research_service:
        await research_service.stop()

# Create FastAPI app
app = FastAPI(title="VolexSwarm Research Agent", lifespan=lifespan)



@app.get("/health")
async def health_check():
    """Health check endpoint for the Research Agent."""
    global research_service
    try:
        if research_service and research_service.running:
            # Calculate actual uptime
            uptime_str = "0h 0m"
            if 'start_time' in globals() and start_time:
                uptime_delta = datetime.now() - start_time
                hours = int(uptime_delta.total_seconds() // 3600)
                minutes = int((uptime_delta.total_seconds() % 3600) // 60)
                uptime_str = f"{hours}h {minutes}m"
            
            # Get real metrics from the agent
            metrics = {}
            if research_service.agent:
                # Get database connectivity
                try:
                    if hasattr(research_service.agent, 'db_client') and research_service.agent.db_client:
                        metrics["database"] = {"status": "connected"}
                    else:
                        metrics["database"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["database"] = {"status": "error", "error": str(e)}
                
                # Get vault connectivity  
                try:
                    if hasattr(research_service.agent, 'vault_client') and research_service.agent.vault_client:
                        metrics["vault"] = {"status": "connected"}
                    else:
                        metrics["vault"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["vault"] = {"status": "error", "error": str(e)}
                
                # Get websocket connectivity
                try:
                    if (hasattr(research_service.agent, 'ws_client') and 
                        research_service.agent.ws_client and 
                        research_service.agent.ws_client.is_connected):
                        metrics["websocket"] = {"status": "connected"}
                    else:
                        metrics["websocket"] = {"status": "disconnected"}
                except Exception as e:
                    metrics["websocket"] = {"status": "error", "error": str(e)}
            
            return {
                "status": "healthy",
                "agent": "research",
                "timestamp": datetime.now().isoformat(),
                "uptime": uptime_str,
                "connectivity": metrics
            }
        else:
            return {
                "status": "unhealthy",
                "agent": "research",
                "timestamp": datetime.now().isoformat(),
                "error": "Service not running"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "research",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Research Agent", "status": "running"}



class AgenticResearchService:
    """Service wrapper for the agentic research agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic research service."""
        try:
            logger.info("Starting Agentic Research Service...")
            
            # Initialize the agentic research agent
            self.agent = AgenticResearchAgent()
            await self.agent.initialize_infrastructure()
            
            # Initialize websocket connection to meta agent
            if not await self.agent.initialize():
                logger.error("Failed to initialize websocket connection")
                raise Exception("Websocket initialization failed")
            
            self.running = True
            logger.info("Agentic Research Service started successfully")
                
        except Exception as e:
            logger.error(f"Failed to start Agentic Research Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic research service."""
        try:
            logger.info("Stopping Agentic Research Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Research Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Research Service: {e}")

def main():
    """Main function to run the agentic research service."""
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    # Run the main function
    main()
