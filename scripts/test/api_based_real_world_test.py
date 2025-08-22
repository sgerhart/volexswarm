#!/usr/bin/env python3
"""
VolexSwarm API-Based Real-World Trading Test
Tests all agents via their API endpoints with live Binance US trading using a $25 budget.

This script orchestrates a comprehensive test by making API calls to:
- Real-time data agent (port 8026)
- News sentiment agent (port 8024) 
- Strategy discovery agent (port 8025)
- Execution agent (port 8002)
- Monitor agent (port 8008)

SAFETY FEATURES:
- Maximum position size limits
- Stop-loss protection
- Budget tracking
- Emergency shutdown
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
import time
import aiohttp

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.logging import get_logger

logger = get_logger("api_real_world_test")

class APIBasedRealWorldTest:
    """API-based real-world trading test orchestrator."""
    
    def __init__(self, budget: float = 25.0):
        """Initialize the test suite."""
        self.budget = budget
        self.remaining_budget = budget
        self.max_position_size = budget * 0.2  # Max 20% per position
        self.stop_loss_percentage = 0.05  # 5% stop loss
        
        # Agent API endpoints
        self.agent_endpoints = {
            "realtime_data": "http://localhost:8026",
            "news_sentiment": "http://localhost:8024",
            "strategy_discovery": "http://localhost:8025",
            "execution": "http://localhost:8002",
            "monitor": "http://localhost:8008"
        }
        
        # Test configuration
        self.test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        self.test_duration_minutes = 60  # 1 hour test
        self.position_check_interval = 30  # Check positions every 30 seconds
        
        # Test state
        self.test_start_time = None
        self.positions = {}
        self.trades_executed = []
        self.test_results = {
            "start_time": None,
            "end_time": None,
            "initial_budget": budget,
            "final_balance": 0.0,
            "total_pnl": 0.0,
            "trades_count": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "max_drawdown": 0.0,
            "agent_performance": {},
            "errors": []
        }
        
        # Safety flags
        self.emergency_stop = False
        self.max_loss_reached = False
        
    async def check_agent_health(self) -> Dict[str, bool]:
        """Check health of all agents via their API endpoints."""
        health_status = {}
        
        async with aiohttp.ClientSession() as session:
            for agent_name, endpoint in self.agent_endpoints.items():
                try:
                    async with session.get(f"{endpoint}/health", timeout=5) as response:
                        if response.status == 200:
                            data = await response.json()
                            health_status[agent_name] = True
                            logger.info(f"✅ {agent_name} agent is healthy")
                        else:
                            health_status[agent_name] = False
                            logger.error(f"❌ {agent_name} agent health check failed: {response.status}")
                except Exception as e:
                    health_status[agent_name] = False
                    logger.error(f"❌ {agent_name} agent unreachable: {e}")
        
        return health_status
    
    async def verify_exchange_connection(self) -> bool:
        """Verify Binance US connection through execution agent."""
        try:
            logger.info("🔐 Verifying Binance US connection via execution agent...")
            
            async with aiohttp.ClientSession() as session:
                # Check portfolio status
                async with session.get(f"{self.agent_endpoints['execution']}/portfolio/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            balance = data.get("balance", {}).get("USDT", 0.0)
                            logger.info(f"✅ Binance US connection verified. Available balance: {balance} USDT")
                            
                            if balance < self.budget:
                                logger.warning(f"⚠️ Available balance ({balance} USDT) is less than test budget ({self.budget} USDT)")
                                self.budget = min(balance * 0.9, self.budget)  # Use 90% of available balance
                                self.remaining_budget = self.budget
                                logger.info(f"Adjusted test budget to {self.budget} USDT")
                            
                            return True
                        else:
                            logger.error(f"❌ Portfolio status failed: {data.get('message')}")
                            return False
                    else:
                        logger.error(f"❌ Portfolio status API call failed: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Exchange connection verification failed: {e}")
            return False
    
    async def setup_real_time_data(self) -> bool:
        """Set up real-time data streams via realtime data agent API."""
        try:
            logger.info("📡 Setting up real-time data streams...")
            
            async with aiohttp.ClientSession() as session:
                # Connect to Binance US WebSocket
                connect_payload = {
                    "exchange_name": "binanceus",
                    "symbols": self.test_symbols
                }
                
                async with session.post(
                    f"{self.agent_endpoints['realtime_data']}/connect",
                    json=connect_payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            logger.info("✅ Connected to Binance US WebSocket")
                        else:
                            logger.error(f"❌ WebSocket connection failed: {data.get('message')}")
                            return False
                    else:
                        logger.error(f"❌ WebSocket connection API call failed: {response.status}")
                        return False
                
                # Subscribe to relevant channels
                for symbol in self.test_symbols:
                    for channel in ["ticker", "kline_1m", "trade"]:
                        subscribe_payload = {
                            "exchange_name": "binanceus",
                            "channel": channel,
                            "symbol": symbol
                        }
                        
                        async with session.post(
                            f"{self.agent_endpoints['realtime_data']}/subscribe",
                            json=subscribe_payload
                        ) as response:
                            if response.status == 200:
                                logger.info(f"✅ Subscribed to {channel} for {symbol}")
                            else:
                                logger.warning(f"⚠️ Failed to subscribe to {channel} for {symbol}")
                
                # Wait for initial data
                await asyncio.sleep(5)
                logger.info("✅ Real-time data streams established")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to setup real-time data: {e}")
            return False
    
    async def run_strategy_discovery(self) -> Dict[str, Any]:
        """Run strategy discovery via strategy discovery agent API."""
        try:
            logger.info("🧠 Running strategy discovery...")
            
            strategies = {}
            async with aiohttp.ClientSession() as session:
                for symbol in self.test_symbols:
                    logger.info(f"Discovering strategies for {symbol}...")
                    
                    strategy_payload = {
                        "symbol": symbol,
                        "timeframe": "1h",
                        "lookback_days": 30,
                        "risk_profile": "conservative"  # Conservative for live testing
                    }
                    
                    async with session.post(
                        f"{self.agent_endpoints['strategy_discovery']}/discover",
                        json=strategy_payload
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("success"):
                                strategies[symbol] = data.get("strategies", [])
                                logger.info(f"Found {len(strategies[symbol])} strategies for {symbol}")
                            else:
                                logger.warning(f"No strategies found for {symbol}: {data.get('message')}")
                                strategies[symbol] = []
                        else:
                            logger.warning(f"Strategy discovery API call failed for {symbol}: {response.status}")
                            strategies[symbol] = []
            
            return strategies
            
        except Exception as e:
            logger.error(f"❌ Strategy discovery failed: {e}")
            return {}
    
    async def analyze_news_sentiment(self) -> Dict[str, Any]:
        """Analyze news sentiment via news sentiment agent API."""
        try:
            logger.info("📰 Analyzing news sentiment...")
            
            sentiment_results = {}
            async with aiohttp.ClientSession() as session:
                for symbol in self.test_symbols:
                    sentiment_payload = {
                        "symbol": symbol,
                        "timeframe": "1h"
                    }
                    
                    async with session.post(
                        f"{self.agent_endpoints['news_sentiment']}/analyze",
                        json=sentiment_payload
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("success"):
                                sentiment_results[symbol] = data.get("sentiment", {})
                                sentiment_score = sentiment_results[symbol].get("overall_sentiment", "neutral")
                                logger.info(f"Sentiment for {symbol}: {sentiment_score}")
                            else:
                                sentiment_results[symbol] = {"overall_sentiment": "neutral", "confidence": 0.5}
                        else:
                            logger.warning(f"Sentiment analysis API call failed for {symbol}: {response.status}")
                            sentiment_results[symbol] = {"overall_sentiment": "neutral", "confidence": 0.5}
            
            return sentiment_results
            
        except Exception as e:
            logger.error(f"❌ News sentiment analysis failed: {e}")
            return {}
    
    async def execute_test_trade(self, symbol: str, side: str, amount: float, reason: str) -> Dict[str, Any]:
        """Execute a test trade via execution agent API."""
        try:
            # Safety checks
            if self.emergency_stop or self.max_loss_reached:
                logger.warning("🛑 Trading halted due to safety conditions")
                return {"success": False, "reason": "safety_halt"}
            
            if amount > self.max_position_size:
                logger.warning(f"⚠️ Trade amount ({amount}) exceeds max position size ({self.max_position_size})")
                amount = self.max_position_size
            
            if amount > self.remaining_budget:
                logger.warning(f"⚠️ Trade amount ({amount}) exceeds remaining budget ({self.remaining_budget})")
                amount = self.remaining_budget * 0.9
            
            if amount < 10:  # Minimum trade size
                logger.warning(f"⚠️ Trade amount ({amount}) below minimum size")
                return {"success": False, "reason": "amount_too_small"}
            
            logger.info(f"🔄 Executing {side} trade: {amount} USDT of {symbol} - Reason: {reason}")
            
            # Execute the trade via API
            trade_payload = {
                "symbol": symbol,
                "side": side,
                "amount": amount,
                "order_type": "market",
                "exchange": "binance"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.agent_endpoints['execution']}/execute",
                    json=trade_payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            # Update tracking
                            self.trades_executed.append({
                                "timestamp": datetime.now(),
                                "symbol": symbol,
                                "side": side,
                                "amount": amount,
                                "reason": reason,
                                "result": data
                            })
                            
                            # Update budget tracking
                            if side == "buy":
                                self.remaining_budget -= amount
                            
                            logger.info(f"✅ Trade executed successfully: {data}")
                            return data
                        else:
                            logger.error(f"❌ Trade execution failed: {data}")
                            return data
                    else:
                        logger.error(f"❌ Trade execution API call failed: {response.status}")
                        return {"success": False, "error": f"API call failed: {response.status}"}
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def monitor_positions(self):
        """Monitor positions via execution agent API."""
        try:
            while not self.emergency_stop and (datetime.now() - self.test_start_time).seconds < self.test_duration_minutes * 60:
                async with aiohttp.ClientSession() as session:
                    # Get current portfolio status
                    async with session.get(f"{self.agent_endpoints['execution']}/portfolio/status") as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("success"):
                                positions = data.get("positions", {})
                                total_pnl = data.get("total_pnl", 0.0)
                                
                                # Check for stop-loss conditions
                                if total_pnl < -self.budget * self.stop_loss_percentage:
                                    logger.warning(f"🛑 Stop-loss triggered! PnL: {total_pnl}")
                                    self.max_loss_reached = True
                                    await self.emergency_close_positions()
                                    break
                                
                                # Log position status
                                logger.info(f"📊 Portfolio PnL: {total_pnl:.2f} USDT, Positions: {len(positions)}")
                                
                                # Update test results
                                self.test_results["total_pnl"] = total_pnl
                                self.test_results["max_drawdown"] = min(self.test_results["max_drawdown"], total_pnl)
                
                await asyncio.sleep(self.position_check_interval)
                
        except Exception as e:
            logger.error(f"❌ Position monitoring error: {e}")
            self.emergency_stop = True
    
    async def emergency_close_positions(self):
        """Emergency close all positions via execution agent API."""
        try:
            logger.warning("🚨 Emergency closing all positions...")
            
            async with aiohttp.ClientSession() as session:
                # Get current positions
                async with session.get(f"{self.agent_endpoints['execution']}/portfolio/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            positions = data.get("positions", {})
                            
                            for symbol, position in positions.items():
                                if position.get("amount", 0) > 0:
                                    # Close long position
                                    await self.execute_test_trade(
                                        symbol=symbol,
                                        side="sell",
                                        amount=position["amount"],
                                        reason="emergency_close"
                                    )
            
            logger.info("✅ Emergency position closure completed")
            
        except Exception as e:
            logger.error(f"❌ Emergency closure failed: {e}")
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the comprehensive real-world trading test via APIs."""
        try:
            self.test_start_time = datetime.now()
            self.test_results["start_time"] = self.test_start_time
            
            logger.info("🎯 Starting VolexSwarm API-Based Real-World Trading Test")
            logger.info(f"💰 Budget: ${self.budget}")
            logger.info(f"⏱️ Duration: {self.test_duration_minutes} minutes")
            logger.info(f"📈 Test symbols: {', '.join(self.test_symbols)}")
            
            # Phase 1: Check agent health
            health_status = await self.check_agent_health()
            unhealthy_agents = [name for name, healthy in health_status.items() if not healthy]
            if unhealthy_agents:
                logger.error(f"❌ Unhealthy agents: {unhealthy_agents}")
                return {"success": False, "error": f"Unhealthy agents: {unhealthy_agents}"}
            
            # Phase 2: Verify exchange connection
            if not await self.verify_exchange_connection():
                return {"success": False, "error": "Exchange connection failed"}
            
            # Phase 3: Setup real-time data
            if not await self.setup_real_time_data():
                return {"success": False, "error": "Real-time data setup failed"}
            
            # Phase 4: Run strategy discovery
            strategies = await self.run_strategy_discovery()
            
            # Phase 5: Analyze news sentiment
            sentiment = await self.analyze_news_sentiment()
            
            # Phase 6: Start position monitoring
            monitor_task = asyncio.create_task(self.monitor_positions())
            
            # Phase 7: Execute test trades based on signals
            await self.execute_signal_based_trades(strategies, sentiment)
            
            # Phase 8: Wait for test completion or emergency stop
            await monitor_task
            
            # Phase 9: Final cleanup and results
            await self.finalize_test_results()
            
            logger.info("🏁 API-based real-world trading test completed")
            return {"success": True, "results": self.test_results}
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            self.test_results["errors"].append(str(e))
            return {"success": False, "error": str(e), "results": self.test_results}
    
    async def execute_signal_based_trades(self, strategies: Dict, sentiment: Dict):
        """Execute trades based on strategy and sentiment signals."""
        try:
            logger.info("🎯 Executing signal-based trades...")
            
            for symbol in self.test_symbols:
                if self.emergency_stop or self.remaining_budget < 10:
                    break
                
                # Get strategy signals
                symbol_strategies = strategies.get(symbol, [])
                symbol_sentiment = sentiment.get(symbol, {})
                
                # Simple signal logic for testing
                if symbol_strategies and symbol_sentiment:
                    # Get best strategy
                    best_strategy = max(symbol_strategies, key=lambda x: x.get("score", 0)) if symbol_strategies else None
                    sentiment_score = symbol_sentiment.get("confidence", 0.5)
                    sentiment_direction = symbol_sentiment.get("overall_sentiment", "neutral")
                    
                    # Generate trading signal
                    if best_strategy and sentiment_score > 0.6:
                        if sentiment_direction == "positive" and best_strategy.get("recommendation") == "BUY":
                            # Execute buy trade
                            trade_amount = min(self.max_position_size, self.remaining_budget * 0.3)
                            await self.execute_test_trade(
                                symbol=symbol,
                                side="buy",
                                amount=trade_amount,
                                reason=f"strategy_sentiment_buy_{best_strategy.get('name', 'unknown')}"
                            )
                            
                            # Wait before next trade
                            await asyncio.sleep(60)  # 1 minute between trades
                
        except Exception as e:
            logger.error(f"❌ Signal-based trading failed: {e}")
    
    async def finalize_test_results(self):
        """Finalize and save test results."""
        try:
            self.test_results["end_time"] = datetime.now()
            self.test_results["trades_count"] = len(self.trades_executed)
            self.test_results["successful_trades"] = sum(1 for t in self.trades_executed if t["result"].get("success"))
            self.test_results["failed_trades"] = self.test_results["trades_count"] - self.test_results["successful_trades"]
            
            # Get final portfolio status via API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.agent_endpoints['execution']}/portfolio/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("success"):
                            self.test_results["final_balance"] = data.get("balance", {}).get("USDT", 0.0)
            
            # Print summary
            logger.info("📊 TEST RESULTS SUMMARY")
            logger.info(f"Duration: {self.test_results['end_time'] - self.test_results['start_time']}")
            logger.info(f"Initial Budget: ${self.test_results['initial_budget']}")
            logger.info(f"Final Balance: ${self.test_results['final_balance']}")
            logger.info(f"Total PnL: ${self.test_results['total_pnl']:.2f}")
            logger.info(f"Trades Executed: {self.test_results['trades_count']}")
            logger.info(f"Success Rate: {(self.test_results['successful_trades']/max(1,self.test_results['trades_count'])*100):.1f}%")
            logger.info(f"Max Drawdown: ${self.test_results['max_drawdown']:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Failed to finalize results: {e}")

async def main():
    """Main test execution function."""
    try:
        # Create test instance
        test = APIBasedRealWorldTest(budget=25.0)
        
        # Run comprehensive test
        results = await test.run_comprehensive_test()
        
        if results["success"]:
            print("✅ API-based real-world trading test completed successfully!")
            return 0
        else:
            print(f"❌ API-based real-world trading test failed: {results.get('error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
