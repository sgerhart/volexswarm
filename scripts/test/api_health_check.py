#!/usr/bin/env python3
"""
VolexSwarm API Health Check
Quick verification that all agent APIs are responding correctly.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Agent API endpoints
AGENT_ENDPOINTS = {
    "realtime_data": "http://localhost:8026",
    "news_sentiment": "http://localhost:8024",
    "strategy_discovery": "http://localhost:8025",
    "execution": "http://localhost:8002",
    "monitor": "http://localhost:8008",
    "backtest": "http://localhost:8006",
    "risk": "http://localhost:8009",
    "compliance": "http://localhost:8010"
}

async def check_agent_health():
    """Check health of all agents."""
    print("🔍 Checking VolexSwarm Agent Health...")
    print("=" * 50)
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for agent_name, endpoint in AGENT_ENDPOINTS.items():
            try:
                async with session.get(f"{endpoint}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        results[agent_name] = {
                            "status": "healthy",
                            "response_time": response.headers.get("X-Response-Time", "N/A"),
                            "data": data
                        }
                        print(f"✅ {agent_name:20} - Healthy ({endpoint})")
                    else:
                        results[agent_name] = {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
                        print(f"❌ {agent_name:20} - Unhealthy: HTTP {response.status}")
            except asyncio.TimeoutError:
                results[agent_name] = {
                    "status": "timeout",
                    "error": "Request timeout"
                }
                print(f"⏰ {agent_name:20} - Timeout")
            except Exception as e:
                results[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"❌ {agent_name:20} - Error: {e}")
    
    print("=" * 50)
    
    # Summary
    healthy_count = sum(1 for r in results.values() if r["status"] == "healthy")
    total_count = len(results)
    
    print(f"📊 Health Summary: {healthy_count}/{total_count} agents healthy")
    
    if healthy_count == total_count:
        print("✅ All agents are healthy and ready for testing!")
        return True
    else:
        print("⚠️ Some agents are not responding correctly.")
        return False

async def test_key_endpoints():
    """Test key endpoints for real-world trading."""
    print("\n🧪 Testing Key Trading Endpoints...")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test execution agent portfolio status
        try:
            async with session.get("http://localhost:8002/portfolio/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Execution Agent - Portfolio Status: OK")
                    if "balance" in data:
                        balance = data.get("balance", {}).get("USDT", 0)
                        print(f"   💰 USDT Balance: {balance}")
                else:
                    print(f"❌ Execution Agent - Portfolio Status: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Execution Agent - Portfolio Status: {e}")
        
        # Test real-time data agent connections
        try:
            async with session.get("http://localhost:8026/connections") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Real-time Data Agent - Connections: OK")
                    connections = data.get("connections", [])
                    print(f"   📡 Active Connections: {len(connections)}")
                else:
                    print(f"❌ Real-time Data Agent - Connections: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Real-time Data Agent - Connections: {e}")
        
        # Test strategy discovery agent
        try:
            async with session.get("http://localhost:8025/health") as response:
                if response.status == 200:
                    print("✅ Strategy Discovery Agent: Ready")
                else:
                    print(f"❌ Strategy Discovery Agent: HTTP {response.status}")
        except Exception as e:
            print(f"❌ Strategy Discovery Agent: {e}")
        
        # Test news sentiment agent
        try:
            async with session.get("http://localhost:8024/health") as response:
                if response.status == 200:
                    print("✅ News Sentiment Agent: Ready")
                else:
                    print(f"❌ News Sentiment Agent: HTTP {response.status}")
        except Exception as e:
            print(f"❌ News Sentiment Agent: {e}")

async def main():
    """Main health check function."""
    print(f"🚀 VolexSwarm API Health Check - {datetime.now()}")
    
    # Check basic health
    all_healthy = await check_agent_health()
    
    # Test key endpoints
    await test_key_endpoints()
    
    print("\n" + "=" * 50)
    if all_healthy:
        print("🎯 System is ready for real-world trading tests!")
        return 0
    else:
        print("⚠️ Please resolve agent issues before proceeding with live trading.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
