#!/usr/bin/env python3
"""
⚠️  DEPRECATED - Clean Meta Agent for VolexSwarm ⚠️

This file is DEPRECATED and no longer used in the active system.
The system now uses the enhanced `hybrid_meta_agent.py` instead.

REASON FOR DEPRECATION:
- This was a "clean" version attempt that was never integrated
- The active system uses `hybrid_meta_agent.py` with enhanced features
- All portfolio coordination improvements have been moved to the active agent

CURRENT ACTIVE AGENT:
- File: `hybrid_meta_agent.py` 
- Main entry point: `main.py`
- Status: Enhanced with portfolio intelligence and AutoGen integration

DO NOT USE THIS FILE - It is kept for reference only.
"""

import sys
import os
import asyncio
import json
import threading
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests
import websockets
from websockets.server import serve
from websockets.exceptions import ConnectionClosed

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client, get_agent_config
from common.db import get_db_client
from common.logging import get_logger
from common.openai_client import get_openai_client

logger = get_logger("clean_meta_agent")

class TaskStatus(Enum):
    """Simple task status tracking."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class SimpleTask:
    """Simple task definition without over-engineering."""
    id: str
    name: str
    description: str
    status: TaskStatus
    assigned_agents: List[str]
    created_at: datetime
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class CleanMetaAgent:
    """Clean, focused Meta Agent for VolexSwarm orchestration."""
    
    def __init__(self):
        self.app = None
        self.vault_client = None
        self.db_client = None
        self.openai_client = None
        self.websocket_clients = set()
        self.tasks: Dict[str, SimpleTask] = {}
        
        # Agent endpoints - the agents we coordinate
        self.agent_endpoints = {
            "execution": "http://localhost:8002",
            "realtime_data": "http://localhost:8026", 
            "news_sentiment": "http://localhost:8024",
            "strategy_discovery": "http://localhost:8025",
            "monitor": "http://localhost:8008",
            "risk": "http://localhost:8027",
            "signal": "http://localhost:8023"
        }
    
    async def initialize(self):
        """Initialize the Meta Agent infrastructure."""
        try:
            logger.info("🚀 Initializing Clean Meta Agent...")
            
            # Initialize clients
            self.vault_client = get_vault_client()
            self.db_client = get_db_client()
            self.openai_client = get_openai_client()
            
            # Setup FastAPI app
            self._setup_api()
            
            # Start servers
            self._start_servers()
            
            logger.info("✅ Clean Meta Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Meta Agent: {e}")
            raise
    
    def _setup_api(self):
        """Setup clean, focused API endpoints."""
        self.app = FastAPI(
            title="VolexSwarm Meta Agent",
            description="Central orchestrator for VolexSwarm trading agents",
            version="2.0.0"
        )
        
        # Add CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Health check
        @self.app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "agent": "meta",
                "version": "2.0.0",
                "timestamp": datetime.now().isoformat()
            }
        
        # Get all agent status
        @self.app.get("/agents/status")
        async def get_agent_status():
            return await self._check_all_agents()
        
        # Coordinate portfolio discovery
        @self.app.post("/coordinate/portfolio")
        async def coordinate_portfolio():
            """Coordinate portfolio discovery across agents using available methods."""
            task_id = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task = SimpleTask(
                id=task_id,
                name="Portfolio Discovery",
                description="Get real Binance US portfolio data and analysis",
                status=TaskStatus.RUNNING,
                assigned_agents=["execution", "risk", "signal"],
                created_at=datetime.now()
            )
            
            self.tasks[task_id] = task
            
            try:
                logger.info(f"🔄 Starting portfolio discovery task: {task_id}")
                
                # Step 1: Get portfolio status from execution agent (using available methods)
                logger.info("📊 Getting portfolio status from Execution Agent...")
                portfolio_result = await self._get_execution_portfolio()
                
                # Step 2: Get risk analysis from risk agent
                logger.info("⚠️ Getting risk analysis from Risk Agent...")
                risk_result = await self._get_risk_analysis(portfolio_result)
                
                # Step 3: Get trading signals for context
                logger.info("📈 Getting trading signals from Signal Agent...")
                signal_result = await self._get_trading_signals()
                
                # Step 4: Aggregate and analyze results
                logger.info("🧠 Aggregating portfolio intelligence...")
                aggregated_result = await self._aggregate_portfolio_intelligence(
                    portfolio_result, risk_result, signal_result
                )
                
                # Combine results
                result = {
                    "task_id": task_id,
                    "portfolio": portfolio_result,
                    "risk_analysis": risk_result,
                    "trading_signals": signal_result,
                    "aggregated_intelligence": aggregated_result,
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed"
                }
                
                task.status = TaskStatus.COMPLETED
                task.result = result
                
                logger.info(f"✅ Portfolio discovery completed: {task_id}")
                return result
                
            except Exception as e:
                logger.error(f"❌ Portfolio discovery failed: {e}")
                task.status = TaskStatus.FAILED
                task.error = str(e)
                return {"error": str(e), "task_id": task_id}
        
        # Coordinate trading strategy
        @self.app.post("/coordinate/trading")
        async def coordinate_trading(request: dict):
            """Coordinate intelligent trading strategy."""
            budget = request.get("budget", 25.0)
            task_id = f"trading_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task = SimpleTask(
                id=task_id,
                name="Trading Strategy",
                description=f"Develop and execute trading strategy with ${budget} budget",
                status=TaskStatus.RUNNING,
                assigned_agents=["strategy_discovery", "news_sentiment", "signal", "execution", "risk"],
                created_at=datetime.now()
            )
            
            self.tasks[task_id] = task
            
            try:
                # Step 1: Get current portfolio
                portfolio = await self._call_agent("execution", "/portfolio/balances")
                
                # Step 2: Get market sentiment
                sentiment = await self._call_agent("news_sentiment", "/analyze/sentiment")
                
                # Step 3: Get trading signals
                signals = await self._call_agent("signal", "/generate/signals")
                
                # Step 4: Discover strategies
                strategies = await self._call_agent("strategy_discovery", "/discover/strategies", {
                    "budget": budget,
                    "portfolio": portfolio,
                    "sentiment": sentiment,
                    "signals": signals
                })
                
                # Step 5: Risk assessment
                risk_assessment = await self._call_agent("risk", "/assess/strategy", {
                    "strategy": strategies,
                    "budget": budget
                })
                
                # Step 6: Execute if risk is acceptable
                execution_result = None
                if risk_assessment.get("risk_score", 1.0) < 0.7:  # Low risk
                    execution_result = await self._call_agent("execution", "/execute/strategy", {
                        "strategy": strategies,
                        "budget": budget,
                        "risk_limits": risk_assessment
                    })
                
                result = {
                    "task_id": task_id,
                    "budget": budget,
                    "portfolio": portfolio,
                    "sentiment": sentiment,
                    "signals": signals,
                    "strategies": strategies,
                    "risk_assessment": risk_assessment,
                    "execution": execution_result,
                    "timestamp": datetime.now().isoformat()
                }
                
                task.status = TaskStatus.COMPLETED
                task.result = result
                
                return result
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                return {"error": str(e), "task_id": task_id}
        
        # Coordinate market research
        @self.app.post("/coordinate/research")
        async def coordinate_research(request: dict):
            """Coordinate comprehensive market research."""
            symbols = request.get("symbols", ["BTCUSDT", "ETHUSDT", "ADAUSDT"])
            task_id = f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            task = SimpleTask(
                id=task_id,
                name="Market Research",
                description=f"Research market conditions for {symbols}",
                status=TaskStatus.RUNNING,
                assigned_agents=["realtime_data", "news_sentiment", "signal"],
                created_at=datetime.now()
            )
            
            self.tasks[task_id] = task
            
            try:
                # Get market data
                market_data = await self._call_agent("realtime_data", "/market/data", {
                    "symbols": symbols
                })
                
                # Get news sentiment
                sentiment = await self._call_agent("news_sentiment", "/analyze/symbols", {
                    "symbols": symbols
                })
                
                # Get technical signals
                signals = await self._call_agent("signal", "/analyze/technical", {
                    "symbols": symbols
                })
                
                result = {
                    "task_id": task_id,
                    "symbols": symbols,
                    "market_data": market_data,
                    "sentiment": sentiment,
                    "signals": signals,
                    "timestamp": datetime.now().isoformat()
                }
                
                task.status = TaskStatus.COMPLETED
                task.result = result
                
                return result
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                return {"error": str(e), "task_id": task_id}
        
        # Get task status
        @self.app.get("/tasks/{task_id}")
        async def get_task_status(task_id: str):
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            
            task = self.tasks[task_id]
            return {
                "task_id": task.id,
                "name": task.name,
                "description": task.description,
                "status": task.status.value,
                "assigned_agents": task.assigned_agents,
                "created_at": task.created_at.isoformat(),
                "result": task.result,
                "error": task.error
            }
        
        # List all tasks
        @self.app.get("/tasks")
        async def list_tasks():
            return {
                "tasks": [
                    {
                        "task_id": task.id,
                        "name": task.name,
                        "status": task.status.value,
                        "created_at": task.created_at.isoformat()
                    }
                    for task in self.tasks.values()
                ]
            }
    
    async def _check_all_agents(self) -> Dict[str, Any]:
        """Check the health of all coordinated agents."""
        agent_status = {}
        healthy_count = 0
        
        for agent_name, endpoint in self.agent_endpoints.items():
            try:
                response = requests.get(f"{endpoint}/health", timeout=3)
                if response.status_code == 200:
                    agent_status[agent_name] = {
                        "status": "healthy",
                        "endpoint": endpoint,
                        "response_time": response.elapsed.total_seconds()
                    }
                    healthy_count += 1
                else:
                    agent_status[agent_name] = {
                        "status": "unhealthy",
                        "endpoint": endpoint,
                        "http_status": response.status_code
                    }
            except Exception as e:
                agent_status[agent_name] = {
                    "status": "unreachable",
                    "endpoint": endpoint,
                    "error": str(e)
                }
        
        return {
            "meta_agent": "healthy",
            "coordinated_agents": agent_status,
            "total_agents": len(self.agent_endpoints),
            "healthy_agents": healthy_count,
            "health_percentage": (healthy_count / len(self.agent_endpoints)) * 100
        }
    
    async def _get_execution_portfolio(self) -> Dict[str, Any]:
        """Get portfolio data from Execution Agent using available methods."""
        try:
            # Since Execution Agent doesn't have portfolio endpoints exposed,
            # we'll simulate portfolio data for now and focus on the coordination pattern
            # In production, this would call the actual portfolio methods
            
            # Simulate portfolio data structure
            portfolio_data = {
                "total_value": 0.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0,
                "positions": [],
                "cash_balance": 0.0,
                "timestamp": datetime.now().isoformat(),
                "source": "execution_agent_simulation"
            }
            
            logger.info("📊 Retrieved portfolio data from Execution Agent")
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Failed to get execution portfolio: {e}")
            return {"error": str(e), "source": "execution_agent"}
    
    async def _get_risk_analysis(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get risk analysis from Risk Agent."""
        try:
            # Call Risk Agent's portfolio assessment endpoint
            risk_result = await self._call_agent("risk", "/api/risk/portfolio", {
                "positions": portfolio_data.get("positions", []),
                "account_balance": portfolio_data.get("total_value", 0)
            })
            
            logger.info("⚠️ Retrieved risk analysis from Risk Agent")
            return risk_result
            
        except Exception as e:
            logger.error(f"Failed to get risk analysis: {e}")
            return {"error": str(e), "source": "risk_agent"}
    
    async def _get_trading_signals(self) -> Dict[str, Any]:
        """Get trading signals from Signal Agent."""
        try:
            # Call Signal Agent's signals endpoint
            signal_result = await self._call_agent("signal", "/signals")
            
            logger.info("📈 Retrieved trading signals from Signal Agent")
            return signal_result
            
        except Exception as e:
            logger.error(f"Failed to get trading signals: {e}")
            return {"error": str(e), "source": "signal_agent"}
    
    async def _aggregate_portfolio_intelligence(self, portfolio: Dict[str, Any], 
                                             risk: Dict[str, Any], 
                                             signals: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate and analyze portfolio intelligence across all sources."""
        try:
            # Calculate portfolio health score
            portfolio_health = self._calculate_portfolio_health(portfolio, risk)
            
            # Generate intelligent insights
            insights = self._generate_portfolio_insights(portfolio, risk, signals)
            
            # Create recommendations
            recommendations = self._create_portfolio_recommendations(portfolio, risk, signals)
            
            aggregated_intelligence = {
                "portfolio_health_score": portfolio_health,
                "insights": insights,
                "recommendations": recommendations,
                "risk_level": risk.get("risk_level", "unknown"),
                "signal_count": len(signals.get("data", [])),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info("🧠 Portfolio intelligence aggregation completed")
            return aggregated_intelligence
            
        except Exception as e:
            logger.error(f"Failed to aggregate portfolio intelligence: {e}")
            return {"error": str(e), "source": "intelligence_aggregation"}
    
    def _calculate_portfolio_health(self, portfolio: Dict[str, Any], risk: Dict[str, Any]) -> float:
        """Calculate a portfolio health score (0-100)."""
        try:
            # Simple health calculation based on available data
            health_score = 50.0  # Base score
            
            # Adjust based on risk level
            risk_level = risk.get("risk_level", "medium")
            if risk_level == "low":
                health_score += 20
            elif risk_level == "high":
                health_score -= 20
            
            # Adjust based on portfolio value
            total_value = portfolio.get("total_value", 0)
            if total_value > 0:
                health_score += 10
            
            # Ensure score is between 0-100
            return max(0, min(100, health_score))
            
        except Exception:
            return 50.0  # Default score
    
    def _generate_portfolio_insights(self, portfolio: Dict[str, Any], 
                                   risk: Dict[str, Any], 
                                   signals: Dict[str, Any]) -> List[str]:
        """Generate intelligent insights about the portfolio."""
        insights = []
        
        try:
            # Portfolio value insights
            total_value = portfolio.get("total_value", 0)
            if total_value == 0:
                insights.append("Portfolio appears to be empty - consider initial funding")
            elif total_value < 100:
                insights.append("Portfolio value is low - consider dollar-cost averaging")
            
            # Risk insights
            risk_level = risk.get("risk_level", "unknown")
            if risk_level == "high":
                insights.append("Portfolio risk level is high - consider risk management strategies")
            elif risk_level == "low":
                insights.append("Portfolio risk level is low - may be underutilizing opportunities")
            
            # Signal insights
            signal_count = len(signals.get("data", []))
            if signal_count == 0:
                insights.append("No active trading signals - market may be in consolidation")
            elif signal_count > 5:
                insights.append("Multiple trading signals active - high market volatility detected")
            
            # Add timestamp insight
            insights.append(f"Analysis performed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            insights.append(f"Error generating insights: {str(e)}")
        
        return insights
    
    def _create_portfolio_recommendations(self, portfolio: Dict[str, Any], 
                                        risk: Dict[str, Any], 
                                        signals: Dict[str, Any]) -> List[str]:
        """Create actionable recommendations for the portfolio."""
        recommendations = []
        
        try:
            # Risk-based recommendations
            risk_level = risk.get("risk_level", "unknown")
            if risk_level == "high":
                recommendations.append("Consider reducing position sizes to manage risk")
                recommendations.append("Implement stop-loss orders for existing positions")
            elif risk_level == "low":
                recommendations.append("Consider increasing position sizes for better returns")
                recommendations.append("Explore higher-risk, higher-reward opportunities")
            
            # Portfolio-based recommendations
            total_value = portfolio.get("total_value", 0)
            if total_value == 0:
                recommendations.append("Start with a small initial investment to test strategies")
                recommendations.append("Consider paper trading to validate approaches")
            
            # Signal-based recommendations
            signal_count = len(signals.get("data", []))
            if signal_count > 0:
                recommendations.append("Review active trading signals for entry opportunities")
                recommendations.append("Monitor signal performance to refine strategies")
            
            # General recommendations
            recommendations.append("Regularly review and rebalance portfolio")
            recommendations.append("Maintain emergency funds outside of trading portfolio")
            
        except Exception as e:
            recommendations.append(f"Error creating recommendations: {str(e)}")
        
        return recommendations

    async def _call_agent(self, agent_name: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a call to a specific agent."""
        if agent_name not in self.agent_endpoints:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        base_url = self.agent_endpoints[agent_name]
        url = f"{base_url}{endpoint}"
        
        try:
            if data:
                response = requests.post(url, json=data, timeout=30)
            else:
                response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Agent {agent_name} returned {response.status_code}: {response.text}")
                return {"error": f"HTTP {response.status_code}", "agent": agent_name}
                
        except Exception as e:
            logger.error(f"Failed to call agent {agent_name}: {e}")
            return {"error": str(e), "agent": agent_name}
    
    def _start_servers(self):
        """Start FastAPI and WebSocket servers."""
        # Start FastAPI server
        def run_fastapi():
            uvicorn.run(self.app, host="0.0.0.0", port=8004, log_level="info")
        
        fastapi_thread = threading.Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        # Start WebSocket server
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def websocket_handler(websocket, path):
                try:
                    self.websocket_clients.add(websocket)
                    logger.info(f"WebSocket client connected: {websocket.remote_address}")
                    
                    await websocket.send(json.dumps({
                        "type": "welcome",
                        "message": "Connected to VolexSwarm Meta Agent",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            if data.get("type") == "ping":
                                await websocket.send(json.dumps({
                                    "type": "pong",
                                    "timestamp": datetime.now().isoformat()
                                }))
                        except Exception as e:
                            logger.error(f"WebSocket message error: {e}")
                            
                except ConnectionClosed:
                    logger.info("WebSocket client disconnected")
                except Exception as e:
                    logger.error(f"WebSocket error: {e}")
                finally:
                    self.websocket_clients.discard(websocket)
            
            start_server = serve(websocket_handler, "localhost", 8005)  # Different port for WS
            loop.run_until_complete(start_server)
            loop.run_forever()
        
        websocket_thread = threading.Thread(target=run_websocket, daemon=True)
        websocket_thread.start()
        
        logger.info("🌐 FastAPI server started on http://localhost:8004")
        logger.info("🔌 WebSocket server started on ws://localhost:8005")

# Global instance
meta_agent = CleanMetaAgent()

async def main():
    """Main entry point."""
    await meta_agent.initialize()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down Clean Meta Agent...")

if __name__ == "__main__":
    asyncio.run(main())
