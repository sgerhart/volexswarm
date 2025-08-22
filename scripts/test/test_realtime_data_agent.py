#!/usr/bin/env python3
"""
Test script for the Real-Time Data Hub Agent

This script tests the WebSocket connection, data streaming, and API endpoints
of the Real-Time Data Hub Agent.
"""

import asyncio
import json
import time
import requests
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8026"
TEST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]

async def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

async def test_connect_to_exchange():
    """Test connecting to Binance US WebSocket."""
    print("\n🔌 Testing WebSocket connection...")
    
    try:
        payload = {
            "exchange_name": "binanceus",
            "symbols": TEST_SYMBOLS
        }
        
        response = requests.post(f"{BASE_URL}/connect", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Connection successful: {data}")
            return True
        else:
            print(f"❌ Connection failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

async def test_subscribe_to_channels():
    """Test subscribing to different channels."""
    print("\n📡 Testing channel subscriptions...")
    
    channels = ["kline_1m", "trade", "ticker"]
    success_count = 0
    
    for symbol in TEST_SYMBOLS[:1]:  # Test with first symbol only
        for channel in channels:
            try:
                payload = {
                    "exchange_name": "binanceus",
                    "channel": channel,
                    "symbol": symbol
                }
                
                response = requests.post(f"{BASE_URL}/subscribe", json=payload)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Subscribed to {channel} for {symbol}: {data}")
                    success_count += 1
                else:
                    print(f"❌ Failed to subscribe to {channel} for {symbol}: {response.status_code}")
            except Exception as e:
                print(f"❌ Subscription error for {channel} {symbol}: {e}")
    
    return success_count > 0

async def test_get_latest_data():
    """Test getting latest market data."""
    print("\n📊 Testing data retrieval...")
    
    # Wait a bit for data to accumulate
    print("⏳ Waiting for data to accumulate...")
    await asyncio.sleep(5)
    
    success_count = 0
    
    for symbol in TEST_SYMBOLS[:1]:  # Test with first symbol only
        try:
            payload = {
                "symbol": symbol,
                "data_type": "ticker"
            }
            
            response = requests.post(f"{BASE_URL}/data", json=payload)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("data"):
                    print(f"✅ Retrieved data for {symbol}: {data['data'].get('data_type', 'unknown')}")
                    success_count += 1
                else:
                    print(f"⚠️  No data available for {symbol}: {data}")
            else:
                print(f"❌ Failed to get data for {symbol}: {response.status_code}")
        except Exception as e:
            print(f"❌ Data retrieval error for {symbol}: {e}")
    
    return success_count > 0

async def test_data_quality():
    """Test data quality metrics."""
    print("\n📈 Testing data quality metrics...")
    
    try:
        response = requests.get(f"{BASE_URL}/quality")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Data quality metrics: {data}")
            return True
        else:
            print(f"❌ Failed to get quality metrics: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Quality metrics error: {e}")
        return False

async def test_connections_list():
    """Test listing active connections."""
    print("\n🔗 Testing connections list...")
    
    try:
        response = requests.get(f"{BASE_URL}/connections")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Active connections: {data}")
            return True
        else:
            print(f"❌ Failed to list connections: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connections list error: {e}")
        return False

async def test_market_summary():
    """Test market summary endpoint."""
    print("\n📋 Testing market summary...")
    
    try:
        response = requests.get(f"{BASE_URL}/summary?symbols={','.join(TEST_SYMBOLS[:1])}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Market summary: {data}")
            return True
        else:
            print(f"❌ Failed to get market summary: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Market summary error: {e}")
        return False

async def test_disconnect():
    """Test disconnecting from exchange."""
    print("\n🔌 Testing disconnection...")
    
    try:
        payload = {
            "exchange_name": "binanceus"
        }
        
        response = requests.post(f"{BASE_URL}/disconnect", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Disconnection successful: {data}")
            return True
        else:
            print(f"❌ Disconnection failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Disconnection error: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive test suite."""
    print("🚀 Starting Real-Time Data Hub Agent Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Health Check
    test_results.append(await test_health_check())
    
    # Test 2: Connect to Exchange
    test_results.append(await test_connect_to_exchange())
    
    # Test 3: Subscribe to Channels
    test_results.append(await test_subscribe_to_channels())
    
    # Test 4: Get Latest Data
    test_results.append(await test_get_latest_data())
    
    # Test 5: Data Quality
    test_results.append(await test_data_quality())
    
    # Test 6: List Connections
    test_results.append(await test_connections_list())
    
    # Test 7: Market Summary
    test_results.append(await test_market_summary())
    
    # Test 8: Disconnect
    test_results.append(await test_disconnect())
    
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
        print("\n🎉 ALL TESTS PASSED! Real-Time Data Hub is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the logs.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(run_comprehensive_test())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        exit(1) 