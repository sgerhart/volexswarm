"""
VolexSwarm Agentic Risk Agent - Main Entry Point
Transforms the FastAPI risk agent into an intelligent AutoGen AssistantAgent
with autonomous risk assessment and position sizing capabilities.
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
sys.path.insert(0, '/app/agents/risk')

from agents.risk.agentic_risk_agent import AgenticRiskAgent
from common.logging import get_logger

logger = get_logger("agentic_risk_main")

class AgenticRiskService:
    """Service wrapper for the agentic risk agent."""
    
    def __init__(self):
        self.agent = None
        self.running = False
        
    async def start(self):
        """Start the agentic risk service."""
        try:
            logger.info("Starting Agentic Risk Service...")
            
            # Initialize the agentic risk agent
            self.agent = AgenticRiskAgent(llm_config=None)  # Will use default config
            await self.agent.initialize_infrastructure()
            await self.agent.initialize()  # Initialize websocket connections and other components
            
            self.running = True
            logger.info("Agentic Risk Service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start Agentic Risk Service: {e}")
            raise
    
    async def stop(self):
        """Stop the agentic risk service."""
        try:
            logger.info("Stopping Agentic Risk Service...")
            self.running = False
            
            if self.agent:
                # Cleanup if needed
                pass
            
            logger.info("Agentic Risk Service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping Agentic Risk Service: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        if self.agent:
            return self.agent.get_agent_status()
        else:
            return {
                "agent_type": "agentic_risk",
                "status": "not_initialized"
            }

# Global service instance
service = AgenticRiskService()

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
app = FastAPI(title="VolexSwarm Risk Agent", lifespan=lifespan)



@app.get("/health")
async def health_check():
    """Health check endpoint for the Risk Agent."""
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
        if globals().get(f'risk_service') and globals()[f'risk_service'].agent:
            # Get database connectivity
            try:
                agent = globals()[f'risk_service'].agent
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
            "agent": "risk",
            "timestamp": datetime.now().isoformat(),
            "uptime": uptime_str,
            "connectivity": metrics,
            "agent_status": status
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "agent": "risk",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "VolexSwarm Risk Agent", "status": "running"}

# Risk Management API Endpoints

@app.post("/api/risk/assess")
async def assess_risk(request: Dict[str, Any]):
    """Assess risk for a position."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        # Extract parameters from request
        symbol = request.get("symbol", "")
        position_size = request.get("position_size", 0.0)
        entry_price = request.get("entry_price", 0.0)
        current_price = request.get("current_price", 0.0)
        side = request.get("side", "buy")
        account_balance = request.get("account_balance", 0.0)
        stop_loss = request.get("stop_loss")
        take_profit = request.get("take_profit")
        existing_positions = request.get("existing_positions", [])
        
        # Create risk assessment request
        from agents.risk.agentic_risk_agent import RiskAssessmentRequest
        risk_request = RiskAssessmentRequest(
            symbol=symbol,
            position_size=position_size,
            entry_price=entry_price,
            current_price=current_price,
            side=side,
            account_balance=account_balance,
            stop_loss=stop_loss,
            take_profit=take_profit,
            existing_positions=existing_positions
        )
        
        result = await service.agent.assess_risk(risk_request)
        return result
    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        return {"error": str(e)}

