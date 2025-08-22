#!/usr/bin/env python3
"""
Test script for Real-Time Signal Generation System

This script tests the enhanced signal agent's real-time capabilities including:
- Signal generation from market data
- Signal validation
- Signal acknowledgment
- Signal routing
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
import random
import requests
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.signal.real_time_signal_generator import RealTimeSignalGenerator, RealTimeSignal, SignalType, SignalPriority
from agents.signal.signal_validation_engine import SignalValidator, SignalRoutingEngine
from agents.signal.signal_acknowledgment_system import SignalAcknowledgmentSystem
from common.logging import get_logger

logger = get_logger("test_real_time_signals")

class RealTimeSignalTester:
    """Test class for real-time signal generation."""
    
    def __init__(self):
        self.signal_generator = RealTimeSignalGenerator()
        self.signal_validator = SignalValidator()
        self.signal_routing = SignalRoutingEngine()
        self.acknowledgment_system = SignalAcknowledgmentSystem()
        
        # Test results
        self.test_results = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
    
    async def setup(self):
        """Setup test environment."""
        logger.info("Setting up real-time signal generation test environment")
        
        # Start components
        await self.signal_generator.start_processing()
        await self.acknowledgment_system.start()
        
        # Setup signal handlers
        self.signal_generator.add_signal_handler(self._test_signal_handler)
        self.acknowledgment_system.add_acknowledgment_handler(self._test_acknowledgment_handler)
        
        # Register routing handlers
        self.signal_routing.register_handler("execution", self._test_execution_handler)
        self.signal_routing.register_handler("risk", self._test_risk_handler)
        self.signal_routing.register_handler("monitor", self._test_monitor_handler)
        
        logger.info("Test environment setup complete")
    
    async def cleanup(self):
        """Cleanup test environment."""
        logger.info("Cleaning up test environment")
        
        await self.signal_generator.stop_processing()
        await self.acknowledgment_system.stop()
        
        logger.info("Test environment cleanup complete")
    
    def _test_signal_handler(self, signal: RealTimeSignal):
        """Test signal handler."""
        logger.info(f"Test signal handler received: {signal.signal_id} - {signal.signal_type.value}")
    
    def _test_acknowledgment_handler(self, acknowledgment):
        """Test acknowledgment handler."""
        logger.info(f"Test acknowledgment handler received: {acknowledgment.signal_id}")
    
    async def _test_execution_handler(self, signal: RealTimeSignal):
        """Test execution handler."""
        logger.info(f"Test execution handler received: {signal.signal_id}")
        return {"success": True, "message": "Test execution completed"}
    
    async def _test_risk_handler(self, signal: RealTimeSignal):
        """Test risk handler."""
        logger.info(f"Test risk handler received: {signal.signal_id}")
        return {"success": True, "risk_approved": True, "risk_score": 0.3}
    
    async def _test_monitor_handler(self, signal: RealTimeSignal):
        """Test monitor handler."""
        logger.info(f"Test monitor handler received: {signal.signal_id}")
        return {"success": True, "monitored": True}
    
    async def test_signal_generation(self):
        """Test real-time signal generation."""
        logger.info("Testing real-time signal generation")
        
        try:
            # Generate test market data
            symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
            base_prices = {"BTCUSDT": 45000, "ETHUSDT": 3000, "ADAUSDT": 0.5}
            
            for i in range(50):  # Generate 50 data points
                for symbol in symbols:
                    # Simulate price movement
                    base_price = base_prices[symbol]
                    price_change = random.uniform(-0.02, 0.02)  # ±2% change
                    price = base_price * (1 + price_change)
                    volume = random.uniform(100, 1000)
                    timestamp = datetime.utcnow() + timedelta(seconds=i)
                    
                    # Process market data
                    await self.signal_generator.process_market_data(symbol, price, volume, timestamp)
                    
                    # Update base price
                    base_prices[symbol] = price
                
                # Small delay between data points
                await asyncio.sleep(0.1)
            
            # Check if signals were generated
            recent_signals = self.signal_generator.get_recent_signals()
            
            if len(recent_signals) > 0:
                logger.info(f"✅ Signal generation test PASSED: Generated {len(recent_signals)} signals")
                self.test_results["tests_passed"] += 1
            else:
                logger.error("❌ Signal generation test FAILED: No signals generated")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append("No signals generated")
            
            self.test_results["tests_run"] += 1
            
        except Exception as e:
            logger.error(f"❌ Signal generation test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(str(e))
            self.test_results["tests_run"] += 1
    
    async def test_signal_validation(self):
        """Test signal validation."""
        logger.info("Testing signal validation")
        
        try:
            # Create test signals
            test_signals = [
                RealTimeSignal(
                    symbol="BTCUSDT",
                    signal_type=SignalType.BUY,
                    priority=SignalPriority.HIGH,
                    confidence=0.8,
                    timestamp=datetime.utcnow(),
                    price=45000.0,
                    volume=500.0,
                    indicators={"rsi": 25.0, "macd": {"macd": 0.5, "signal": 0.3}},
                    reasoning="RSI oversold, MACD bullish"
                ),
                RealTimeSignal(
                    symbol="ETHUSDT",
                    signal_type=SignalType.SELL,
                    priority=SignalPriority.MEDIUM,
                    confidence=0.6,
                    timestamp=datetime.utcnow(),
                    price=3000.0,
                    volume=300.0,
                    indicators={"rsi": 75.0, "macd": {"macd": -0.2, "signal": 0.1}},
                    reasoning="RSI overbought, MACD bearish"
                ),
                RealTimeSignal(
                    symbol="ADAUSDT",
                    signal_type=SignalType.WATCH,
                    priority=SignalPriority.LOW,
                    confidence=0.4,
                    timestamp=datetime.utcnow(),
                    price=0.5,
                    volume=100.0,
                    indicators={"rsi": 50.0, "macd": {"macd": 0.0, "signal": 0.0}},
                    reasoning="Neutral indicators"
                )
            ]
            
            validation_results = []
            for signal in test_signals:
                result = await self.signal_validator.validate_signal(signal)
                validation_results.append(result)
                logger.info(f"Signal {signal.signal_id} validation: {result['validation_result'].value} "
                           f"(score: {result['validation_score']:.2f})")
            
            # Check validation results
            approved_count = sum(1 for r in validation_results if r["validation_result"].value == "approved")
            rejected_count = sum(1 for r in validation_results if r["validation_result"].value == "rejected")
            
            if approved_count > 0 and rejected_count > 0:
                logger.info(f"✅ Signal validation test PASSED: {approved_count} approved, {rejected_count} rejected")
                self.test_results["tests_passed"] += 1
            else:
                logger.error("❌ Signal validation test FAILED: Unexpected validation results")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append("Unexpected validation results")
            
            self.test_results["tests_run"] += 1
            
        except Exception as e:
            logger.error(f"❌ Signal validation test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(str(e))
            self.test_results["tests_run"] += 1
    
    async def test_signal_routing(self):
        """Test signal routing."""
        logger.info("Testing signal routing")
        
        try:
            # Create test signals with different priorities
            test_signals = [
                RealTimeSignal(
                    symbol="BTCUSDT",
                    signal_type=SignalType.STRONG_BUY,
                    priority=SignalPriority.CRITICAL,
                    confidence=0.9,
                    timestamp=datetime.utcnow(),
                    price=45000.0,
                    volume=500.0,
                    indicators={"rsi": 20.0},
                    reasoning="Critical buy signal"
                ),
                RealTimeSignal(
                    symbol="ETHUSDT",
                    signal_type=SignalType.SELL,
                    priority=SignalPriority.HIGH,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    price=3000.0,
                    volume=300.0,
                    indicators={"rsi": 80.0},
                    reasoning="High priority sell signal"
                )
            ]
            
            routing_results = []
            for signal in test_signals:
                result = await self.signal_routing.route_signal(signal)
                routing_results.append(result)
                logger.info(f"Signal {signal.signal_id} routing: {result['success']} "
                           f"(handlers: {result['handlers_called']})")
            
            # Check routing results
            successful_routes = sum(1 for r in routing_results if r["success"])
            
            if successful_routes == len(test_signals):
                logger.info(f"✅ Signal routing test PASSED: {successful_routes}/{len(test_signals)} successful routes")
                self.test_results["tests_passed"] += 1
            else:
                logger.error("❌ Signal routing test FAILED: Not all signals routed successfully")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append("Routing failures")
            
            self.test_results["tests_run"] += 1
            
        except Exception as e:
            logger.error(f"❌ Signal routing test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(str(e))
            self.test_results["tests_run"] += 1
    
    async def test_signal_acknowledgment(self):
        """Test signal acknowledgment."""
        logger.info("Testing signal acknowledgment")
        
        try:
            # Create test signal
            test_signal = RealTimeSignal(
                symbol="BTCUSDT",
                signal_type=SignalType.BUY,
                priority=SignalPriority.HIGH,
                confidence=0.8,
                timestamp=datetime.utcnow(),
                price=45000.0,
                volume=500.0,
                indicators={"rsi": 25.0},
                reasoning="Test acknowledgment signal"
            )
            
            # Acknowledge signal
            acknowledgment = await self.acknowledgment_system.acknowledge_signal(test_signal, "test_processor")
            
            if acknowledgment and acknowledgment.signal_id == test_signal.signal_id:
                logger.info(f"✅ Signal acknowledgment test PASSED: Signal {test_signal.signal_id} acknowledged")
                self.test_results["tests_passed"] += 1
            else:
                logger.error("❌ Signal acknowledgment test FAILED: Signal not acknowledged properly")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append("Acknowledgment failure")
            
            self.test_results["tests_run"] += 1
            
        except Exception as e:
            logger.error(f"❌ Signal acknowledgment test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(str(e))
            self.test_results["tests_run"] += 1
    
    async def test_performance_metrics(self):
        """Test performance metrics collection."""
        logger.info("Testing performance metrics")
        
        try:
            # Get various statistics
            signal_stats = self.signal_generator.get_signal_stats()
            validation_stats = self.signal_validator.get_validation_stats()
            routing_stats = self.signal_routing.get_routing_stats()
            acknowledgment_stats = self.acknowledgment_system.get_acknowledgment_stats()
            
            # Check if metrics are available
            metrics_available = (
                signal_stats is not None and
                validation_stats is not None and
                routing_stats is not None and
                acknowledgment_stats is not None
            )
            
            if metrics_available:
                logger.info("✅ Performance metrics test PASSED: All metrics available")
                logger.info(f"   Signal stats: {signal_stats}")
                logger.info(f"   Validation stats: {validation_stats}")
                logger.info(f"   Routing stats: {routing_stats}")
                logger.info(f"   Acknowledgment stats: {acknowledgment_stats}")
                self.test_results["tests_passed"] += 1
            else:
                logger.error("❌ Performance metrics test FAILED: Missing metrics")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append("Missing performance metrics")
            
            self.test_results["tests_run"] += 1
            
        except Exception as e:
            logger.error(f"❌ Performance metrics test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(str(e))
            self.test_results["tests_run"] += 1
    
    async def test_api_endpoints(self):
        """Test API endpoints."""
        logger.info("Testing API endpoints")
        
        try:
            # Test health endpoint
            response = requests.get("http://localhost:8003/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Health endpoint test PASSED")
            else:
                logger.error(f"❌ Health endpoint test FAILED: {response.status_code}")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append(f"Health endpoint failed: {response.status_code}")
            
            # Test status endpoint
            response = requests.get("http://localhost:8003/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                logger.info("✅ Status endpoint test PASSED")
                logger.info(f"   Agent status: {status_data.get('status', 'unknown')}")
            else:
                logger.error(f"❌ Status endpoint test FAILED: {response.status_code}")
                self.test_results["tests_failed"] += 1
                self.test_results["errors"].append(f"Status endpoint failed: {response.status_code}")
            
            self.test_results["tests_run"] += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API endpoints test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(f"API request failed: {str(e)}")
            self.test_results["tests_run"] += 1
        except Exception as e:
            logger.error(f"❌ API endpoints test FAILED: {e}")
            self.test_results["tests_failed"] += 1
            self.test_results["errors"].append(str(e))
            self.test_results["tests_run"] += 1
    
    def print_test_results(self):
        """Print test results summary."""
        logger.info("=" * 60)
        logger.info("REAL-TIME SIGNAL GENERATION TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Tests Run: {self.test_results['tests_run']}")
        logger.info(f"Tests Passed: {self.test_results['tests_passed']}")
        logger.info(f"Tests Failed: {self.test_results['tests_failed']}")
        logger.info(f"Success Rate: {(self.test_results['tests_passed'] / max(1, self.test_results['tests_run'])) * 100:.1f}%")
        
        if self.test_results["errors"]:
            logger.info("\nErrors:")
            for error in self.test_results["errors"]:
                logger.error(f"  - {error}")
        
        logger.info("=" * 60)
        
        # Return success if all tests passed
        return self.test_results["tests_failed"] == 0

async def main():
    """Main test function."""
    logger.info("Starting Real-Time Signal Generation System Tests")
    
    tester = RealTimeSignalTester()
    
    try:
        # Setup
        await tester.setup()
        
        # Run tests
        await tester.test_signal_generation()
        await asyncio.sleep(1)  # Allow time for signal processing
        
        await tester.test_signal_validation()
        await tester.test_signal_routing()
        await tester.test_signal_acknowledgment()
        await tester.test_performance_metrics()
        await tester.test_api_endpoints()
        
        # Print results
        success = tester.print_test_results()
        
        if success:
            logger.info("🎉 All tests PASSED! Real-time signal generation system is working correctly.")
            return 0
        else:
            logger.error("❌ Some tests FAILED! Please check the errors above.")
            return 1
            
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        return 1
    finally:
        # Cleanup
        await tester.cleanup()

if __name__ == "__main__":
    # Run the tests
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 