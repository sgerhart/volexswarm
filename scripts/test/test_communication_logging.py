#!/usr/bin/env python3
"""
Test script for Agent Communication Logging System
Demonstrates how all agent communications are logged and tracked.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.communication_logger import communication_logger
from common.logging import get_logger

logger = get_logger("test_communication_logging")

async def test_communication_logging():
    """Test the comprehensive agent communication logging system."""
    
    print("🔍 Testing Agent Communication Logging System")
    print("=" * 60)
    
    try:
        # Initialize the communication logger
        await communication_logger.initialize()
        print("✅ Communication logger initialized")
        
        # Test 1: Start a conversation
        conversation_id = str(uuid.uuid4())
        participants = ["signal_agent", "risk_agent", "execution_agent"]
        
        success = await communication_logger.start_conversation(
            conversation_id=conversation_id,
            topic="signal_validation_and_execution",
            participants=participants,
            initiator="signal_agent",
            metadata={"symbol": "BTCUSDT", "signal_type": "BUY"}
        )
        
        if success:
            print(f"✅ Started conversation: {conversation_id}")
        else:
            print("❌ Failed to start conversation")
            return
        
        # Test 2: Log WebSocket messages
        print("\n📡 Testing WebSocket Message Logging:")
        
        # Signal agent sends signal to risk agent
        await communication_logger.log_websocket_message(
            from_agent="signal_agent",
            to_agent="risk_agent",
            message_type="SIGNAL_UPDATE",
            direction="outbound",
            message_data={
                "symbol": "BTCUSDT",
                "signal_type": "BUY",
                "confidence": 0.85,
                "price": 45000.0,
                "timestamp": datetime.now().isoformat()
            },
            conversation_id=conversation_id,
            response_time_ms=150,
            status="delivered"
        )
        print("  ✅ Logged: Signal Agent → Risk Agent (SIGNAL_UPDATE)")
        
        # Risk agent responds with risk assessment
        await communication_logger.log_websocket_message(
            from_agent="risk_agent",
            to_agent="signal_agent",
            message_type="RISK_ASSESSMENT",
            direction="outbound",
            message_data={
                "symbol": "BTCUSDT",
                "risk_level": "medium",
                "position_size": 1000.0,
                "stop_loss": 44100.0,
                "approved": True,
                "timestamp": datetime.now().isoformat()
            },
            conversation_id=conversation_id,
            response_time_ms=200,
            status="delivered"
        )
        print("  ✅ Logged: Risk Agent → Signal Agent (RISK_ASSESSMENT)")
        
        # Test 3: Log API calls
        print("\n🌐 Testing API Call Logging:")
        
        # Signal agent calls execution agent API
        await communication_logger.log_api_call(
            from_agent="signal_agent",
            to_agent="execution_agent",
            endpoint="/execute_trade",
            method="POST",
            request_data={
                "symbol": "BTCUSDT",
                "side": "buy",
                "amount": 1000.0,
                "order_type": "market"
            },
            response_data={
                "order_id": "order_12345",
                "status": "filled",
                "filled_price": 45000.0,
                "filled_amount": 1000.0
            },
            response_code=200,
            response_time_ms=500,
            conversation_id=conversation_id,
            status="success"
        )
        print("  ✅ Logged: Signal Agent → Execution Agent (POST /execute_trade)")
        
        # Test 4: Log AI interactions
        print("\n🤖 Testing AI Interaction Logging:")
        
        # Signal agent uses AI for signal generation
        await communication_logger.log_ai_interaction(
            agent_name="signal_agent",
            interaction_type="signal_generation",
            ai_model="gpt-4o-mini",
            prompt_tokens=150,
            completion_tokens=75,
            total_tokens=225,
            response_time_ms=1200,
            confidence_score=0.85,
            reasoning="Based on RSI oversold conditions, MACD bullish crossover, and volume spike, this appears to be a strong buy opportunity.",
            decision="buy",
            conversation_id=conversation_id,
            metadata={"symbol": "BTCUSDT", "timeframe": "1h"}
        )
        print("  ✅ Logged: Signal Agent AI Interaction (signal_generation)")
        
        # Risk agent uses AI for risk assessment
        await communication_logger.log_ai_interaction(
            agent_name="risk_agent",
            interaction_type="risk_assessment",
            ai_model="gpt-4o-mini",
            prompt_tokens=200,
            completion_tokens=100,
            total_tokens=300,
            response_time_ms=800,
            confidence_score=0.92,
            reasoning="Current portfolio risk is acceptable, position size is within limits, and market volatility is manageable.",
            decision="approve",
            conversation_id=conversation_id,
            metadata={"symbol": "BTCUSDT", "position_size": 1000.0}
        )
        print("  ✅ Logged: Risk Agent AI Interaction (risk_assessment)")
        
        # Test 5: Log performance metrics
        print("\n📊 Testing Performance Metrics Logging:")
        
        await communication_logger.log_performance_metric(
            agent_name="signal_agent",
            metric_name="signal_generation_time_ms",
            metric_value=1200.0,
            metric_unit="ms",
            context={"symbol": "BTCUSDT", "signal_type": "BUY"}
        )
        print("  ✅ Logged: Signal Agent Performance Metric")
        
        await communication_logger.log_performance_metric(
            agent_name="risk_agent",
            metric_name="risk_assessment_time_ms",
            metric_value=800.0,
            metric_unit="ms",
            context={"symbol": "BTCUSDT", "risk_level": "medium"}
        )
        print("  ✅ Logged: Risk Agent Performance Metric")
        
        # Test 6: End the conversation
        print("\n🏁 Ending Conversation:")
        
        success = await communication_logger.end_conversation(
            conversation_id=conversation_id,
            outcome="success",
            summary="Successfully generated, validated, and executed BTCUSDT buy signal",
            metadata={"final_price": 45000.0, "total_volume": 1000.0}
        )
        
        if success:
            print("  ✅ Ended conversation successfully")
        else:
            print("  ❌ Failed to end conversation")
        
        # Test 7: Generate conversation summary
        print("\n📈 Generating Conversation Summary:")
        
        period_start = datetime.now() - timedelta(hours=1)
        period_end = datetime.now()
        
        summary = await communication_logger.get_conversation_summary(
            period_start=period_start,
            period_end=period_end,
            period_type="hourly"
        )
        
        if summary:
            print("  ✅ Generated conversation summary:")
            print(f"     Total conversations: {summary.get('total_conversations', 0)}")
            print(f"     Successful: {summary.get('successful_conversations', 0)}")
            print(f"     Failed: {summary.get('failed_conversations', 0)}")
            print(f"     Avg duration: {summary.get('avg_duration_seconds', 0):.1f}s")
            print(f"     Avg messages: {summary.get('avg_message_count', 0):.1f}")
        else:
            print("  ❌ Failed to generate conversation summary")
        
        print("\n🎉 Communication Logging Test Completed Successfully!")
        print("\n📋 What was logged:")
        print("  • 1 conversation (start to finish)")
        print("  • 2 WebSocket messages between agents")
        print("  • 1 API call between agents")
        print("  • 2 AI interactions with reasoning and decisions")
        print("  • 2 performance metrics")
        print("  • 1 conversation summary")
        
        print("\n🔍 You can now query the database to see all logged communications:")
        print("  • agent_communications - All communications")
        print("  • agent_websocket_messages - WebSocket messages")
        print("  • agent_api_calls - API calls")
        print("  • agent_ai_interactions - AI interactions")
        print("  • agent_conversations - Conversation tracking")
        print("  • agent_performance_metrics - Performance data")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_communication_logging())
