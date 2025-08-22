#!/usr/bin/env python3
"""
Test script for Phase 9.3 Real-Time Execution System

This script tests the real-time execution engine, enhanced execution agent,
and all related components to ensure they work correctly.
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.execution.real_time_execution_engine import (
    RealTimeExecutionEngine, RealTimeOrder, OrderPriority, OrderStatus,
    PositionUpdate, ExecutionAnalytics
)
from agents.execution.enhanced_execution_agent import EnhancedExecutionAgent, ExecutionConfig
from common.logging import get_logger

logger = get_logger("test_real_time_execution")

class RealTimeExecutionTester:
    """Test suite for real-time execution system."""
    
    def __init__(self):
        self.test_results = []
        self.engine = None
        self.agent = None
    
    async def run_all_tests(self):
        """Run all tests for the real-time execution system."""
        logger.info("Starting Phase 9.3 Real-Time Execution System Tests")
        
        try:
            # Test 1: Real-Time Execution Engine
            await self.test_execution_engine()
            
            # Test 2: Order Priority Queue
            await self.test_order_priority_queue()
            
            # Test 3: Position Tracking
            await self.test_position_tracking()
            
            # Test 4: Execution Analytics
            await self.test_execution_analytics()
            
            # Test 5: Enhanced Execution Agent (simplified)
            await self.test_enhanced_execution_agent()
            
            # Test 6: Integration Tests
            await self.test_integration()
            
            # Print results
            self.print_test_results()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            raise
    
    async def test_execution_engine(self):
        """Test the real-time execution engine."""
        logger.info("Testing Real-Time Execution Engine...")
        
        try:
            # Initialize engine
            self.engine = RealTimeExecutionEngine()
            
            # Test engine startup
            await self.engine.start()
            assert self.engine.is_running, "Engine should be running"
            self.record_test_result("Engine Startup", True, "Engine started successfully")
            
            # Test order submission
            order = RealTimeOrder(
                order_id="test_order_1",
                symbol="BTC/USDT",
                side="buy",
                amount=0.001,
                priority=OrderPriority.HIGH
            )
            
            success = await self.engine.submit_order(order)
            assert success, "Order submission should succeed"
            self.record_test_result("Order Submission", True, "Order submitted successfully")
            
            # Wait for execution
            await asyncio.sleep(0.2)
            
            # Check order status
            recent_orders = self.engine.order_queue.get_recent_orders()
            assert len(recent_orders) > 0, "Should have recent orders"
            
            executed_order = recent_orders[0]
            assert executed_order.status in [OrderStatus.FILLED, OrderStatus.FAILED], "Order should have final status"
            
            self.record_test_result("Order Execution", True, f"Order executed with status: {executed_order.status.value}")
            
            # Test engine shutdown
            await self.engine.stop()
            assert not self.engine.is_running, "Engine should be stopped"
            self.record_test_result("Engine Shutdown", True, "Engine stopped successfully")
            
        except Exception as e:
            self.record_test_result("Execution Engine", False, str(e))
            raise
    
    async def test_order_priority_queue(self):
        """Test order priority queue functionality."""
        logger.info("Testing Order Priority Queue...")
        
        try:
            # Create orders with different priorities
            orders = [
                RealTimeOrder(order_id="low_priority", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.LOW),
                RealTimeOrder(order_id="high_priority", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.HIGH),
                RealTimeOrder(order_id="critical_priority", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.CRITICAL),
                RealTimeOrder(order_id="normal_priority", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.NORMAL)
            ]
            
            # Add orders to queue
            for order in orders:
                self.engine.order_queue.add_order(order)
            
            # Check queue stats
            stats = self.engine.order_queue.get_queue_stats()
            assert stats["queue_size"] == 4, f"Queue should have 4 orders, got {stats['queue_size']}"
            self.record_test_result("Queue Stats", True, f"Queue contains {stats['queue_size']} orders")
            
            # Test priority ordering
            processed_orders = []
            for _ in range(4):
                order = self.engine.order_queue.get_next_order()
                if order:
                    processed_orders.append(order)
                    self.engine.order_queue.mark_order_completed(order.order_id)
            
            # Check priority order (CRITICAL, HIGH, NORMAL, LOW)
            expected_order = ["critical_priority", "high_priority", "normal_priority", "low_priority"]
            actual_order = [order.order_id for order in processed_orders]
            
            assert actual_order == expected_order, f"Priority order incorrect. Expected: {expected_order}, Got: {actual_order}"
            self.record_test_result("Priority Ordering", True, "Orders processed in correct priority order")
            
        except Exception as e:
            self.record_test_result("Order Priority Queue", False, str(e))
            raise
    
    async def test_position_tracking(self):
        """Test position tracking functionality."""
        logger.info("Testing Position Tracking...")
        
        try:
            # Create test positions
            position1 = PositionUpdate(
                symbol="BTC/USDT",
                side="long",
                amount=0.001,
                entry_price=50000.0,
                current_price=51000.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                timestamp=datetime.utcnow(),
                exchange="binance"
            )
            
            position2 = PositionUpdate(
                symbol="ETH/USDT",
                side="short",
                amount=0.01,
                entry_price=3000.0,
                current_price=2900.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                timestamp=datetime.utcnow(),
                exchange="binance"
            )
            
            # Update positions
            self.engine.position_tracker.update_position(position1)
            self.engine.position_tracker.update_position(position2)
            
            # Check position count
            all_positions = self.engine.position_tracker.get_all_positions()
            assert len(all_positions) == 2, f"Should have 2 positions, got {len(all_positions)}"
            self.record_test_result("Position Count", True, f"Tracking {len(all_positions)} positions")
            
            # Check PnL calculation
            portfolio_pnl = self.engine.position_tracker.calculate_portfolio_pnl()
            assert "total_pnl" in portfolio_pnl, "Portfolio PnL should be calculated"
            self.record_test_result("PnL Calculation", True, f"Portfolio PnL: {portfolio_pnl['total_pnl']}")
            
            # Check position retrieval
            btc_position = self.engine.position_tracker.get_position("BTC/USDT")
            assert btc_position is not None, "Should retrieve BTC position"
            assert btc_position.symbol == "BTC/USDT", "Position symbol should match"
            self.record_test_result("Position Retrieval", True, "Position retrieved successfully")
            
        except Exception as e:
            self.record_test_result("Position Tracking", False, str(e))
            raise
    
    async def test_execution_analytics(self):
        """Test execution analytics functionality."""
        logger.info("Testing Execution Analytics...")
        
        try:
            # Reset analytics for clean test
            self.engine.execution_analytics = ExecutionAnalytics()
            
            # Create test orders for analytics
            test_orders = [
                RealTimeOrder(order_id="analytics_test_1", symbol="BTC/USDT", side="buy", amount=0.001, status=OrderStatus.FILLED),
                RealTimeOrder(order_id="analytics_test_2", symbol="ETH/USDT", side="sell", amount=0.01, status=OrderStatus.FILLED),
                RealTimeOrder(order_id="analytics_test_3", symbol="BTC/USDT", side="buy", amount=0.002, status=OrderStatus.FAILED)
            ]
            
            # Record executions
            for i, order in enumerate(test_orders):
                if order.status == OrderStatus.FILLED:
                    order.filled_at = datetime.utcnow()
                    order.filled_quantity = order.amount
                    order.filled_price = 50000.0 + i * 100
                    order.commission = 0.1
                    order.slippage = 0.0001
                
                self.engine.execution_analytics.record_execution(order, 0.1 + i * 0.05)
            
            # Get performance report
            report = self.engine.execution_analytics.get_performance_report()
            
            # Check basic metrics
            basic_metrics = report.get("basic_metrics", {})
            assert basic_metrics["total_orders"] == 3, f"Should have 3 total orders, got {basic_metrics['total_orders']}"
            assert basic_metrics["successful_orders"] == 2, f"Should have 2 successful orders, got {basic_metrics['successful_orders']}"
            assert basic_metrics["failed_orders"] == 1, f"Should have 1 failed order, got {basic_metrics['failed_orders']}"
            
            self.record_test_result("Basic Analytics", True, f"Success rate: {basic_metrics['success_rate']:.2%}")
            
            # Check quality metrics
            quality_metrics = report.get("quality_metrics", {})
            assert "avg_execution_time" in quality_metrics, "Should have average execution time"
            assert "avg_slippage" in quality_metrics, "Should have average slippage"
            
            self.record_test_result("Quality Analytics", True, f"Avg execution time: {quality_metrics['avg_execution_time']:.3f}s")
            
            # Check latency stats
            latency_stats = report.get("latency_stats", {})
            assert "avg" in latency_stats, "Should have latency statistics"
            
            self.record_test_result("Latency Analytics", True, f"Avg latency: {latency_stats['avg']:.3f}s")
            
        except Exception as e:
            self.record_test_result("Execution Analytics", False, str(e))
            raise
    
    async def test_enhanced_execution_agent(self):
        """Test enhanced execution agent (simplified without database)."""
        logger.info("Testing Enhanced Execution Agent...")
        
        try:
            # Initialize agent with test configuration (no database)
            config = ExecutionConfig(
                max_order_size=1000.0,
                max_daily_volume=10000.0,
                enable_real_time=True,
                enable_analytics=True,
                enable_position_tracking=True
            )
            
            self.agent = EnhancedExecutionAgent(config=config)
            
            # Test agent initialization (without infrastructure)
            # Skip infrastructure initialization for testing
            self.agent.db_client = None
            self.agent.ws_client = None
            
            # Test real-time trade execution
            result = await self.agent.execute_trade_real_time(
                symbol="BTC/USDT",
                side="buy",
                amount=0.001,
                priority=OrderPriority.HIGH
            )
            
            assert result["success"], f"Trade execution should succeed: {result.get('error')}"
            self.record_test_result("Real-Time Trade Execution", True, f"Order ID: {result['order_id']}")
            
            # Test position retrieval
            positions = await self.agent.get_real_time_positions()
            assert isinstance(positions, list), "Positions should be a list"
            self.record_test_result("Position Retrieval", True, f"Retrieved {len(positions)} positions")
            
            # Test portfolio PnL
            pnl = await self.agent.get_portfolio_pnl()
            assert "total_pnl" in pnl, "Portfolio PnL should be available"
            self.record_test_result("Portfolio PnL", True, f"Total PnL: {pnl['total_pnl']}")
            
            # Test execution analytics
            analytics = await self.agent.get_execution_analytics()
            assert "basic_metrics" in analytics, "Analytics should be available"
            self.record_test_result("Execution Analytics", True, "Analytics retrieved successfully")
            
            # Test engine status
            status = await self.agent.get_engine_status()
            assert "is_running" in status, "Engine status should be available"
            self.record_test_result("Engine Status", True, f"Engine running: {status['is_running']}")
            
            # Test strategy optimization
            optimization = await self.agent.optimize_execution_strategy("BTC/USDT", "buy", 0.001)
            assert "recommendation" in optimization, "Optimization should provide recommendations"
            self.record_test_result("Strategy Optimization", True, optimization["recommendation"])
            
            # Test agent status
            agent_status = self.agent.get_agent_status()
            assert "real_time_enabled" in agent_status, "Agent status should include real-time info"
            self.record_test_result("Agent Status", True, f"Real-time enabled: {agent_status['real_time_enabled']}")
            
            # Shutdown agent
            await self.agent.shutdown()
            self.record_test_result("Agent Shutdown", True, "Agent shutdown successfully")
            
        except Exception as e:
            self.record_test_result("Enhanced Execution Agent", False, str(e))
            raise
    
    async def test_integration(self):
        """Test integration between components."""
        logger.info("Testing Integration...")
        
        try:
            # Test signal to execution flow
            # Simulate a signal from the signal agent
            signal_data = {
                "signal_id": "test_signal_1",
                "symbol": "BTC/USDT",
                "side": "buy",
                "confidence": 0.85,
                "priority": "HIGH"
            }
            
            # Create order from signal
            order = RealTimeOrder(
                order_id=str(uuid.uuid4()),
                signal_id=signal_data["signal_id"],
                symbol=signal_data["symbol"],
                side=signal_data["side"],
                amount=0.001,
                priority=OrderPriority.HIGH if signal_data["priority"] == "HIGH" else OrderPriority.NORMAL
            )
            
            # Submit to engine
            success = await self.engine.submit_order(order)
            assert success, "Signal-based order should be submitted successfully"
            self.record_test_result("Signal Integration", True, "Signal converted to order successfully")
            
            # Test position update flow
            position = PositionUpdate(
                symbol="BTC/USDT",
                side="long",
                amount=0.001,
                entry_price=50000.0,
                current_price=50500.0,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                timestamp=datetime.utcnow(),
                exchange="binance"
            )
            
            # Update position
            self.engine.position_tracker.update_position(position)
            
            # Check portfolio impact
            portfolio_pnl = self.engine.position_tracker.calculate_portfolio_pnl()
            assert portfolio_pnl["total_pnl"] != 0, "Portfolio PnL should reflect position changes"
            self.record_test_result("Position Integration", True, f"Portfolio updated: {portfolio_pnl['total_pnl']}")
            
            # Test analytics integration
            analytics = self.engine.execution_analytics.get_performance_report()
            assert analytics["basic_metrics"]["total_orders"] > 0, "Analytics should track orders"
            self.record_test_result("Analytics Integration", True, "Analytics integrated successfully")
            
        except Exception as e:
            self.record_test_result("Integration", False, str(e))
            raise
    
    def record_test_result(self, test_name: str, passed: bool, message: str):
        """Record a test result."""
        result = {
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    def print_test_results(self):
        """Print test results summary."""
        logger.info("\n" + "="*60)
        logger.info("PHASE 9.3 REAL-TIME EXECUTION SYSTEM TEST RESULTS")
        logger.info("="*60)
        
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        logger.info("\nDetailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            logger.info(f"{status} {result['test']}: {result['message']}")
        
        if passed == total:
            logger.info("\n🎉 ALL TESTS PASSED! Phase 9.3 Real-Time Execution System is working correctly.")
        else:
            logger.error(f"\n⚠️  {total - passed} TESTS FAILED. Please review the implementation.")
        
        logger.info("="*60)

async def main():
    """Main test function."""
    try:
        tester = RealTimeExecutionTester()
        await tester.run_all_tests()
        
        # Save test results to file
        with open("real_time_execution_test_results.json", "w") as f:
            json.dump(tester.test_results, f, indent=2, default=str)
        
        logger.info("Test results saved to real_time_execution_test_results.json")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 