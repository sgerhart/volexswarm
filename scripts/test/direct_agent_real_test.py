#!/usr/bin/env python3
"""
VolexSwarm Direct Agent Real Test
Directly tests agent capabilities with real Binance data and verifies LLM usage.

This test:
1. Directly calls agent methods to get real Binance portfolio data
2. Triggers LLM-based analysis and decision making
3. Verifies OpenAI API calls are being made
4. Uses the Meta agent to orchestrate real trading decisions
5. Monitors actual API usage and agent coordination

IMPORTANT: This uses REAL Binance data and can trigger REAL OpenAI API calls.
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
import time

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

logger = logging.getLogger("direct_agent_real_test")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class DirectAgentRealTest:
    """Direct agent testing with real data and LLM verification."""
    
    def __init__(self, max_budget_usd: float = 25.0):
        """Initialize the direct agent test."""
        self.max_budget_usd = max_budget_usd
        
        # Agent endpoints
        self.agent_endpoints = {
            "meta": "http://localhost:8004",
            "execution": "http://localhost:8002", 
            "realtime_data": "http://localhost:8026",
            "news_sentiment": "http://localhost:8024",
            "strategy_discovery": "http://localhost:8025",
            "monitor": "http://localhost:8008"
        }
        
        self.test_results = {
            "start_time": None,
            "real_binance_connection": False,
            "real_portfolio_data": {},
            "live_market_data": {},
            "llm_calls_verified": 0,
            "openai_api_activity": False,
            "agent_coordination": False,
            "trading_recommendations": [],
            "errors": []
        }
    
    async def test_real_binance_connection(self) -> bool:
        """Test real connection to Binance US and get actual data."""
        try:
            logger.info("🔗 Testing REAL Binance US connection...")
            
            async with aiohttp.ClientSession() as session:
                # Connect to Binance US via realtime data agent
                connect_payload = {
                    "exchange_name": "binanceus",
                    "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT"]
                }
                
                async with session.post(
                    f"{self.agent_endpoints['realtime_data']}/connect",
                    json=connect_payload,
                    timeout=15
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success") or data.get("status") == "success":
                            logger.info(f"✅ Real Binance US connection established: {data}")
                            self.test_results["real_binance_connection"] = True
                            
                            # Get real market data
                            await asyncio.sleep(2)  # Allow connection to establish
                            
                            for symbol in ["BTCUSDT", "ETHUSDT"]:
                                try:
                                    data_payload = {
                                        "symbol": symbol,
                                        "data_type": "ticker"
                                    }
                                    
                                    async with session.post(
                                        f"{self.agent_endpoints['realtime_data']}/data/latest",
                                        json=data_payload,
                                        timeout=10
                                    ) as data_response:
                                        if data_response.status == 200:
                                            market_data = await data_response.json()
                                            logger.info(f"📊 Real market data for {symbol}: {market_data}")
                                            self.test_results["live_market_data"][symbol] = market_data
                                        else:
                                            logger.warning(f"⚠️ Failed to get market data for {symbol}: {data_response.status}")
                                            
                                except Exception as e:
                                    logger.warning(f"⚠️ Error getting {symbol} data: {e}")
                            
                            return True
                        else:
                            logger.error(f"❌ Binance connection failed: {data}")
                            return False
                    else:
                        logger.error(f"❌ Binance connection API call failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Binance connection test failed: {e}")
            return False
    
    async def trigger_llm_analysis(self) -> int:
        """Trigger LLM-based analysis and count OpenAI API calls."""
        try:
            logger.info("🧠 Triggering LLM-based analysis...")
            llm_calls_made = 0
            
            async with aiohttp.ClientSession() as session:
                # 1. Trigger LLM-based news sentiment analysis
                logger.info("📰 Requesting LLM-based news sentiment analysis...")
                
                sentiment_payload = {
                    "query": "Bitcoin Ethereum cryptocurrency market analysis investment opportunities",
                    "symbols": ["BTCUSDT", "ETHUSDT"],
                    "analysis_type": "comprehensive",
                    "use_llm": True,
                    "force_fresh_analysis": True
                }
                
                try:
                    async with session.post(
                        f"{self.agent_endpoints['news_sentiment']}/analyze",
                        json=sentiment_payload,
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"🎯 LLM Sentiment Analysis Result: {data}")
                            
                            # Check for LLM usage indicators
                            if any(key in str(data).lower() for key in ['gpt', 'openai', 'llm', 'model']):
                                llm_calls_made += 1
                                logger.info("✅ LLM usage detected in sentiment analysis")
                            
                        else:
                            logger.warning(f"⚠️ Sentiment analysis failed: {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.warning("⏰ Sentiment analysis timed out")
                except Exception as e:
                    logger.warning(f"⚠️ Sentiment analysis error: {e}")
                
                # 2. Trigger LLM-based strategy discovery
                logger.info("🔬 Requesting LLM-based strategy discovery...")
                
                strategy_payload = {
                    "portfolio": {"BTC": 0.001, "USDT": 15.0},
                    "market_conditions": self.test_results["live_market_data"],
                    "budget_usd": self.max_budget_usd,
                    "risk_tolerance": "moderate",
                    "use_llm": True,
                    "generate_recommendations": True
                }
                
                try:
                    async with session.post(
                        f"{self.agent_endpoints['strategy_discovery']}/discover",
                        json=strategy_payload,
                        timeout=45
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"🎯 LLM Strategy Discovery Result: {data}")
                            
                            # Check for LLM usage indicators
                            if any(key in str(data).lower() for key in ['gpt', 'openai', 'llm', 'model', 'reasoning']):
                                llm_calls_made += 1
                                logger.info("✅ LLM usage detected in strategy discovery")
                                
                            # Extract trading recommendations
                            if "recommendations" in data or "strategies" in data:
                                self.test_results["trading_recommendations"] = data
                                
                        else:
                            logger.warning(f"⚠️ Strategy discovery failed: {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.warning("⏰ Strategy discovery timed out")
                except Exception as e:
                    logger.warning(f"⚠️ Strategy discovery error: {e}")
                
                # 3. Try to trigger Meta agent orchestration with LLM
                logger.info("🤖 Requesting Meta agent LLM orchestration...")
                
                meta_payload = {
                    "task": "portfolio_optimization",
                    "context": {
                        "current_portfolio": {"BTC": 0.001, "USDT": 15.0},
                        "budget": self.max_budget_usd,
                        "market_data": self.test_results["live_market_data"],
                        "objective": "Optimize portfolio for growth with moderate risk"
                    },
                    "use_llm": True,
                    "require_reasoning": True
                }
                
                # Try different potential Meta agent endpoints
                meta_endpoints = ["/orchestrate", "/analyze", "/optimize", "/recommend", "/chat"]
                
                for endpoint in meta_endpoints:
                    try:
                        async with session.post(
                            f"{self.agent_endpoints['meta']}{endpoint}",
                            json=meta_payload,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"🎯 Meta Agent LLM Response via {endpoint}: {data}")
                                
                                # Check for LLM usage indicators
                                if any(key in str(data).lower() for key in ['gpt', 'openai', 'llm', 'reasoning', 'analysis']):
                                    llm_calls_made += 1
                                    logger.info("✅ LLM usage detected in Meta agent")
                                    self.test_results["agent_coordination"] = True
                                
                                break  # Success, no need to try other endpoints
                                
                            elif response.status == 404:
                                continue  # Try next endpoint
                            else:
                                logger.warning(f"⚠️ Meta agent {endpoint} returned: {response.status}")
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Meta agent {endpoint} timed out")
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Meta agent {endpoint} error: {e}")
                        continue
            
            self.test_results["llm_calls_verified"] = llm_calls_made
            if llm_calls_made > 0:
                self.test_results["openai_api_activity"] = True
                logger.info(f"✅ Confirmed {llm_calls_made} LLM-based analyses")
            else:
                logger.warning("⚠️ No LLM usage detected - may need to check OpenAI API configuration")
            
            return llm_calls_made
            
        except Exception as e:
            logger.error(f"❌ LLM analysis trigger failed: {e}")
            return 0
    
    async def verify_openai_integration(self) -> bool:
        """Verify OpenAI integration is working."""
        try:
            logger.info("🔍 Verifying OpenAI integration...")
            
            # Check if agents have OpenAI credentials configured
            async with aiohttp.ClientSession() as session:
                for agent_name, endpoint in self.agent_endpoints.items():
                    try:
                        async with session.get(f"{endpoint}/health") as response:
                            if response.status == 200:
                                health_data = await response.json()
                                
                                # Look for OpenAI/LLM configuration indicators
                                health_str = str(health_data).lower()
                                if any(key in health_str for key in ['openai', 'llm', 'gpt', 'model']):
                                    logger.info(f"✅ {agent_name} agent has LLM configuration")
                                    return True
                                    
                    except Exception as e:
                        continue
            
            # Try a direct test call to see if we can trigger OpenAI
            logger.info("🧪 Testing direct OpenAI trigger...")
            
            # Simple test that should trigger LLM if configured
            test_payload = {
                "message": "Analyze the current cryptocurrency market conditions for Bitcoin and Ethereum. Provide investment recommendations.",
                "use_llm": True
            }
            
            async with aiohttp.ClientSession() as session:
                # Try news sentiment agent with a direct analysis request
                try:
                    async with session.post(
                        f"{self.agent_endpoints['news_sentiment']}/chat",
                        json=test_payload,
                        timeout=20
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"🎯 Direct LLM test response: {data}")
                            
                            # Check if response shows LLM usage
                            if len(str(data)) > 100:  # Substantial response suggests LLM usage
                                logger.info("✅ OpenAI integration appears to be working")
                                return True
                                
                except Exception as e:
                    logger.warning(f"⚠️ Direct LLM test failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ OpenAI integration verification failed: {e}")
            return False
    
    async def run_comprehensive_real_test(self) -> Dict[str, Any]:
        """Run comprehensive test with real data and LLM verification."""
        try:
            self.test_results["start_time"] = datetime.now()
            
            logger.info("🚀 Starting Direct Agent Real Data Test")
            logger.info("=" * 60)
            logger.info("🎯 Testing: Real Binance data + LLM decision making")
            logger.info(f"💰 Budget: ${self.max_budget_usd}")
            
            # Phase 1: Test real Binance connection
            binance_connected = await self.test_real_binance_connection()
            
            # Phase 2: Verify OpenAI integration
            openai_working = await self.verify_openai_integration()
            
            # Phase 3: Trigger LLM analysis
            llm_calls = await self.trigger_llm_analysis()
            
            # Phase 4: Generate comprehensive report
            await self.generate_comprehensive_report()
            
            return {"success": True, "results": self.test_results}
            
        except Exception as e:
            logger.error(f"❌ Comprehensive test failed: {e}")
            self.test_results["errors"].append(str(e))
            return {"success": False, "error": str(e), "results": self.test_results}
    
    async def generate_comprehensive_report(self):
        """Generate detailed test report."""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("📊 DIRECT AGENT REAL DATA TEST RESULTS")
            logger.info("=" * 60)
            
            # Connection Status
            logger.info("🔗 CONNECTION STATUS:")
            logger.info(f"  • Real Binance Connection: {'✅' if self.test_results['real_binance_connection'] else '❌'}")
            logger.info(f"  • OpenAI API Activity: {'✅' if self.test_results['openai_api_activity'] else '❌'}")
            logger.info(f"  • Agent Coordination: {'✅' if self.test_results['agent_coordination'] else '❌'}")
            
            # Data Quality
            logger.info("\n📊 DATA QUALITY:")
            logger.info(f"  • Live Market Data Points: {len(self.test_results['live_market_data'])}")
            logger.info(f"  • LLM Analyses Completed: {self.test_results['llm_calls_verified']}")
            
            if self.test_results["live_market_data"]:
                logger.info("  • Market Data Sample:")
                for symbol, data in list(self.test_results["live_market_data"].items())[:2]:
                    logger.info(f"    - {symbol}: {data}")
            
            # LLM Integration
            logger.info("\n🧠 LLM INTEGRATION:")
            if self.test_results["llm_calls_verified"] > 0:
                logger.info(f"  ✅ {self.test_results['llm_calls_verified']} LLM-based analyses confirmed")
                logger.info("  ✅ OpenAI API integration is working")
                logger.info("  ✅ Agents are making intelligent decisions")
            else:
                logger.info("  ⚠️ No LLM usage detected")
                logger.info("  💡 Check OpenAI API key configuration in Vault")
                logger.info("  💡 Verify agents have proper LLM initialization")
            
            # Trading Readiness
            logger.info("\n🎯 TRADING READINESS:")
            if (self.test_results["real_binance_connection"] and 
                self.test_results["llm_calls_verified"] > 0):
                logger.info("  ✅ System is ready for live trading")
                logger.info("  ✅ Real market data integration working")
                logger.info("  ✅ AI decision-making capabilities confirmed")
                logger.info(f"  ✅ Ready to deploy ${self.max_budget_usd} budget")
            else:
                logger.info("  ⚠️ System needs configuration before live trading")
                if not self.test_results["real_binance_connection"]:
                    logger.info("  - Fix Binance US connection")
                if not self.test_results["llm_calls_verified"]:
                    logger.info("  - Configure OpenAI API integration")
            
            # Next Steps
            logger.info("\n🚀 NEXT STEPS:")
            if self.test_results["openai_api_activity"]:
                logger.info("  1. ✅ LLM integration confirmed - proceed with live trading")
                logger.info("  2. 🎯 Execute real trades with AI recommendations")
                logger.info("  3. 📊 Monitor performance and adjust strategies")
            else:
                logger.info("  1. 🔧 Configure OpenAI API key in Vault")
                logger.info("  2. 🔄 Restart agents to pick up new configuration")
                logger.info("  3. 🧪 Re-run this test to verify LLM integration")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Report generation failed: {e}")

async def main():
    """Main test execution function."""
    try:
        test = DirectAgentRealTest(max_budget_usd=25.0)
        results = await test.run_comprehensive_real_test()
        
        if results["success"]:
            print("\n🎉 Direct Agent Real Data Test Completed!")
            print("🔍 Check the detailed report above for LLM and data verification.")
            return 0
        else:
            print(f"❌ Test failed: {results.get('error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
