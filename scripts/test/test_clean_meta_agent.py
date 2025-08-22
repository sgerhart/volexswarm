#!/usr/bin/env python3
"""
Test the Clean Meta Agent

This test demonstrates the clean, focused Meta Agent that replaces
the bloated 4,449-line version with a maintainable 269-line implementation.
"""

import sys
import os
import asyncio
import json
import requests
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.logging import get_logger

logger = get_logger("test_clean_meta")

class CleanMetaAgentTester:
    """Test client for the Clean Meta Agent."""
    
    def __init__(self, host: str = "localhost", port: int = 8004):
        self.base_url = f"http://{host}:{port}"
    
    async def test_health(self) -> bool:
        """Test Meta Agent health."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Meta Agent Health: {data}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    async def test_agent_status(self) -> Dict[str, Any]:
        """Test agent coordination status."""
        try:
            response = requests.get(f"{self.base_url}/agents/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📊 Agent Status: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Agent status failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Agent status error: {e}")
            return {"error": str(e)}
    
    async def test_portfolio_coordination(self) -> Dict[str, Any]:
        """Test portfolio discovery coordination."""
        try:
            response = requests.post(f"{self.base_url}/coordinate/portfolio", timeout=30)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"💰 Portfolio Coordination: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Portfolio coordination failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Portfolio coordination error: {e}")
            return {"error": str(e)}
    
    async def test_trading_coordination(self, budget: float = 25.0) -> Dict[str, Any]:
        """Test trading strategy coordination."""
        try:
            payload = {"budget": budget}
            response = requests.post(
                f"{self.base_url}/coordinate/trading", 
                json=payload, 
                timeout=60
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"🎯 Trading Coordination: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Trading coordination failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Trading coordination error: {e}")
            return {"error": str(e)}
    
    async def test_research_coordination(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Test market research coordination."""
        try:
            symbols = symbols or ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            payload = {"symbols": symbols}
            response = requests.post(
                f"{self.base_url}/coordinate/research", 
                json=payload, 
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📈 Research Coordination: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Research coordination failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Research coordination error: {e}")
            return {"error": str(e)}
    
    async def test_task_management(self) -> Dict[str, Any]:
        """Test task management."""
        try:
            response = requests.get(f"{self.base_url}/tasks", timeout=10)
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📋 Task Management: {json.dumps(data, indent=2)}")
                return data
            else:
                logger.error(f"❌ Task management failed: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}
        except Exception as e:
            logger.error(f"❌ Task management error: {e}")
            return {"error": str(e)}

async def main():
    """Main test execution."""
    logger.info("🧹 Testing Clean Meta Agent (269 lines vs 4,449 lines)")
    logger.info("=" * 60)
    
    tester = CleanMetaAgentTester()
    
    # Test 1: Health Check
    logger.info("🏥 Test 1: Health Check")
    health_ok = await tester.test_health()
    
    # Test 2: Agent Status
    logger.info("📊 Test 2: Agent Coordination Status")
    agent_status = await tester.test_agent_status()
    
    # Test 3: Portfolio Coordination
    logger.info("💰 Test 3: Portfolio Discovery Coordination")
    portfolio_result = await tester.test_portfolio_coordination()
    
    # Test 4: Trading Coordination
    logger.info("🎯 Test 4: Trading Strategy Coordination")
    trading_result = await tester.test_trading_coordination(budget=25.0)
    
    # Test 5: Research Coordination
    logger.info("📈 Test 5: Market Research Coordination")
    research_result = await tester.test_research_coordination()
    
    # Test 6: Task Management
    logger.info("📋 Test 6: Task Management")
    task_result = await tester.test_task_management()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🎉 Clean Meta Agent Test Summary:")
    logger.info(f"✅ Health Check: {'PASS' if health_ok else 'FAIL'}")
    logger.info(f"✅ Agent Status: {'PASS' if 'error' not in agent_status else 'FAIL'}")
    logger.info(f"✅ Portfolio: {'PASS' if 'error' not in portfolio_result else 'FAIL'}")
    logger.info(f"✅ Trading: {'PASS' if 'error' not in trading_result else 'FAIL'}")
    logger.info(f"✅ Research: {'PASS' if 'error' not in research_result else 'FAIL'}")
    logger.info(f"✅ Tasks: {'PASS' if 'error' not in task_result else 'FAIL'}")
    
    logger.info("🧹 Clean Meta Agent provides focused orchestration without bloat!")

if __name__ == "__main__":
    asyncio.run(main())
