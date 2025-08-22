#!/usr/bin/env python3
"""
Real-Time Signal Generation Demo

This script demonstrates the real-time signal generation capabilities
of the enhanced signal agent system.
"""

import asyncio
import random
import time
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.signal.real_time_signal_generator import RealTimeSignalGenerator, RealTimeSignal, SignalType, SignalPriority
from agents.signal.signal_validation_engine import SignalValidator, SignalRoutingEngine
from agents.signal.signal_acknowledgment_system import SignalAcknowledgmentSystem
from common.logging import get_logger

logger = get_logger("real_time_signal_demo")

class RealTimeSignalDemo:
    """Demo class for real-time signal generation."""
    
    def __init__(self):
        self.signal_generator = RealTimeSignalGenerator()
        self.signal_validator = SignalValidator()
        self.signal_routing = SignalRoutingEngine()
        self.acknowledgment_system = SignalAcknowledgmentSystem()
        
        # Demo statistics
        self.demo_stats = {
            "signals_generated": 0,
            "signals_validated": 0,
            "signals_routed": 0,
            "signals_acknowledged": 0,
            "start_time": None
        }
    
    async def setup(self):
        """Setup demo environment."""
        logger.info("🚀 Setting up Real-Time Signal Generation Demo")
        
        # Start components
        await self.signal_generator.start_processing()
        await self.acknowledgment_system.start()
        
        # Setup handlers
        self.signal_generator.add_signal_handler(self._demo_signal_handler)
        self.acknowledgment_system.add_acknowledgment_handler(self._demo_acknowledgment_handler)
        
        # Register routing handlers
        self.signal_routing.register_handler("execution", self._demo_execution_handler)
        self.signal_routing.register_handler("risk", self._demo_risk_handler)
        self.signal_routing.register_handler("monitor", self._demo_monitor_handler)
        
        self.demo_stats["start_time"] = datetime.utcnow()
        logger.info("✅ Demo environment ready")
    
    async def cleanup(self):
        """Cleanup demo environment."""
        logger.info("🧹 Cleaning up demo environment")
        await self.signal_generator.stop_processing()
        await self.acknowledgment_system.stop()
    
    def _demo_signal_handler(self, signal: RealTimeSignal):
        """Demo signal handler."""
        self.demo_stats["signals_generated"] += 1
        logger.info(f"📊 Signal Generated: {signal.signal_type.value} {signal.symbol} "
                   f"(Confidence: {signal.confidence:.2f}, Priority: {signal.priority.name})")
    
    def _demo_acknowledgment_handler(self, acknowledgment):
        """Demo acknowledgment handler."""
        self.demo_stats["signals_acknowledged"] += 1
        logger.info(f"✅ Signal Acknowledged: {acknowledgment.signal_id} "
                   f"(Status: {acknowledgment.status.value})")
    
    async def _demo_execution_handler(self, signal: RealTimeSignal):
        """Demo execution handler."""
        self.demo_stats["signals_routed"] += 1
        logger.info(f"⚡ Execution Handler: {signal.signal_id} - {signal.signal_type.value}")
        return {"success": True, "message": "Demo execution completed"}
    
    async def _demo_risk_handler(self, signal: RealTimeSignal):
        """Demo risk handler."""
        logger.info(f"🛡️ Risk Handler: {signal.signal_id} - Risk assessment completed")
        return {"success": True, "risk_approved": True, "risk_score": 0.3}
    
    async def _demo_monitor_handler(self, signal: RealTimeSignal):
        """Demo monitor handler."""
        logger.info(f"👁️ Monitor Handler: {signal.signal_id} - Signal monitored")
        return {"success": True, "monitored": True}
    
    async def run_market_data_simulation(self, duration: int = 60):
        """Run market data simulation."""
        logger.info(f"📈 Starting market data simulation for {duration} seconds")
        
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "SOLUSDT", "DOTUSDT"]
        base_prices = {
            "BTCUSDT": 45000,
            "ETHUSDT": 3000,
            "ADAUSDT": 0.5,
            "SOLUSDT": 100,
            "DOTUSDT": 7
        }
        
        start_time = time.time()
        data_points = 0
        
        while time.time() - start_time < duration:
            for symbol in symbols:
                # Simulate realistic price movements
                base_price = base_prices[symbol]
                
                # Add some volatility
                volatility = 0.02  # 2% volatility
                trend = random.uniform(-0.01, 0.01)  # Slight trend
                noise = random.uniform(-volatility, volatility)
                
                price_change = trend + noise
                price = base_price * (1 + price_change)
                volume = random.uniform(100, 1000)
                timestamp = datetime.utcnow()
                
                # Process market data
                await self.signal_generator.process_market_data(symbol, price, volume, timestamp)
                
                # Update base price
                base_prices[symbol] = price
                data_points += 1
            
            # Small delay between updates
            await asyncio.sleep(0.5)
        
        logger.info(f"📊 Market data simulation completed: {data_points} data points processed")
    
    async def run_validation_demo(self):
        """Run signal validation demo."""
        logger.info("🔍 Running signal validation demo")
        
        # Create test signals with different characteristics
        test_signals = [
            RealTimeSignal(
                symbol="BTCUSDT",
                signal_type=SignalType.STRONG_BUY,
                priority=SignalPriority.CRITICAL,
                confidence=0.95,
                timestamp=datetime.utcnow(),
                price=45000.0,
                volume=1000.0,
                indicators={"rsi": 15.0, "macd": {"macd": 1.0, "signal": 0.5}},
                reasoning="Extreme oversold conditions with strong MACD"
            ),
            RealTimeSignal(
                symbol="ETHUSDT",
                signal_type=SignalType.SELL,
                priority=SignalPriority.HIGH,
                confidence=0.75,
                timestamp=datetime.utcnow(),
                price=3000.0,
                volume=500.0,
                indicators={"rsi": 85.0, "macd": {"macd": -0.5, "signal": 0.2}},
                reasoning="Overbought conditions with bearish MACD"
            ),
            RealTimeSignal(
                symbol="ADAUSDT",
                signal_type=SignalType.WATCH,
                priority=SignalPriority.LOW,
                confidence=0.45,
                timestamp=datetime.utcnow(),
                price=0.5,
                volume=200.0,
                indicators={"rsi": 55.0, "macd": {"macd": 0.0, "signal": 0.0}},
                reasoning="Neutral conditions, monitoring for opportunities"
            )
        ]
        
        for signal in test_signals:
            # Validate signal
            validation_result = await self.signal_validator.validate_signal(signal)
            self.demo_stats["signals_validated"] += 1
            
            logger.info(f"🔍 Signal Validation: {signal.symbol} - {signal.signal_type.value}")
            logger.info(f"   Confidence: {signal.confidence:.2f}")
            logger.info(f"   Validation Result: {validation_result['validation_result'].value}")
            logger.info(f"   Validation Score: {validation_result['validation_score']:.2f}")
            
            # Route signal if approved
            if validation_result["validation_result"].value == "approved":
                final_signal = validation_result["final_signal"]
                routing_result = await self.signal_routing.route_signal(final_signal)
                logger.info(f"   Routing: {routing_result['success']} "
                           f"(Handlers: {routing_result['handlers_called']})")
            
            logger.info("")
    
    async def run_performance_demo(self):
        """Run performance metrics demo."""
        logger.info("📊 Running performance metrics demo")
        
        # Get various statistics
        signal_stats = self.signal_generator.get_signal_stats()
        validation_stats = self.signal_validator.get_validation_stats()
        routing_stats = self.signal_routing.get_routing_stats()
        acknowledgment_stats = self.acknowledgment_system.get_acknowledgment_stats()
        
        logger.info("📈 Performance Metrics:")
        logger.info(f"   Signal Generation: {signal_stats}")
        logger.info(f"   Validation: {validation_stats}")
        logger.info(f"   Routing: {routing_stats}")
        logger.info(f"   Acknowledgment: {acknowledgment_stats}")
        
        # Calculate demo statistics
        if self.demo_stats["start_time"]:
            duration = (datetime.utcnow() - self.demo_stats["start_time"]).total_seconds()
            signals_per_second = self.demo_stats["signals_generated"] / max(1, duration)
            
            logger.info(f"🚀 Demo Performance:")
            logger.info(f"   Duration: {duration:.1f} seconds")
            logger.info(f"   Signals Generated: {self.demo_stats['signals_generated']}")
            logger.info(f"   Signals Validated: {self.demo_stats['signals_validated']}")
            logger.info(f"   Signals Routed: {self.demo_stats['signals_routed']}")
            logger.info(f"   Signals Acknowledged: {self.demo_stats['signals_acknowledged']}")
            logger.info(f"   Signals/Second: {signals_per_second:.2f}")
    
    async def run_complete_demo(self):
        """Run complete demo."""
        logger.info("🎬 Starting Real-Time Signal Generation Demo")
        logger.info("=" * 60)
        
        try:
            # Setup
            await self.setup()
            
            # Run market data simulation
            logger.info("Phase 1: Market Data Simulation")
            await self.run_market_data_simulation(duration=30)
            
            # Run validation demo
            logger.info("\nPhase 2: Signal Validation Demo")
            await self.run_validation_demo()
            
            # Run performance demo
            logger.info("\nPhase 3: Performance Metrics Demo")
            await self.run_performance_demo()
            
            # Final summary
            logger.info("\n" + "=" * 60)
            logger.info("🎉 Demo Completed Successfully!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
        finally:
            await self.cleanup()

async def main():
    """Main demo function."""
    demo = RealTimeSignalDemo()
    await demo.run_complete_demo()

if __name__ == "__main__":
    asyncio.run(main()) 