#!/usr/bin/env python3
"""
Smart Portfolio Collection System Demo

This script demonstrates the hybrid portfolio collection system with:
1. Scheduled collection (every 15 minutes by default)
2. Event-driven collection (when portfolio changes by >2%)
3. Manual collection (force collection)
4. User-configurable settings
"""

import asyncio
import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
EXECUTION_AGENT_URL = "http://localhost:8002"
COLLECTION_CONFIG_ENDPOINT = f"{EXECUTION_AGENT_URL}/api/execution/portfolio-collection-config"
UPDATE_CONFIG_ENDPOINT = f"{EXECUTION_AGENT_URL}/api/execution/update-portfolio-collection-config"
FORCE_SNAPSHOT_ENDPOINT = f"{EXECUTION_AGENT_URL}/api/execution/force-portfolio-snapshot"
PORTFOLIO_HISTORY_ENDPOINT = f"{EXECUTION_AGENT_URL}/api/execution/portfolio-history"

async def get_portfolio_collection_config() -> Dict[str, Any]:
    """Get current portfolio collection configuration."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(COLLECTION_CONFIG_ENDPOINT)
            if response.status_code == 200:
                data = response.json()
                print("✅ Current Portfolio Collection Configuration:")
                for key, value in data['config'].items():
                    print(f"   {key}: {value}")
                return data['config']
            else:
                print(f"❌ Failed to get config: {response.status_code}")
                return {}
    except Exception as e:
        print(f"❌ Error getting config: {e}")
        return {}

async def update_portfolio_collection_config(updates: Dict[str, Any]) -> bool:
    """Update portfolio collection configuration."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(UPDATE_CONFIG_ENDPOINT, json=updates)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"✅ Configuration updated successfully: {list(updates.keys())}")
                    return True
                else:
                    print(f"❌ Configuration update failed: {data.get('message')}")
                    return False
            else:
                print(f"❌ Failed to update config: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error updating config: {e}")
        return False

async def force_portfolio_snapshot() -> bool:
    """Force a portfolio snapshot collection."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(FORCE_SNAPSHOT_ENDPOINT)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Portfolio snapshot forced successfully")
                    return True
                else:
                    print(f"❌ Forced snapshot failed: {data.get('message')}")
                    return False
            else:
                print(f"❌ Failed to force snapshot: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Error forcing snapshot: {e}")
        return False

async def get_portfolio_history(days: int = 1) -> Dict[str, Any]:
    """Get portfolio history data."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{PORTFOLIO_HISTORY_ENDPOINT}?days={days}")
            if response.status_code == 200:
                data = response.json()
                if 'data_points' in data:
                    print(f"✅ Portfolio history retrieved: {len(data['data_points'])} data points")
                    return data
                else:
                    print("❌ No data points in portfolio history")
                    return {}
            else:
                print(f"❌ Failed to get portfolio history: {response.status_code}")
                return {}
    except Exception as e:
        print(f"❌ Error getting portfolio history: {e}")
        return {}

async def demonstrate_smart_collection():
    """Demonstrate the smart portfolio collection system."""
    print("🚀 Smart Portfolio Collection System Demo")
    print("=" * 50)
    
    # Step 1: Show current configuration
    print("\n📋 Step 1: Current Configuration")
    current_config = await get_portfolio_collection_config()
    
    if not current_config:
        print("❌ Could not retrieve configuration")
        return
    
    # Step 2: Update configuration for testing
    print("\n⚙️ Step 2: Updating Configuration for Testing")
    test_updates = {
        'collection_frequency_minutes': 5,  # More frequent for testing
        'change_threshold_percent': 1.0,    # Lower threshold for testing
        'max_collections_per_hour': 120     # Higher limit for testing
    }
    
    success = await update_portfolio_collection_config(test_updates)
    if not success:
        print("❌ Configuration update failed")
        return
    
    # Step 3: Show updated configuration
    print("\n📋 Step 3: Updated Configuration")
    updated_config = await get_portfolio_collection_config()
    
    # Step 4: Force a portfolio snapshot
    print("\n📊 Step 4: Forcing Portfolio Snapshot")
    snapshot_success = await force_portfolio_snapshot()
    
    if snapshot_success:
        # Step 5: Show portfolio history
        print("\n📈 Step 5: Portfolio History Analysis")
        history = await get_portfolio_history(days=1)
        
        if history and 'data_points' in history:
            data_points = history['data_points']
            if data_points:
                print(f"   Total data points: {len(data_points)}")
                
                # Show recent entries
                recent = data_points[:5]
                print("   Recent portfolio values:")
                for i, point in enumerate(recent):
                    timestamp = point.get('timestamp', 'Unknown')
                    value = point.get('portfolio_value', 0)
                    print(f"     {i+1}. {timestamp}: ${value:.2f}")
                
                # Calculate collection frequency
                if len(data_points) > 1:
                    timestamps = [point.get('timestamp') for point in data_points if point.get('timestamp')]
                    if timestamps:
                        try:
                            # Parse timestamps and calculate intervals
                            parsed_times = []
                            for ts in timestamps:
                                if isinstance(ts, str):
                                    parsed_times.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                            
                            if len(parsed_times) > 1:
                                intervals = []
                                for i in range(1, len(parsed_times)):
                                    interval = (parsed_times[i] - parsed_times[i-1]).total_seconds() / 60
                                    intervals.append(interval)
                                
                                avg_interval = sum(intervals) / len(intervals)
                                print(f"   Average collection interval: {avg_interval:.1f} minutes")
                                
                                # Show collection pattern
                                print("   Collection pattern analysis:")
                                rapid_collections = [i for i in intervals if i < 1]  # Less than 1 minute
                                normal_collections = [i for i in intervals if 1 <= i <= 30]  # 1-30 minutes
                                slow_collections = [i for i in intervals if i > 30]  # More than 30 minutes
                                
                                print(f"     Rapid collections (<1 min): {len(rapid_collections)}")
                                print(f"     Normal collections (1-30 min): {len(normal_collections)}")
                                print(f"     Slow collections (>30 min): {len(slow_collections)}")
                                
                        except Exception as e:
                            print(f"   Could not analyze collection intervals: {e}")
    
    # Step 6: Restore original configuration
    print("\n🔄 Step 6: Restoring Original Configuration")
    restore_updates = {
        'collection_frequency_minutes': 15,  # Back to default
        'change_threshold_percent': 2.0,     # Back to default
        'max_collections_per_hour': 60       # Back to default
    }
    
    restore_success = await update_portfolio_collection_config(restore_updates)
    if restore_success:
        print("✅ Original configuration restored")
    else:
        print("❌ Failed to restore original configuration")
    
    print("\n🎯 Demo Complete!")
    print("\nKey Benefits of Smart Collection System:")
    print("✅ Reduces excessive database writes")
    print("✅ Captures significant portfolio changes")
    print("✅ User-configurable collection frequency")
    print("✅ Smart deduplication of similar data")
    print("✅ Maintains data quality while optimizing performance")

async def main():
    """Main demo function."""
    try:
        await demonstrate_smart_collection()
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")

if __name__ == "__main__":
    print("Starting Smart Portfolio Collection Demo...")
    print("Make sure the Execution Agent is running on port 8002")
    print("Press Ctrl+C to stop the demo\n")
    
    asyncio.run(main())
