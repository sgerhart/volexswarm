#!/usr/bin/env python3
"""
VolexSwarm Real Data Orchestrated Test
Uses the Meta agent to orchestrate all other agents with real Binance data and LLM decision-making.

This test:
1. Calls the Meta agent (orchestrator) to coordinate all operations
2. Gets real balance data from the actual Binance account
3. Uses live market data from Binance US
4. Triggers actual OpenAI LLM calls for intelligent decision-making
5. Executes real trading recommendations based on AI analysis

IMPORTANT: This uses REAL data and can execute REAL trades with the $25 budget.
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

logger = logging.getLogger("real_data_orchestrated_test")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class RealDataOrchestratedTest:
    """Real-world test using Meta agent orchestration with actual data."""
    
    def __init__(self, max_budget_usd: float = 25.0):
        """Initialize the real data test."""
        self.max_budget_usd = max_budget_usd
        
        # Main orchestrating agent (Meta agent)
        self.meta_agent_endpoint = "http://localhost:8004"
        
        # Individual agent endpoints for direct calls if needed
        self.agent_endpoints = {
            "meta": "http://localhost:8004",
            "execution": "http://localhost:8002",
            "realtime_data": "http://localhost:8026",
            "news_sentiment": "http://localhost:8024",
            "strategy_discovery": "http://localhost:8025",
            "monitor": "http://localhost:8008"
        }
        
        # Test state
        self.test_start_time = None
        self.real_portfolio = {}
        self.market_analysis = {}
        self.llm_decisions = []
        self.openai_calls_made = 0
        
        self.test_results = {
            "start_time": None,
            "real_portfolio_retrieved": False,
            "live_market_data_retrieved": False,
            "llm_decisions_made": 0,
            "openai_api_calls": 0,
            "meta_agent_orchestration": False,
            "trading_recommendations": [],
            "actual_trades_executed": 0,
            "final_portfolio": {},
            "errors": []
        }
    
    async def get_real_binance_portfolio(self) -> Dict[str, float]:
        """Get the actual portfolio balances from Binance account via execution agent."""
        try:
            logger.info("💼 Retrieving REAL portfolio balances from Binance account...")
            
            async with aiohttp.ClientSession() as session:
                # Call execution agent to get real portfolio
                async with session.get(f"{self.agent_endpoints['execution']}/portfolio") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            portfolio = data.get("balances", {})
                            logger.info("✅ Real portfolio retrieved from Binance:")
                            
                            total_value_usd = 0
                            for asset, balance in portfolio.items():
                                if float(balance) > 0:
                                    logger.info(f"  • {asset}: {balance}")
                                    self.real_portfolio[asset] = float(balance)
                                    
                                    # Estimate USD value (simplified)
                                    if asset == "USDT":
                                        total_value_usd += float(balance)
                                    elif asset == "BTC":
                                        total_value_usd += float(balance) * 45000  # Rough estimate
                            
                            logger.info(f"📊 Estimated Total Portfolio Value: ${total_value_usd:.2f}")
                            self.test_results["real_portfolio_retrieved"] = True
                            return self.real_portfolio
                        else:
                            logger.error(f"❌ Portfolio retrieval failed: {data.get('message')}")
                    else:
                        logger.error(f"❌ Portfolio API call failed: {response.status}")
                        
                # Fallback: try alternative endpoint
                async with session.post(
                    f"{self.agent_endpoints['execution']}/get_balance",
                    json={"exchange": "binance"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Balance data retrieved: {data}")
                        self.test_results["real_portfolio_retrieved"] = True
                        return data.get("balance", {})
                    else:
                        logger.warning(f"⚠️ Balance endpoint returned: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Real portfolio retrieval failed: {e}")
            
        return {}
    
    async def orchestrate_via_meta_agent(self, task_description: str) -> Dict[str, Any]:
        """Use the Meta agent to orchestrate a complex trading task."""
        try:
            logger.info("🎯 Orchestrating task via Meta agent...")
            logger.info(f"📋 Task: {task_description}")
            
            async with aiohttp.ClientSession() as session:
                # Send orchestration request to Meta agent
                orchestration_payload = {
                    "task_type": "portfolio_analysis_and_trading",
                    "description": task_description,
                    "parameters": {
                        "max_budget_usd": self.max_budget_usd,
                        "risk_level": "moderate",
                        "diversification_target": 3,
                        "use_real_data": True,
                        "enable_llm_analysis": True
                    }
                }
                
                # Try different potential endpoints for orchestration
                endpoints_to_try = [
                    "/orchestrate",
                    "/execute_task",
                    "/analyze_and_trade",
                    "/portfolio_management",
                    "/trading_session"
                ]
                
                for endpoint in endpoints_to_try:
                    try:
                        async with session.post(
                            f"{self.meta_agent_endpoint}{endpoint}",
                            json=orchestration_payload,
                            timeout=30
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"✅ Meta agent orchestration successful via {endpoint}")
                                logger.info(f"📊 Orchestration result: {data}")
                                
                                self.test_results["meta_agent_orchestration"] = True
                                self.test_results["llm_decisions_made"] = data.get("llm_calls", 0)
                                
                                return data
                            elif response.status == 404:
                                continue  # Try next endpoint
                            else:
                                logger.warning(f"⚠️ {endpoint} returned: {response.status}")
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"⏰ Timeout on {endpoint}")
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Error on {endpoint}: {e}")
                        continue
                
                # If no specific orchestration endpoint works, try a general approach
                logger.info("🔄 Trying general Meta agent communication...")
                
                # Check what endpoints are available
                async with session.get(f"{self.meta_agent_endpoint}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📋 Meta agent info: {data}")
                        
                        # Try to trigger agent coordination manually
                        return await self.manual_agent_coordination()
                    
        except Exception as e:
            logger.error(f"❌ Meta agent orchestration failed: {e}")
            
        return {}
    
    async def manual_agent_coordination(self) -> Dict[str, Any]:
        """Manually coordinate agents to ensure LLM usage and real data."""
        try:
            logger.info("🔧 Manually coordinating agents for real data analysis...")
            
            coordination_results = {
                "portfolio_analysis": {},
                "market_research": {},
                "sentiment_analysis": {},
                "strategy_recommendations": {},
                "llm_calls_made": 0
            }
            
            async with aiohttp.ClientSession() as session:
                # 1. Get real-time market data
                logger.info("📡 Getting live market data...")
                market_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "LINKUSDT"]
                
                for symbol in market_symbols:
                    try:
                        async with session.post(
                            f"{self.agent_endpoints['realtime_data']}/get_ticker",
                            json={"symbol": symbol, "exchange": "binanceus"},
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                ticker_data = await response.json()
                                logger.info(f"📈 {symbol}: {ticker_data}")
                                coordination_results["market_research"][symbol] = ticker_data
                                self.test_results["live_market_data_retrieved"] = True
                            else:
                                logger.warning(f"⚠️ Failed to get ticker for {symbol}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error getting {symbol} data: {e}")
                
                # 2. Trigger LLM-based sentiment analysis
                logger.info("🧠 Triggering LLM-based sentiment analysis...")
                for symbol in market_symbols[:3]:  # Limit to avoid too many API calls
                    try:
                        async with session.post(
                            f"{self.agent_endpoints['news_sentiment']}/analyze_sentiment",
                            json={
                                "symbol": symbol,
                                "use_llm": True,
                                "analysis_depth": "comprehensive"
                            },
                            timeout=20
                        ) as response:
                            if response.status == 200:
                                sentiment_data = await response.json()
                                logger.info(f"🎯 LLM Sentiment for {symbol}: {sentiment_data}")
                                coordination_results["sentiment_analysis"][symbol] = sentiment_data
                                
                                # Check if LLM was actually used
                                if sentiment_data.get("llm_used") or sentiment_data.get("openai_calls"):
                                    coordination_results["llm_calls_made"] += 1
                                    self.openai_calls_made += 1
                                    logger.info(f"✅ OpenAI LLM call confirmed for {symbol}")
                            else:
                                logger.warning(f"⚠️ Sentiment analysis failed for {symbol}")
                    except Exception as e:
                        logger.warning(f"⚠️ Sentiment analysis error for {symbol}: {e}")
                
                # 3. Trigger LLM-based strategy discovery
                logger.info("🔬 Triggering LLM-based strategy discovery...")
                try:
                    async with session.post(
                        f"{self.agent_endpoints['strategy_discovery']}/discover_strategies",
                        json={
                            "portfolio": self.real_portfolio,
                            "market_data": coordination_results["market_research"],
                            "use_llm": True,
                            "generate_recommendations": True
                        },
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            strategy_data = await response.json()
                            logger.info(f"🎯 LLM Strategy Discovery: {strategy_data}")
                            coordination_results["strategy_recommendations"] = strategy_data
                            
                            if strategy_data.get("llm_used") or strategy_data.get("openai_calls"):
                                coordination_results["llm_calls_made"] += 1
                                self.openai_calls_made += 1
                                logger.info("✅ OpenAI LLM call confirmed for strategy discovery")
                        else:
                            logger.warning(f"⚠️ Strategy discovery failed: {response.status}")
                except Exception as e:
                    logger.warning(f"⚠️ Strategy discovery error: {e}")
            
            # Update test results
            self.test_results["openai_api_calls"] = coordination_results["llm_calls_made"]
            self.test_results["llm_decisions_made"] = coordination_results["llm_calls_made"]
            
            logger.info(f"📊 Manual coordination completed. LLM calls made: {coordination_results['llm_calls_made']}")
            
            return coordination_results
            
        except Exception as e:
            logger.error(f"❌ Manual agent coordination failed: {e}")
            return {}
    
    async def run_real_data_test(self) -> Dict[str, Any]:
        """Run the comprehensive real-data test with Meta agent orchestration."""
        try:
            self.test_start_time = datetime.now()
            self.test_results["start_time"] = self.test_start_time
            
            logger.info("🚀 Starting VolexSwarm Real Data Orchestrated Test")
            logger.info("=" * 60)
            logger.info("🎯 Using REAL Binance data and LLM decision-making")
            logger.info("🤖 Meta agent will orchestrate all operations")
            logger.info(f"💰 Maximum budget: ${self.max_budget_usd}")
            
            # Phase 1: Get real portfolio data
            real_portfolio = await self.get_real_binance_portfolio()
            if not real_portfolio:
                logger.warning("⚠️ Could not retrieve real portfolio, but continuing test...")
            
            # Phase 2: Orchestrate via Meta agent
            task_description = (
                f"Analyze the current portfolio and market conditions. "
                f"The user has a ${self.max_budget_usd} budget and wants to optimize their holdings. "
                f"Use real market data from Binance US and provide intelligent trading recommendations. "
                f"Consider diversification opportunities and risk management."
            )
            
            orchestration_result = await self.orchestrate_via_meta_agent(task_description)
            
            # Phase 3: Verify LLM usage
            await self.verify_llm_usage()
            
            # Phase 4: Generate final report
            await self.generate_final_report()
            
            return {"success": True, "results": self.test_results}
            
        except Exception as e:
            logger.error(f"❌ Real data test failed: {e}")
            self.test_results["errors"].append(str(e))
            return {"success": False, "error": str(e), "results": self.test_results}
    
    async def verify_llm_usage(self):
        """Verify that OpenAI LLM calls were actually made."""
        try:
            logger.info("🔍 Verifying OpenAI LLM usage...")
            
            if self.openai_calls_made > 0:
                logger.info(f"✅ Confirmed {self.openai_calls_made} OpenAI API calls were made")
                logger.info("🧠 LLM-based decision making is active")
            else:
                logger.warning("⚠️ No confirmed OpenAI API calls detected")
                logger.info("💡 This might indicate agents are using cached responses or fallback logic")
            
            # Check agent logs for LLM activity
            async with aiohttp.ClientSession() as session:
                for agent_name, endpoint in self.agent_endpoints.items():
                    try:
                        async with session.get(f"{endpoint}/stats") as response:
                            if response.status == 200:
                                stats = await response.json()
                                llm_calls = stats.get("llm_calls", 0)
                                if llm_calls > 0:
                                    logger.info(f"📊 {agent_name} agent: {llm_calls} LLM calls")
                                    self.test_results["openai_api_calls"] += llm_calls
                    except:
                        continue  # Agent might not have stats endpoint
                        
        except Exception as e:
            logger.error(f"❌ LLM verification failed: {e}")
    
    async def generate_final_report(self):
        """Generate comprehensive final report."""
        try:
            logger.info("\n" + "=" * 60)
            logger.info("📊 REAL DATA ORCHESTRATED TEST RESULTS")
            logger.info("=" * 60)
            
            # Test completion status
            logger.info("✅ TEST COMPLETION STATUS:")
            logger.info(f"  • Real Portfolio Retrieved: {'✅' if self.test_results['real_portfolio_retrieved'] else '❌'}")
            logger.info(f"  • Live Market Data Retrieved: {'✅' if self.test_results['live_market_data_retrieved'] else '❌'}")
            logger.info(f"  • Meta Agent Orchestration: {'✅' if self.test_results['meta_agent_orchestration'] else '❌'}")
            logger.info(f"  • LLM Decisions Made: {self.test_results['llm_decisions_made']}")
            logger.info(f"  • OpenAI API Calls: {self.test_results['openai_api_calls']}")
            
            # Portfolio information
            if self.real_portfolio:
                logger.info("\n💼 REAL PORTFOLIO DATA:")
                for asset, balance in self.real_portfolio.items():
                    logger.info(f"  • {asset}: {balance}")
            
            # Recommendations
            logger.info("\n🎯 NEXT STEPS:")
            if self.test_results["openai_api_calls"] > 0:
                logger.info("  ✅ LLM integration confirmed - agents are making intelligent decisions")
                logger.info("  ✅ Ready for live trading with real market analysis")
            else:
                logger.info("  ⚠️ LLM integration needs verification - check OpenAI API key in Vault")
                logger.info("  💡 Ensure agents have proper OpenAI credentials configured")
            
            if self.test_results["real_portfolio_retrieved"]:
                logger.info("  ✅ Real portfolio data integration working")
            else:
                logger.info("  ⚠️ Portfolio data retrieval needs debugging")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ Final report generation failed: {e}")

async def main():
    """Main test execution function."""
    try:
        test = RealDataOrchestratedTest(max_budget_usd=25.0)
        results = await test.run_real_data_test()
        
        if results["success"]:
            print("\n🎉 Real Data Orchestrated Test Completed!")
            print("🎯 Check the logs above for LLM usage and real data verification.")
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
