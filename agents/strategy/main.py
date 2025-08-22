"""
VolexSwarm Agentic Strategy Agent - Main Entry Point
Transforms the FastAPI strategy agent into an intelligent AutoGen AssistantAgent
with autonomous strategy development and management capabilities.
"""

import sys
import os
import asyncio
import signal
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

import uvicorn
from contextlib import asynccontextmanager

# Add the current directory to the path for local imports
sys.path.append(os.path.dirname(__file__))

sys.path.insert(0, '/app')
sys.path.insert(0, '/app/agents/strategy')

from agentic_strategy_agent import AgenticStrategyAgent
from common.logging import get_logger

logger = get_logger("agentic_strategy_main")

# Global service instance
strategy_service = None
start_time = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global strategy_service, start_time

    start_time = datetime.now()
    strategy_service = AgenticStrategyService()
    await strategy_service.start()
    yield
    # Shutdown
    if strategy_service:
        await strategy_service.stop()

# Create FastAPI app
app = FastAPI(title="VolexSwarm Strategy Agent", lifespan=lifespan)



@app.get("/health")
async def health_check():
    """Health check endpoint for the Strategy Agent."""
    global strategy_service
    try:
        if strategy_service and strategy_service.running:
            return {
                "status": "healthy",
                "agent": "strategy",
                "timestamp": datetime.now().isoformat(),
                "uptime": "0h 0m"
            }
        else:
            return {
                "status": "unhealthy",
                "agent": "strategy",
                "timestamp": datetime.now().isoformat(),
                "error": "Service not running"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "strategy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Strategy Agent", "status": "running"}

@app.post("/api/strategy/create")
async def create_strategy(request: Dict[str, Any]):
    """Create a new trading strategy."""
    global strategy_service
    try:
        if not strategy_service or not strategy_service.running:
            raise HTTPException(status_code=503, detail="Strategy service not available")
        
        from agents.strategy.agentic_strategy_agent import StrategyRequest
        
        strategy_request = StrategyRequest(
            name=request.get("name"),
            description=request.get("description"),
            strategy_type=request.get("strategy_type", "moving_average"),
            parameters=request.get("parameters", {}),
            symbols=request.get("symbols", ["BTC/USD"]),
            timeframe=request.get("timeframe", "1h"),
            risk_per_trade=request.get("risk_per_trade", 0.01),
            max_positions=request.get("max_positions", 5),
            enabled=request.get("enabled", False)
        )
        
        result = await strategy_service.agent.create_strategy(strategy_request)
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error creating strategy: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/strategy/templates")
async def get_strategy_templates():
    """Get available strategy templates."""
    global strategy_service
    try:
        if not strategy_service or not strategy_service.running:
            raise HTTPException(status_code=503, detail="Strategy service not available")
        
        result = await strategy_service.agent.get_strategy_templates()
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error getting strategy templates: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/strategy/list")
async def list_strategies(status: Optional[str] = None, limit: int = 50):
    """List all strategies."""
    global strategy_service
    try:
        if not strategy_service or not strategy_service.running:
            raise HTTPException(status_code=503, detail="Strategy service not available")
        
        result = await strategy_service.agent.list_strategies(status=status, limit=limit)
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.put("/api/strategy/{strategy_id}")
async def update_strategy(strategy_id: int, request: Dict[str, Any]):
    """Update an existing strategy."""
    global strategy_service
    try:
        if not strategy_service or not strategy_service.running:
            raise HTTPException(status_code=503, detail="Strategy service not available")
        
        result = await strategy_service.agent.update_strategy(strategy_id, request)
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/strategy/{strategy_id}/performance")
async def analyze_strategy_performance(strategy_id: int):
    """Analyze strategy performance."""
    global strategy_service
    try:
        if not strategy_service or not strategy_service.running:
            raise HTTPException(status_code=503, detail="Strategy service not available")
        
        result = await strategy_service.agent.analyze_strategy_performance(strategy_id)
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Error analyzing strategy performance: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

class AgenticStrategyService:
    """Service wrapper for the agentic strategy agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic strategy service."""
        try:
            logger.info("Starting Agentic Strategy Service...")
            
            # Initialize the agentic strategy agent
            self.agent = AgenticStrategyAgent(llm_config=None)  # Will use default config
            await self.agent.initialize_infrastructure()
            await self.agent.initialize()  # Initialize websocket connections and other components
            
            self.running = True
            logger.info("Agentic Strategy Service started successfully")
                
        except Exception as e:
            logger.error(f"Failed to start Agentic Strategy Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic strategy service."""
        try:
            logger.info("Stopping Agentic Strategy Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Strategy Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Strategy Service: {e}")

def main():
    """Main function to run the agentic strategy service."""
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8011, log_level="info")

if __name__ == "__main__":
    # Run the main function
    main()
