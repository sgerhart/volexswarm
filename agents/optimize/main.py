"""
VolexSwarm Optimize Agent - Strategy Optimization and Performance Enhancement
Handles parameter optimization, portfolio rebalancing, and performance analysis.
"""

import sys
import os
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI
import uvicorn

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client, health_check as db_health_check
from common.logging import get_logger
from common.websocket_client import AgentWebSocketClient, MessageType

# Initialize structured logger
logger = get_logger("optimize")

app = FastAPI(title="VolexSwarm Optimize Agent", version="1.0.0")

# Global clients
vault_client = None
db_client = None
ws_client = None  # WebSocket client for real-time communication


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
                    "optimization_engine_active": True,
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
    """Initialize the optimize agent on startup."""
    global vault_client, db_client, ws_client
    
    try:
        # Initialize Vault client
        vault_client = get_vault_client()
        logger.info("Vault client initialized")
        
        # Initialize database client
        db_client = get_db_client()
        logger.info("Database client initialized")
        
        # Initialize WebSocket client for real-time communication
        ws_client = AgentWebSocketClient("optimize")
        await ws_client.connect()
        logger.info("WebSocket client connected to Meta Agent")
        
        # Start health monitoring background task
        asyncio.create_task(health_monitor_loop())
        
        logger.info("Optimize agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize optimize agent: {str(e)}")
        raise


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {
        "agent": "optimize",
        "status": "running",
        "version": "1.0.0",
        "vault_connected": vault_client.health_check() if vault_client else False,
        "db_connected": db_health_check() if db_client else False
    }


@app.get("/health")
def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "vault": vault_client.health_check() if vault_client else False,
            "database": db_health_check() if db_client else False,
            "websocket": ws_client.is_connected if ws_client else False
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007)
