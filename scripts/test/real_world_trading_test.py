#!/usr/bin/env python3
"""
VolexSwarm Real-World Trading Test Suite
Tests all agents with live Binance US trading using a $25 budget.

This script orchestrates a comprehensive test of:
- Real-time data collection
- News sentiment analysis
- Strategy discovery
- Risk management
- Trade execution
- Portfolio monitoring

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

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.logging import get_logger
from common.vault import get_vault_client, get_exchange_credentials
from common.db import get_db_client
from agents.execution.agentic_execution_agent import AgenticExecutionAgent
from agents.realtime_data.agentic_realtime_data_agent import AgenticRealtimeDataAgent
from agents.news_sentiment.agentic_news_sentiment_agent import AgenticNewsSentimentAgent
from agents.strategy_discovery.agentic_strategy_discovery_agent import AgenticStrategyDiscoveryAgent
from agents.monitor.agentic_monitor_agent import AgenticMonitorAgent

logger = get_logger("real_world_trading_test")

class RealWorldTradingTest:
    """Comprehensive real-world trading test orchestrator."""
    
    def __init__(self, budget: float = 25.0):
        """Initialize the test suite."""
        self.budget = budget
        self.remaining_budget = budget
        self.max_position_size = budget * 0.2  # Max 20% per position
        self.stop_loss_percentage = 0.05  # 5% stop loss
        
        # Test configuration
        self.test_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        self.test_duration_minutes = 60  # 1 hour test
        self.position_check_interval = 30  # Check positions every 30 seconds
        
        # Agents
        self.execution_agent = None
        self.realtime_agent = None
        self.sentiment_agent = None
        self.strategy_agent = None
        self.monitor_agent = None
        
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
        
    async def initialize_agents(self) -> bool:
        """Initialize all agents for testing."""
        try:
            logger.info("🚀 Initializing agents for real-world testing...")
            
            # Initialize execution agent
            logger.info("Initializing execution agent...")
            self.execution_agent = AgenticExecutionAgent()
            await self.execution_agent.initialize()
            
            # Initialize real-time data agent
            logger.info("Initializing real-time data agent...")
            self.realtime_agent = AgenticRealtimeDataAgent()
            await self.realtime_agent.initialize()
            
            # Initialize sentiment agent
            logger.info("Initializing sentiment agent...")
            self.sentiment_agent = AgenticNewsSentimentAgent()
            await self.sentiment_agent.initialize()
            
            # Initialize strategy discovery agent
            logger.info("Initializing strategy discovery agent...")
            self.strategy_agent = AgenticStrategyDiscoveryAgent()
            await self.strategy_agent.initialize()
            
            # Initialize monitor agent
            logger.info("Initializing monitor agent...")
            self.monitor_agent = AgenticMonitorAgent()
            await self.monitor_agent.initialize()
            
            logger.info("✅ All agents initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            return False
    
    async def verify_exchange_connection(self) -> bool:
        """Verify Binance US connection and credentials."""
        try:
            logger.info("🔐 Verifying Binance US connection...")
            
            # Check vault credentials
            credentials = get_exchange_credentials("binance")
            if not credentials:
                logger.error("❌ No Binance credentials found in Vault")
                return False
            
            # Test connection through execution agent
            portfolio_status = await self.execution_agent.get_portfolio_status("binance")
            if portfolio_status.get("status") != "success":
                logger.error("❌ Failed to connect to Binance US")
                return False
            
            # Check available balance
            balance = portfolio_status.get("balance", {}).get("USDT", 0.0)
            if balance < self.budget:
                logger.warning(f"⚠️ Available balance ({balance} USDT) is less than test budget ({self.budget} USDT)")
                self.budget = min(balance * 0.9, self.budget)  # Use 90% of available balance
                self.remaining_budget = self.budget
                logger.info(f"Adjusted test budget to {self.budget} USDT")
            
            logger.info(f"✅ Binance US connection verified. Available balance: {balance} USDT")
            return True
            
        except Exception as e:
            logger.error(f"❌ Exchange connection verification failed: {e}")
            return False
    
    async def setup_real_time_data(self) -> bool:
        """Set up real-time data streams for test symbols."""
        try:
            logger.info("📡 Setting up real-time data streams...")
            
            # Connect to Binance US WebSocket
            connection_result = await self.realtime_agent.connect_to_exchange({
                "exchange_name": "binanceus",
                "symbols": self.test_symbols
            })
            
            if not connection_result.get("success"):
                logger.error("❌ Failed to connect to real-time data")
                return False
            
            # Subscribe to relevant channels
            for symbol in self.test_symbols:
                for channel in ["ticker", "kline_1m", "trade"]:
                    await self.realtime_agent.subscribe_to_channel({
                        "exchange_name": "binanceus",
                        "channel": channel,
                        "symbol": symbol
                    })
            
            # Wait for initial data
            await asyncio.sleep(5)
            
            logger.info("✅ Real-time data streams established")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup real-time data: {e}")
            return False
    
    async def run_strategy_discovery(self) -> Dict[str, Any]:
        """Run strategy discovery for test symbols."""
        try:
            logger.info("🧠 Running strategy discovery...")
            
            strategies = {}
            for symbol in self.test_symbols:
                logger.info(f"Discovering strategies for {symbol}...")
                
                strategy_result = await self.strategy_agent.discover_strategies({
                    "symbol": symbol,
                    "timeframe": "1h",
                    "lookback_days": 30,
                    "risk_profile": "conservative"  # Conservative for live testing
                })
                
                if strategy_result.get("success"):
                    strategies[symbol] = strategy_result.get("strategies", [])
                    logger.info(f"Found {len(strategies[symbol])} strategies for {symbol}")
                else:
                    logger.warning(f"No strategies found for {symbol}")
                    strategies[symbol] = []
            
            return strategies
            
        except Exception as e:
            logger.error(f"❌ Strategy discovery failed: {e}")
            return {}
    
    async def analyze_news_sentiment(self) -> Dict[str, Any]:
        """Analyze current news sentiment for test symbols."""
        try:
            logger.info("📰 Analyzing news sentiment...")
            
            sentiment_results = {}
            for symbol in self.test_symbols:
                # Get news sentiment for the symbol
                sentiment_result = await self.sentiment_agent.analyze_news_sentiment({
                    "symbol": symbol,
                    "timeframe": "1h"
                })
                
                if sentiment_result.get("success"):
                    sentiment_results[symbol] = sentiment_result.get("sentiment", {})
                    logger.info(f"Sentiment for {symbol}: {sentiment_results[symbol].get('overall_sentiment', 'neutral')}")
                else:
                    sentiment_results[symbol] = {"overall_sentiment": "neutral", "confidence": 0.5}
            
            return sentiment_results
            
        except Exception as e:
            logger.error(f"❌ News sentiment analysis failed: {e}")
            return {}
    
    async def execute_test_trade(self, symbol: str, side: str, amount: float, reason: str) -> Dict[str, Any]:
        """Execute a test trade with safety checks."""
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
            
            # Execute the trade
            trade_result = await self.execution_agent.execute_trade(
                symbol=symbol,
                side=side,
                amount=amount,
                order_type="market",
                exchange="binance"
            )
            
            if trade_result.get("success"):
                # Update tracking
                self.trades_executed.append({
                    "timestamp": datetime.now(),
                    "symbol": symbol,
                    "side": side,
                    "amount": amount,
                    "reason": reason,
                    "result": trade_result
                })
                
                # Update budget tracking
                if side == "buy":
                    self.remaining_budget -= amount
                
                logger.info(f"✅ Trade executed successfully: {trade_result}")
                return trade_result
            else:
                logger.error(f"❌ Trade execution failed: {trade_result}")
                return trade_result
                
        except Exception as e:
            logger.error(f"❌ Trade execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def monitor_positions(self):
        """Monitor positions and apply risk management."""
        try:
            while not self.emergency_stop and (datetime.now() - self.test_start_time).seconds < self.test_duration_minutes * 60:
                # Get current portfolio status
                portfolio = await self.execution_agent.get_portfolio_status("binance")
                
                if portfolio.get("success"):
                    positions = portfolio.get("positions", {})
                    total_pnl = portfolio.get("total_pnl", 0.0)
                    
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
        """Emergency close all positions."""
        try:
            logger.warning("🚨 Emergency closing all positions...")
            
            portfolio = await self.execution_agent.get_portfolio_status("binance")
            if portfolio.get("success"):
                positions = portfolio.get("positions", {})
                
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
        """Run the comprehensive real-world trading test."""
        try:
            self.test_start_time = datetime.now()
            self.test_results["start_time"] = self.test_start_time
            
            logger.info("🎯 Starting VolexSwarm Real-World Trading Test")
            logger.info(f"💰 Budget: ${self.budget}")
            logger.info(f"⏱️ Duration: {self.test_duration_minutes} minutes")
            logger.info(f"📈 Test symbols: {', '.join(self.test_symbols)}")
            
            # Phase 1: Initialize agents
            if not await self.initialize_agents():
                return {"success": False, "error": "Agent initialization failed"}
            
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
            
            logger.info("🏁 Real-world trading test completed")
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
            
            # Get final portfolio status
            final_portfolio = await self.execution_agent.get_portfolio_status("binance")
            if final_portfolio.get("success"):
                self.test_results["final_balance"] = final_portfolio.get("balance", {}).get("USDT", 0.0)
            
            # Save results to database
            db_client = get_db_client()
            if db_client:
                await db_client.execute("""
                    INSERT INTO test_results (test_type, test_data, created_at)
                    VALUES ($1, $2, $3)
                """, "real_world_trading", json.dumps(self.test_results), datetime.now())
            
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
        test = RealWorldTradingTest(budget=25.0)
        
        # Run comprehensive test
        results = await test.run_comprehensive_test()
        
        if results["success"]:
            print("✅ Real-world trading test completed successfully!")
            return 0
        else:
            print(f"❌ Real-world trading test failed: {results.get('error')}")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
