"""
VolexSwarm Web UI Backend
FastAPI server that aggregates data from all agents and serves the web interface.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uvicorn
from pydantic import BaseModel
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="VolexSwarm Web UI",
    description="Web interface for VolexSwarm Autonomous AI Trading System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent endpoints
AGENT_ENDPOINTS = {
    "research": "http://localhost:8001",
    "signal": "http://localhost:8003", 
    "execution": "http://localhost:8002",
    "meta": "http://localhost:8004"
}

# Data models
class AgentStatus(BaseModel):
    agent: str
    status: str
    healthy: bool
    last_check: datetime
    details: Dict[str, Any]

class TradingSignal(BaseModel):
    symbol: str
    signal_type: str
    confidence: float
    strength: float
    timestamp: datetime
    price: float
    indicators: Dict[str, Any]
    gpt_commentary: Optional[Dict[str, Any]]

class MarketData(BaseModel):
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime

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

async def check_agent_health(agent_name: str, endpoint: str) -> AgentStatus:
    """Check health of a specific agent."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{endpoint}/health")
            if response.status_code == 200:
                data = response.json()
                return AgentStatus(
                    agent=agent_name,
                    status=data.get("status", "unknown"),
                    healthy=data.get("status") == "healthy",
                    last_check=datetime.now(),
                    details=data
                )
            else:
                return AgentStatus(
                    agent=agent_name,
                    status="unhealthy",
                    healthy=False,
                    last_check=datetime.now(),
                    details={"error": f"HTTP {response.status_code}"}
                )
    except Exception as e:
        logger.error(f"Error checking {agent_name} agent: {e}")
        return AgentStatus(
            agent=agent_name,
            status="error",
            healthy=False,
            last_check=datetime.now(),
            details={"error": str(e)}
        )

async def get_agent_data(agent_name: str, endpoint: str) -> Dict[str, Any]:
    """Get data from a specific agent."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Get health status
            health_response = await client.get(f"{endpoint}/health")
            health_data = health_response.json() if health_response.status_code == 200 else {}
            
            # Get additional data based on agent type
            agent_data = {"health": health_data}
            
            if agent_name == "research":
                # Get market data
                try:
                    market_response = await client.get(f"{endpoint}/market/BTCUSD")
                    if market_response.status_code == 200:
                        agent_data["market_data"] = market_response.json()
                except:
                    pass
                    
            elif agent_name == "signal":
                # Get recent signals
                try:
                    signals_response = await client.get(f"{endpoint}/signals/recent")
                    if signals_response.status_code == 200:
                        agent_data["signals"] = signals_response.json()
                except:
                    pass
                    
            elif agent_name == "execution":
                # Get trade history
                try:
                    trades_response = await client.get(f"{endpoint}/trades")
                    if trades_response.status_code == 200:
                        agent_data["trades"] = trades_response.json()
                except:
                    pass
                    
            elif agent_name == "meta":
                # Get system overview
                try:
                    status_response = await client.get(f"{endpoint}/status")
                    if status_response.status_code == 200:
                        agent_data["system_status"] = status_response.json()
                except:
                    pass
            
            return agent_data
            
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

@app.on_event("startup")
async def startup_event():
    """Initialize the web UI backend."""
    logger.info("Starting VolexSwarm Web UI Backend...")
    
    # Start background task to update system state
    asyncio.create_task(periodic_state_update())

async def periodic_state_update():
    """Periodically update system state."""
    while True:
        await update_system_state()
        await asyncio.sleep(30)  # Update every 30 seconds

# API Endpoints

@app.get("/")
async def serve_webui():
    """Serve the React web interface."""
    return FileResponse("webui/build/index.html")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/api/agents")
async def get_agents():
    """Get status of all agents."""
    return system_state["agents"]

@app.get("/api/agents/{agent_name}")
async def get_agent(agent_name: str):
    """Get detailed data for a specific agent."""
    if agent_name not in system_state["agents"]:
        raise HTTPException(status_code=404, detail="Agent not found")
    return system_state["agents"][agent_name]

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

@app.post("/api/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """Manually trigger a system state refresh."""
    background_tasks.add_task(update_system_state)
    return {"message": "Refresh initiated"}

# Serve static files
if os.path.exists("webui/build"):
    app.mount("/static", StaticFiles(directory="webui/build/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8005, reload=True) 