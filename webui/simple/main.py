"""
Simple VolexSwarm Web UI Backend
FastAPI server that serves a simple HTML dashboard and aggregates data from all agents.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
import uvicorn
from pydantic import BaseModel
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent endpoints
AGENT_ENDPOINTS = {
    "research": "http://research:8000",
    "signal": "http://signal:8003", 
    "execution": "http://execution:8002",
    "meta": "http://meta:8004"
}

# Data models
class SystemMetrics(BaseModel):
    total_agents: int
    healthy_agents: int
    active_signals: int
    total_trades: int
    system_uptime: str
    last_update: datetime

# Global state
system_state = {
    "agents": {},
    "signals": [],
    "market_data": {},
    "trades": [],
    "metrics": None,
    "last_update": datetime.now()
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting VolexSwarm Simple Web UI Backend...")
    
    # Start background task to update system state
    task = asyncio.create_task(periodic_state_update())
    
    yield
    
    # Shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="VolexSwarm Simple Web UI",
    description="Simple web interface for VolexSwarm Autonomous AI Trading System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_agent_data(agent_name: str, endpoint: str) -> Dict[str, Any]:
    """Get data from a specific agent."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Get health status
            health_response = await client.get(f"{endpoint}/health")
            health_data = health_response.json() if health_response.status_code == 200 else {}
            
            return {"health": health_data}
            
    except Exception as e:
        logger.error(f"Error getting data from {agent_name} agent: {e}")
        return {"error": str(e)}

async def update_system_state():
    """Update global system state by polling all agents."""
    logger.info("Updating system state...")
    
    # Check all agents
    agent_tasks = []
    for agent_name, endpoint in AGENT_ENDPOINTS.items():
        task = asyncio.create_task(get_agent_data(agent_name, endpoint))
        agent_tasks.append((agent_name, task))
    
    # Wait for all agent responses
    for agent_name, task in agent_tasks:
        try:
            data = await task
            system_state["agents"][agent_name] = data
        except Exception as e:
            logger.error(f"Error updating {agent_name}: {e}")
            system_state["agents"][agent_name] = {"error": str(e)}
    
    # Update metrics
    healthy_agents = sum(1 for agent_data in system_state["agents"].values() 
                        if agent_data.get("health", {}).get("status") == "healthy")
    
    system_state["metrics"] = SystemMetrics(
        total_agents=len(AGENT_ENDPOINTS),
        healthy_agents=healthy_agents,
        active_signals=len(system_state.get("signals", [])),
        total_trades=len(system_state.get("trades", [])),
        system_uptime="24h",  # TODO: Calculate actual uptime
        last_update=datetime.now()
    )
    
    system_state["last_update"] = datetime.now()
    logger.info("System state updated")

async def periodic_state_update():
    """Periodically update system state."""
    while True:
        await update_system_state()
        await asyncio.sleep(30)  # Update every 30 seconds

# API Endpoints

@app.get("/")
async def serve_dashboard():
    """Serve the HTML dashboard."""
    return FileResponse("index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/agents")
async def get_agents():
    """Get status of all agents."""
    return system_state["agents"]

@app.get("/api/signals")
async def get_signals():
    """Get recent trading signals."""
    return system_state.get("signals", [])

@app.get("/api/market-data")
async def get_market_data():
    """Get current market data."""
    return system_state.get("market_data", {})

@app.get("/api/trades")
async def get_trades():
    """Get trade history."""
    return system_state.get("trades", [])

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics."""
    return system_state.get("metrics")

@app.get("/api/system-status")
async def get_system_status():
    """Get overall system status."""
    return {
        "status": "operational" if system_state.get("metrics", {}).healthy_agents == len(AGENT_ENDPOINTS) else "degraded",
        "last_update": system_state["last_update"],
        "agents": system_state["agents"],
        "metrics": system_state.get("metrics")
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=False) 