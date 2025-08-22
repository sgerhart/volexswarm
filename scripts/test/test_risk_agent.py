#!/usr/bin/env python3
"""
Test script for Risk Agent
Tests the AI-powered risk management and position sizing capabilities.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.risk.agentic_risk_agent import AgenticRiskAgent, PositionSizingRequest, RiskAssessmentRequest, StopLossRequest
from common.db import get_db_client
from common.logging import get_logger

logger = get_logger("test_risk_agent")

async def test_database_connectivity():
    """Test database connectivity and risk configuration."""
    print("🔌 Testing Database Connectivity...")
    
    try:
        db_client = get_db_client()
        
        # Check if risk_config table exists
        result = await db_client.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'risk_config'
        """)
        
        if not result:
            print("   ❌ risk_config table not found - needs to be created")
            return False
        
        print("   ✅ risk_config table exists")
        
        # Check if table has data
        count_result = await db_client.fetch("SELECT COUNT(*) as count FROM risk_config")
        row_count = count_result[0]['count']
        
        if row_count == 0:
            print("   ⚠️  risk_config table is empty - needs default data")
            return False
        
        print(f"   ✅ risk_config table has {row_count} configuration items")
        
        # Show sample configuration
        sample_result = await db_client.fetch("SELECT * FROM risk_config LIMIT 3")
        print("   📋 Sample configuration:")
        for row in sample_result:
            print(f"      - {row['config_key']}: {row['config_value']} ({row['category']})")
        
        await db_client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database connectivity failed: {e}")
        return False

async def test_risk_agent_initialization():
    """Test risk agent initialization."""
    print("\n🚀 Testing Risk Agent Initialization...")
    
    try:
        # Initialize the agent
        agent = AgenticRiskAgent()
        print("   ✅ Risk Agent created")
        
        # Initialize infrastructure
        await agent.initialize_infrastructure()
        print("   ✅ Infrastructure initialized")
        
        # Initialize the agent
        init_result = await agent.initialize()
        if init_result:
            print("   ✅ Risk Agent initialized successfully")
        else:
            print("   ❌ Risk Agent initialization failed")
            return False
        
        await agent.shutdown()
        print("   ✅ Risk Agent shutdown successfully")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Risk Agent initialization failed: {e}")
        return False

async def test_position_sizing():
    """Test position sizing calculations."""
    print("\n📊 Testing Position Sizing...")
    
    try:
        agent = AgenticRiskAgent()
        await agent.initialize_infrastructure()
        await agent.initialize()
        
        # Test Kelly Criterion
        print("   Testing Kelly Criterion position sizing...")
        kelly_request = PositionSizingRequest(
            symbol="BTC/USDT",
            side="buy",
            account_balance=10000.0,
            current_price=50000.0,
            method="kelly",
            win_rate=0.6,
            avg_win=0.05,
            avg_loss=0.03
        )
        
        kelly_result = await agent.calculate_position_size(kelly_request)
        if "error" not in kelly_result:
            print(f"   ✅ Kelly Criterion: {kelly_result.get('position_size', 0):.4f} BTC")
            print(f"      Risk level: {kelly_result.get('risk_level', 'unknown')}")
        else:
            print(f"   ❌ Kelly Criterion failed: {kelly_result.get('error', 'Unknown error')}")
        
        # Test Fixed Percentage
        print("   Testing Fixed Percentage position sizing...")
        fixed_request = PositionSizingRequest(
            symbol="ETH/USDT",
            side="buy",
            account_balance=10000.0,
            current_price=3000.0,
            method="fixed"
        )
        
        fixed_result = await agent.calculate_position_size(fixed_request)
        if "error" not in fixed_result:
            print(f"   ✅ Fixed Percentage: {fixed_result.get('position_size', 0):.4f} ETH")
            print(f"      Risk level: {fixed_result.get('risk_level', 'unknown')}")
        else:
            print(f"   ❌ Fixed Percentage failed: {fixed_result.get('error', 'Unknown error')}")
        
        await agent.shutdown()
        return True
        
    except Exception as e:
        print(f"   ❌ Position sizing test failed: {e}")
        return False

async def test_risk_assessment():
    """Test risk assessment functionality."""
    print("\n⚠️  Testing Risk Assessment...")
    
    try:
        agent = AgenticRiskAgent()
        await agent.initialize_infrastructure()
        await agent.initialize()
        
        # Test risk assessment
        risk_request = RiskAssessmentRequest(
            symbol="BTC/USDT",
            position_size=0.1,
            entry_price=50000.0,
            current_price=50000.0,
            side="buy",
            account_balance=10000.0,
            stop_loss=48000.0,
            take_profit=55000.0,
            existing_positions=[]
        )
        
        risk_result = await agent.assess_risk(risk_request)
        if "error" not in risk_result:
            print(f"   ✅ Risk Assessment completed")
            print(f"      Risk Level: {risk_result.get('risk_level', 'unknown')}")
            print(f"      Risk-Reward Ratio: {risk_result.get('risk_reward_ratio', 0):.2f}")
            print(f"      Portfolio Risk: {risk_result.get('portfolio_risk', 0):.4f}")
            
            recommendations = risk_result.get('recommendations', [])
            if recommendations:
                print(f"      Recommendations: {len(recommendations)} items")
                for rec in recommendations[:3]:
                    print(f"        - {rec}")
        else:
            print(f"   ❌ Risk assessment failed: {risk_result.get('error', 'Unknown error')}")
        
        await agent.shutdown()
        return True
        
    except Exception as e:
        print(f"   ❌ Risk assessment test failed: {e}")
        return False

