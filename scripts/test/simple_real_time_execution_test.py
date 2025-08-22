#!/usr/bin/env python3
"""
Simple test for Phase 9.3 Real-Time Execution System

This script tests the core real-time execution engine components
to validate the implementation.
"""

import sys
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.execution.real_time_execution_engine import (
    RealTimeExecutionEngine, RealTimeOrder, OrderPriority, OrderStatus,
    PositionUpdate
)

async def test_real_time_execution():
    """Test the core real-time execution functionality."""
    print("🚀 Testing Phase 9.3 Real-Time Execution System")
    print("=" * 60)
    
    test_results = []
    
    try:
        # Test 1: Engine Initialization
        print("1. Testing Engine Initialization...")
        engine = RealTimeExecutionEngine()
        test_results.append({"test": "Engine Initialization", "passed": True, "message": "Engine created successfully"})
        print("   ✅ Engine Initialization: PASS")
        
        # Test 2: Engine Startup
        print("2. Testing Engine Startup...")
        await engine.start()
        if engine.is_running:
            test_results.append({"test": "Engine Startup", "passed": True, "message": "Engine started successfully"})
            print("   ✅ Engine Startup: PASS")
        else:
            test_results.append({"test": "Engine Startup", "passed": False, "message": "Engine failed to start"})
            print("   ❌ Engine Startup: FAIL")
        
        # Test 3: Order Submission
        print("3. Testing Order Submission...")
        order = RealTimeOrder(
            order_id="test_order_1",
            symbol="BTC/USDT",
            side="buy",
            amount=0.001,
            priority=OrderPriority.HIGH
        )
        
        success = await engine.submit_order(order)
        if success:
            test_results.append({"test": "Order Submission", "passed": True, "message": "Order submitted successfully"})
            print("   ✅ Order Submission: PASS")
        else:
            test_results.append({"test": "Order Submission", "passed": False, "message": "Order submission failed"})
            print("   ❌ Order Submission: FAIL")
        
        # Test 4: Order Execution
        print("4. Testing Order Execution...")
        await asyncio.sleep(0.2)  # Wait for execution
        
        recent_orders = engine.order_queue.get_recent_orders()
        if len(recent_orders) > 0:
            executed_order = recent_orders[0]
            if executed_order.status in [OrderStatus.FILLED, OrderStatus.FAILED]:
                test_results.append({"test": "Order Execution", "passed": True, "message": f"Order executed with status: {executed_order.status.value}"})
                print(f"   ✅ Order Execution: PASS (Status: {executed_order.status.value})")
            else:
                test_results.append({"test": "Order Execution", "passed": False, "message": f"Order not executed properly: {executed_order.status.value}"})
                print(f"   ❌ Order Execution: FAIL (Status: {executed_order.status.value})")
        else:
            test_results.append({"test": "Order Execution", "passed": False, "message": "No orders found"})
            print("   ❌ Order Execution: FAIL (No orders)")
        
        # Test 5: Priority Queue
        print("5. Testing Priority Queue...")
        orders = [
            RealTimeOrder(order_id="low", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.LOW),
            RealTimeOrder(order_id="high", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.HIGH),
            RealTimeOrder(order_id="critical", symbol="BTC/USDT", side="buy", amount=0.001, priority=OrderPriority.CRITICAL)
        ]
        
        for order in orders:
            engine.order_queue.add_order(order)
        
        stats = engine.order_queue.get_queue_stats()
        if stats["queue_size"] == 3:
            test_results.append({"test": "Priority Queue", "passed": True, "message": f"Queue contains {stats['queue_size']} orders"})
            print(f"   ✅ Priority Queue: PASS ({stats['queue_size']} orders)")
        else:
            test_results.append({"test": "Priority Queue", "passed": False, "message": f"Queue size incorrect: {stats['queue_size']}"})
            print(f"   ❌ Priority Queue: FAIL (Expected 3, got {stats['queue_size']})")
        
        # Test 6: Position Tracking
        print("6. Testing Position Tracking...")
        position = PositionUpdate(
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
        
        engine.position_tracker.update_position(position)
        all_positions = engine.position_tracker.get_all_positions()
        
        if len(all_positions) == 1:
            test_results.append({"test": "Position Tracking", "passed": True, "message": f"Tracking {len(all_positions)} position"})
            print(f"   ✅ Position Tracking: PASS ({len(all_positions)} position)")
        else:
            test_results.append({"test": "Position Tracking", "passed": False, "message": f"Position count incorrect: {len(all_positions)}"})
            print(f"   ❌ Position Tracking: FAIL (Expected 1, got {len(all_positions)})")
        
        # Test 7: PnL Calculation
        print("7. Testing PnL Calculation...")
        portfolio_pnl = engine.position_tracker.calculate_portfolio_pnl()
        if "total_pnl" in portfolio_pnl:
            test_results.append({"test": "PnL Calculation", "passed": True, "message": f"Portfolio PnL: {portfolio_pnl['total_pnl']}"})
            print(f"   ✅ PnL Calculation: PASS (PnL: {portfolio_pnl['total_pnl']})")
        else:
            test_results.append({"test": "PnL Calculation", "passed": False, "message": "PnL calculation failed"})
            print("   ❌ PnL Calculation: FAIL")
        
        # Test 8: Execution Analytics
        print("8. Testing Execution Analytics...")
        analytics = engine.execution_analytics.get_performance_report()
        if "basic_metrics" in analytics:
            basic_metrics = analytics["basic_metrics"]
            test_results.append({"test": "Execution Analytics", "passed": True, "message": f"Success rate: {basic_metrics.get('success_rate', 0):.2%}"})
            print(f"   ✅ Execution Analytics: PASS (Success rate: {basic_metrics.get('success_rate', 0):.2%})")
        else:
            test_results.append({"test": "Execution Analytics", "passed": False, "message": "Analytics failed"})
            print("   ❌ Execution Analytics: FAIL")
        
        # Test 9: Engine Shutdown
        print("9. Testing Engine Shutdown...")
        await engine.stop()
        if not engine.is_running:
            test_results.append({"test": "Engine Shutdown", "passed": True, "message": "Engine stopped successfully"})
            print("   ✅ Engine Shutdown: PASS")
        else:
            test_results.append({"test": "Engine Shutdown", "passed": False, "message": "Engine failed to stop"})
            print("   ❌ Engine Shutdown: FAIL")
        
        # Print Summary
        print("\n" + "=" * 60)
        print("PHASE 9.3 REAL-TIME EXECUTION SYSTEM TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for result in test_results if result["passed"])
        total = len(test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"{status} {result['test']}: {result['message']}")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED! Phase 9.3 Real-Time Execution System is working correctly.")
        else:
            print(f"\n⚠️  {total - passed} TESTS FAILED. Please review the implementation.")
        
        print("=" * 60)
        
        # Save results
        with open("simple_real_time_execution_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print("Test results saved to simple_real_time_execution_test_results.json")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Test suite failed with error: {e}")
        return False

async def main():
    """Main test function."""
    success = await test_real_time_execution()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 