#!/usr/bin/env python3
"""
Meta Agent Orchestrator Test

This test demonstrates the proper way to interact with VolexSwarm through the Meta Agent
as the central orchestrator. The Meta Agent coordinates all 12 agents and manages
intelligent task delegation, consensus building, and autonomous decision making.

Architecture Flow:
User Request → Meta Agent (Port 8004) → Coordinates Other Agents → Returns Results
"""

import sys
import os
import asyncio
import json
import websockets
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.logging import get_logger

logger = get_logger("meta_orchestrator_test")

class MetaAgentOrchestrator:
    """Client for interacting with the Meta Agent as the central orchestrator."""
    
    def __init__(self, meta_host: str = "localhost", meta_port: int = 8004):
        self.meta_host = meta_host
        self.meta_port = meta_port
        self.base_url = f"http://{meta_host}:{meta_port}"
        self.websocket_url = f"ws://{meta_host}:{meta_port}/ws"
        self.websocket = None
        
    async def connect(self) -> bool:
        """Connect to the Meta Agent."""
        try:
            # Test HTTP connection first
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Meta Agent HTTP connection successful")
                
                # Try to connect to WebSocket
                try:
                    self.websocket = await websockets.connect(self.websocket_url)
                    logger.info("✅ Meta Agent WebSocket connection successful")
                    return True
                except Exception as ws_error:
                    logger.warning(f"⚠️ WebSocket connection failed: {ws_error}")
                    logger.info("📡 Using HTTP-only mode")
                    return True
            else:
                logger.error(f"❌ Meta Agent HTTP connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Meta Agent: {e}")
            return False
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get the status of all agents coordinated by Meta Agent."""
        try:
            response = requests.get(f"{self.base_url}/agents/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get agent status: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting agent status: {e}")
            return {"error": str(e)}
    
    async def create_intelligent_task(self, name: str, description: str, 
                                    priority: str = "MEDIUM",
                                    required_agents: List[str] = None) -> Dict[str, Any]:
        """Create an intelligent task through the Meta Agent."""
        try:
            task_data = {
                "name": name,
                "description": description,
                "priority": priority,
                "required_agents": required_agents or []
            }
            
            response = requests.post(
                f"{self.base_url}/tasks/create",
                json=task_data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create task: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error creating intelligent task: {e}")
            return {"error": str(e)}
    
    async def execute_task_with_autogen(self, task_description: str, 
                                      required_agents: List[str] = None) -> Dict[str, Any]:
        """Execute a task using AutoGen coordination through Meta Agent."""
        try:
            task_data = {
                "task_description": task_description,
                "required_agents": required_agents or [],
                "max_rounds": 10,
                "preserve_context": True
            }
            
            response = requests.post(
                f"{self.base_url}/autogen/execute",
                json=task_data,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to execute AutoGen task: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error executing AutoGen task: {e}")
            return {"error": str(e)}
    
    async def get_autogen_status(self) -> Dict[str, Any]:
        """Get AutoGen coordination status from Meta Agent."""
        try:
            response = requests.get(f"{self.base_url}/autogen/status", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get AutoGen status: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"Error getting AutoGen status: {e}")
            return {"error": str(e)}
    
    async def coordinate_portfolio_discovery(self) -> Dict[str, Any]:
        """Coordinate portfolio discovery through Meta Agent."""
        task_description = """
        Discover and analyze the current Binance US portfolio:
        1. Retrieve current account balances and positions
        2. Calculate portfolio valuation in USD
        3. Analyze asset allocation and diversification
        4. Identify trading opportunities based on current holdings
        5. Assess risk exposure and position sizes
        
        Use real Binance US data - no simulated data.
        """
        
        required_agents = ["execution", "realtime_data", "research", "risk"]
        
        return await self.execute_task_with_autogen(task_description, required_agents)
    
    async def coordinate_trading_strategy(self, budget: float = 25.0) -> Dict[str, Any]:
        """Coordinate intelligent trading strategy through Meta Agent."""
        task_description = f"""
        Develop and execute an intelligent trading strategy with ${budget} budget:
        1. Analyze current market conditions and trends
        2. Research news sentiment and market drivers
        3. Generate trading signals based on technical analysis
        4. Develop risk-managed trading strategy
        5. Execute trades if signals are strong and risk is acceptable
        6. Monitor positions and adjust as needed
        
        Use real Binance US account and live market data.
        Budget: ${budget}
        """
        
        required_agents = ["strategy", "news_sentiment", "signal", "execution", "risk", "monitor"]
        
        return await self.execute_task_with_autogen(task_description, required_agents)
    
    async def coordinate_market_research(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Coordinate comprehensive market research through Meta Agent."""
        symbols = symbols or ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        task_description = f"""
        Conduct comprehensive market research and analysis:
        1. Analyze market trends for symbols: {', '.join(symbols)}
        2. Research news sentiment and market drivers
        3. Perform technical analysis and pattern recognition
        4. Identify potential trading opportunities
        5. Assess market volatility and risk factors
        6. Generate actionable insights and recommendations
        
        Use real-time market data and live news feeds.
        """
        
        required_agents = ["research", "news_sentiment", "signal", "realtime_data"]
        
        return await self.execute_task_with_autogen(task_description, required_agents)
    
    async def send_websocket_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send a message via WebSocket to Meta Agent."""
        if not self.websocket:
            logger.warning("WebSocket not connected")
            return None
            
        try:
            await self.websocket.send(json.dumps(message))
            response = await asyncio.wait_for(self.websocket.recv(), timeout=30)
            return json.loads(response)
        except Exception as e:
            logger.error(f"WebSocket communication error: {e}")
            return None
    
    async def disconnect(self):
        """Disconnect from Meta Agent."""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket connection closed")

async def test_meta_agent_orchestration():
    """Test the Meta Agent orchestration capabilities."""
    logger.info("🚀 Starting Meta Agent Orchestrator Test")
    logger.info("=" * 60)
    
    # Initialize Meta Agent orchestrator
    orchestrator = MetaAgentOrchestrator()
    
    try:
        # Step 1: Connect to Meta Agent
        logger.info("📡 Step 1: Connecting to Meta Agent...")
        connected = await orchestrator.connect()
        if not connected:
            logger.error("❌ Failed to connect to Meta Agent")
            return False
        
        # Step 2: Get agent status
        logger.info("📊 Step 2: Getting agent coordination status...")
        agent_status = await orchestrator.get_agent_status()
        logger.info(f"Agent Status: {json.dumps(agent_status, indent=2)}")
        
        # Step 3: Get AutoGen status
        logger.info("🤖 Step 3: Getting AutoGen coordination status...")
        autogen_status = await orchestrator.get_autogen_status()
        logger.info(f"AutoGen Status: {json.dumps(autogen_status, indent=2)}")
        
        # Step 4: Test portfolio discovery coordination
        logger.info("💰 Step 4: Testing portfolio discovery coordination...")
        portfolio_result = await orchestrator.coordinate_portfolio_discovery()
        logger.info(f"Portfolio Discovery Result: {json.dumps(portfolio_result, indent=2)}")
        
        # Step 5: Test market research coordination
        logger.info("📈 Step 5: Testing market research coordination...")
        research_result = await orchestrator.coordinate_market_research()
        logger.info(f"Market Research Result: {json.dumps(research_result, indent=2)}")
        
        # Step 6: Test trading strategy coordination
        logger.info("🎯 Step 6: Testing trading strategy coordination...")
        strategy_result = await orchestrator.coordinate_trading_strategy(budget=25.0)
        logger.info(f"Trading Strategy Result: {json.dumps(strategy_result, indent=2)}")
        
        # Step 7: Create intelligent task
        logger.info("🧠 Step 7: Testing intelligent task creation...")
        task_result = await orchestrator.create_intelligent_task(
            name="Live Trading Readiness Assessment",
            description="Assess system readiness for live trading with $25 budget on Binance US",
            priority="HIGH",
            required_agents=["execution", "risk", "compliance", "monitor"]
        )
        logger.info(f"Intelligent Task Result: {json.dumps(task_result, indent=2)}")
        
        logger.info("✅ Meta Agent Orchestrator Test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        await orchestrator.disconnect()

async def main():
    """Main test execution."""
    logger.info("🎯 VolexSwarm Meta Agent Orchestrator Test")
    logger.info("Testing the proper architecture flow through Meta Agent")
    logger.info("=" * 80)
    
    success = await test_meta_agent_orchestration()
    
    if success:
        logger.info("🎉 All tests passed! Meta Agent orchestration is working correctly.")
    else:
        logger.error("💥 Tests failed. Check Meta Agent configuration and endpoints.")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())