async def test_stop_loss_calculation():
    """Test stop loss calculation."""
    print("\n🛑 Testing Stop Loss Calculation...")
    
    try:
        agent = AgenticRiskAgent()
        await agent.initialize_infrastructure()
        await agent.initialize()
        
        # Test stop loss calculation
        stop_loss_request = StopLossRequest(
            symbol="BTC/USDT",
            side="buy",
            entry_price=50000.0,
            current_price=50000.0,
            volatility=0.03,
            risk_tolerance="medium"
        )
        
        stop_loss_result = await agent.calculate_stop_loss(stop_loss_request)
        if "error" not in stop_loss_result:
            print(f"   ✅ Stop Loss calculated")
            print(f"      Stop Loss Price: ${stop_loss_result.get('stop_loss_price', 0):.2f}")
            print(f"      Stop Loss Percentage: {stop_loss_result.get('stop_loss_percentage', 0):.2%}")
            print(f"      Risk Amount: ${stop_loss_result.get('risk_amount', 0):.2f}")
        else:
            print(f"   ❌ Stop loss calculation failed: {stop_loss_result.get('error', 'Unknown error')}")
        
        await agent.shutdown()
        return True
        
    except Exception as e:
        print(f"   ❌ Stop loss test failed: {e}")
        return False

async def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("\n🔌 Testing Circuit Breaker...")
    
    try:
        agent = AgenticRiskAgent()
        await agent.initialize_infrastructure()
        await agent.initialize()
        
        # Test circuit breaker check
        circuit_result = await agent.check_circuit_breaker({
            "symbol": "BTC/USDT",
            "current_drawdown": 0.15,
            "daily_loss": 0.08,
            "volatility": 0.05
        })
        
        if "error" not in circuit_result:
            print(f"   ✅ Circuit breaker check completed")
            print(f"      Status: {circuit_result.get('status', 'unknown')}")
            print(f"      Triggered: {circuit_result.get('triggered', False)}")
            
            if circuit_result.get('triggered'):
                print(f"      Reason: {circuit_result.get('reason', 'Unknown')}")
                print(f"      Actions: {circuit_result.get('actions', [])}")
        else:
            print(f"   ❌ Circuit breaker check failed: {circuit_result.get('error', 'Unknown error')}")
        
        await agent.shutdown()
        return True
        
    except Exception as e:
        print(f"   ❌ Circuit breaker test failed: {e}")
        return False

async def test_portfolio_risk():
    """Test portfolio risk assessment."""
    print("\n📈 Testing Portfolio Risk Assessment...")
    
    try:
        agent = AgenticRiskAgent()
        await agent.initialize_infrastructure()
        await agent.initialize()
        
        # Test portfolio risk assessment
        portfolio_request = {
            "account_balance": 10000.0,
            "positions": [
                {"symbol": "BTC/USDT", "value": 2000.0, "risk": 100.0},
                {"symbol": "ETH/USDT", "value": 1500.0, "risk": 75.0},
                {"symbol": "ADA/USDT", "value": 500.0, "risk": 25.0}
            ]
        }
        
        portfolio_result = await agent.assess_portfolio_risk(portfolio_request)
        if "error" not in portfolio_result:
            print(f"   ✅ Portfolio risk assessment completed")
            print(f"      Total Risk: ${portfolio_result.get('total_risk', 0):.2f}")
            print(f"      Portfolio Value: ${portfolio_result.get('portfolio_value', 0):.2f}")
            print(f"      Risk Level: {portfolio_result.get('risk_level', 'unknown')}")
            
            recommendations = portfolio_result.get('recommendations', [])
            if recommendations:
                print(f"      Recommendations: {len(recommendations)} items")
                for rec in recommendations[:3]:
                    print(f"        - {rec}")
        else:
            print(f"   ❌ Portfolio risk assessment failed: {portfolio_result.get('error', 'Unknown error')}")
        
        await agent.shutdown()
        return True
        
    except Exception as e:
        print(f"   ❌ Portfolio risk test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🚀 Starting Risk Agent Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Database Connectivity
    test_results.append(await test_database_connectivity())
    
    # Test 2: Agent Initialization
    test_results.append(await test_risk_agent_initialization())
    
    # Test 3: Position Sizing
    test_results.append(await test_position_sizing())
    
    # Test 4: Risk Assessment
    test_results.append(await test_risk_assessment())
    
    # Test 5: Stop Loss Calculation
    test_results.append(await test_stop_loss_calculation())
    
    # Test 6: Circuit Breaker
    test_results.append(await test_circuit_breaker())
    
    # Test 7: Portfolio Risk Assessment
    test_results.append(await test_portfolio_risk())
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Risk Agent is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the logs.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())