@app.post("/api/risk/position-size")
async def calculate_position_size(request: Dict[str, Any]):
    """Calculate optimal position size."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        # Extract parameters from request
        symbol = request.get("symbol", "")
        side = request.get("side", "buy")
        account_balance = request.get("account_balance", 0.0)
        current_price = request.get("current_price", 0.0)
        method = request.get("method", "kelly")
        volatility = request.get("volatility")
        win_rate = request.get("win_rate")
        avg_win = request.get("avg_win")
        avg_loss = request.get("avg_loss")
        correlation = request.get("correlation")
        
        # Create position sizing request
        from agents.risk.agentic_risk_agent import PositionSizingRequest
        sizing_request = PositionSizingRequest(
            symbol=symbol,
            side=side,
            account_balance=account_balance,
            current_price=current_price,
            method=method,
            volatility=volatility,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            correlation=correlation
        )
        
        result = await service.agent.calculate_position_size(sizing_request)
        return result
    except Exception as e:
        logger.error(f"Error in position sizing: {e}")
        return {"error": str(e)}

@app.post("/api/risk/stop-loss")
async def calculate_stop_loss(request: Dict[str, Any]):
    """Calculate stop-loss level."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        # Extract parameters from request
        symbol = request.get("symbol", "")
        entry_price = request.get("entry_price", 0.0)
        current_price = request.get("current_price", 0.0)
        side = request.get("side", "buy")
        volatility = request.get("volatility")
        atr_multiplier = request.get("atr_multiplier", 2.0)
        percentage = request.get("percentage")
        
        # Create stop-loss request
        from agents.risk.agentic_risk_agent import StopLossRequest
        stop_loss_request = StopLossRequest(
            symbol=symbol,
            entry_price=entry_price,
            current_price=current_price,
            side=side,
            volatility=volatility,
            atr_multiplier=atr_multiplier,
            percentage=percentage
        )
        
        result = await service.agent.calculate_stop_loss(stop_loss_request)
        return result
    except Exception as e:
        logger.error(f"Error in stop-loss calculation: {e}")
        return {"error": str(e)}

@app.post("/api/risk/portfolio")
async def assess_portfolio_risk(request: Dict[str, Any]):
    """Assess portfolio risk."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        # Extract parameters from request
        positions = request.get("positions", [])
        account_balance = request.get("account_balance", 0.0)
        risk_free_rate = request.get("risk_free_rate", 0.02)
        
        # Create portfolio risk request
        from agents.risk.agentic_risk_agent import PortfolioRiskRequest
        portfolio_request = PortfolioRiskRequest(
            positions=positions,
            account_balance=account_balance,
            risk_free_rate=risk_free_rate
        )
        
        result = await service.agent.assess_portfolio_risk(portfolio_request)
        return result
    except Exception as e:
        logger.error(f"Error in portfolio risk assessment: {e}")
        return {"error": str(e)}

@app.post("/api/risk/circuit-breaker")
async def check_circuit_breaker(request: Dict[str, Any]):
    """Check circuit breaker status."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        # Extract parameters from request
        symbol = request.get("symbol", "")
        current_price = request.get("current_price", 0.0)
        previous_price = request.get("previous_price", 0.0)
        timestamp = datetime.now()
        
        # Create circuit breaker request
        from agents.risk.agentic_risk_agent import CircuitBreakerRequest
        circuit_request = CircuitBreakerRequest(
            symbol=symbol,
            current_price=current_price,
            previous_price=previous_price,
            timestamp=timestamp
        )
        
        result = await service.agent.check_circuit_breaker(circuit_request)
        return result
    except Exception as e:
        logger.error(f"Error in circuit breaker check: {e}")
        return {"error": str(e)}

@app.post("/api/risk/drawdown-protection")
async def check_drawdown_protection(request: Dict[str, Any]):
    """Check drawdown protection."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        # Extract parameters from request
        account_balance = request.get("account_balance", 0.0)
        initial_balance = request.get("initial_balance", 0.0)
        current_positions = request.get("current_positions", [])
        timestamp = datetime.now()
        
        # Create drawdown protection request
        from agents.risk.agentic_risk_agent import DrawdownProtectionRequest
        drawdown_request = DrawdownProtectionRequest(
            account_balance=account_balance,
            initial_balance=initial_balance,
            current_positions=current_positions,
            timestamp=timestamp
        )
        
        result = await service.agent.check_drawdown_protection(drawdown_request)
        return result
    except Exception as e:
        logger.error(f"Error in drawdown protection check: {e}")
        return {"error": str(e)}

@app.get("/api/risk/status")
async def get_risk_status():
    """Get current risk management status."""
    try:
        if not service.agent:
            return {"error": "Risk agent not initialized"}
        
        status = service.agent.get_agent_status()
        return status
    except Exception as e:
        logger.error(f"Error getting risk status: {e}")
        return {"error": str(e)}

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    asyncio.create_task(service.stop())

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8009) 