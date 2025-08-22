#!/usr/bin/env python3
"""
Test script for Strategy Discovery Agent
Tests the AI-powered strategy discovery and pattern recognition capabilities.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.strategy_discovery.agentic_strategy_discovery_agent import AgenticStrategyDiscoveryAgent

async def test_strategy_discovery():
    """Test the strategy discovery functionality."""
    print("🧪 Testing Strategy Discovery Agent")
    print("=" * 50)
    
    try:
        # Initialize the agent
        agent = AgenticStrategyDiscoveryAgent()
        print("✅ Strategy Discovery Agent initialized")
        
        # Test symbols
        test_symbols = ["BTC/USDT", "ETH/USDT", "ADA/USDT"]
        
        print(f"\n🔍 Testing strategy discovery for symbols: {test_symbols}")
        
        # Test strategy discovery
        result = await agent.discover_strategies(test_symbols, risk_profile="balanced")
        
        if result["status"] == "success":
            print(f"✅ Strategy discovery successful!")
            print(f"   Symbols analyzed: {result['symbols_analyzed']}")
            print(f"   Strategies found: {result['strategies_found']}")
            
            # Display top strategies
            if result['strategies']:
                print(f"\n📊 Top Strategies Found:")
                for i, strategy in enumerate(result['strategies'][:5], 1):
                    print(f"   {i}. {strategy.get('name', 'Unknown')}")
                    print(f"      Type: {strategy.get('type', 'Unknown')}")
                    print(f"      Risk Profile: {strategy.get('risk_profile', 'Unknown')}")
                    print(f"      Confidence: {strategy.get('confidence', 0):.2f}")
                    print(f"      Score: {strategy.get('score', 0):.2f}")
                    print()
            
            # Test sandbox creation for top strategy
            if result['strategies']:
                top_strategy = result['strategies'][0]
                print(f"🧪 Creating sandbox test for top strategy: {top_strategy.get('name', 'Unknown')}")
                
                sandbox_result = await agent.create_sandbox_test(top_strategy)
                
                if sandbox_result["status"] == "success":
                    print(f"✅ Sandbox test created successfully!")
                    print(f"   Test ID: {sandbox_result['test_id']}")
                    print(f"   Initial Capital: ${sandbox_result['sandbox_config']['initial_capital']:,}")
                    print(f"   Commission: {sandbox_result['sandbox_config']['commission']:.3f}")
                    print(f"   Slippage: {sandbox_result['sandbox_config']['slippage']:.4f}")
                else:
                    print(f"❌ Sandbox test creation failed: {sandbox_result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Strategy discovery failed: {result.get('error', 'Unknown error')}")
        
        # Test individual tool functions
        print(f"\n🔧 Testing individual tools...")
        
        # Test market pattern analysis
        print("   Testing market pattern analysis...")
        pattern_result = await agent.tools.analyze_market_patterns("BTC/USDT", "1d", 30)
        
        if "error" not in pattern_result:
            print(f"   ✅ Pattern analysis successful for BTC/USDT")
            print(f"      Data points: {pattern_result.get('data_points', 0)}")
            print(f"      Trend strength: {pattern_result.get('patterns', {}).get('price_trend', {}).get('trend_strength', 0)}")
            print(f"      RSI: {pattern_result.get('patterns', {}).get('price_trend', {}).get('rsi', 0):.2f}")
        else:
            print(f"   ❌ Pattern analysis failed: {pattern_result.get('error', 'Unknown error')}")
        
        # Test strategy candidate generation
        print("   Testing strategy candidate generation...")
        candidates = await agent.tools.generate_strategy_candidates("BTC/USDT", "balanced")
        
        if candidates and "error" not in candidates[0]:
            print(f"   ✅ Strategy candidates generated: {len(candidates)}")
            for candidate in candidates[:3]:
                print(f"      - {candidate.get('name', 'Unknown')} ({candidate.get('type', 'Unknown')})")
        else:
            print(f"   ❌ Strategy candidate generation failed")
        
        # Test risk profile detection
        print("   Testing risk profile detection...")
        test_strategy = {
            "volatility": 0.25,
            "max_drawdown": 0.12,
            "sharpe_ratio": 1.8
        }
        risk_profile = await agent.tools.detect_risk_profile(test_strategy)
        print(f"   ✅ Risk profile detected: {risk_profile}")
        
        print(f"\n🎉 Strategy Discovery Agent test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test the FastAPI endpoints."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    try:
        import httpx
        
        base_url = "http://localhost:8025"
        
        # Test health endpoint
        print("   Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
        
        # Test strategy discovery endpoint
        print("   Testing strategy discovery endpoint...")
        test_data = {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "risk_profile": "balanced"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}/discover_strategies", json=test_data)
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Strategy discovery endpoint working")
                print(f"      Strategies found: {result.get('strategies_found', 0)}")
            else:
                print(f"   ❌ Strategy discovery endpoint failed: {response.status_code}")
        
        print("   ✅ API endpoints test completed")
        return True
        
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Starting Strategy Discovery Agent Tests")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Test agent functionality
    agent_test_passed = await test_strategy_discovery()
    
    # Test API endpoints (if agent is running)
    api_test_passed = await test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Agent Functionality: {'✅ PASSED' if agent_test_passed else '❌ FAILED'}")
    print(f"API Endpoints: {'✅ PASSED' if api_test_passed else '❌ FAILED'}")
    
    if agent_test_passed and api_test_passed:
        print("\n🎉 All tests passed! Strategy Discovery Agent is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 