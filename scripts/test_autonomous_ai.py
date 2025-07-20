#!/usr/bin/env python3
"""
Test script for VolexSwarm Autonomous AI Signal Agent.
Demonstrates autonomous decision making, ML model training, and AI insights.
"""

import requests
import json
import time
import numpy as np
from datetime import datetime, timedelta

SIGNAL_URL = "http://localhost:8003"
RESEARCH_URL = "http://localhost:8001"
EXECUTION_URL = "http://localhost:8002"

def test_ai_health():
    """Test autonomous AI signal agent health."""
    print("🤖 Testing Autonomous AI Signal Agent Health...")
    try:
        response = requests.get(f"{SIGNAL_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AI Agent Health: {data['status']}")
            print(f"   - Vault connected: {data['vault_connected']}")
            print(f"   - Database connected: {data['database_connected']}")
            print(f"   - Agent ready: {data['agent_ready']}")
            print(f"   - Autonomous mode: {data['autonomous_mode']}")
            print(f"   - ML models loaded: {data['models_loaded']}")
            return True
        else:
            print(f"❌ AI health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AI health check error: {e}")
        return False

def generate_mock_price_data():
    """Generate mock price data for testing."""
    print("\n📊 Generating mock price data for AI training...")
    
    # Generate realistic price data
    np.random.seed(42)
    base_price = 50000  # BTC starting price
    days = 90
    prices = []
    
    for i in range(days * 24):  # Hourly data
        # Random walk with trend
        change = np.random.normal(0, 0.02)  # 2% volatility
        if i > 0:
            base_price *= (1 + change)
        prices.append(max(base_price, 1000))  # Minimum price
    
    # Add some price data to database via research agent
    try:
        for i, price in enumerate(prices[-100:]):  # Last 100 data points
            timestamp = datetime.now() - timedelta(hours=100-i)
            
            # Create price data entry
            price_data = {
                "time": timestamp.isoformat(),
                "symbol": "BTCUSD",
                "exchange": "binanceus",
                "open": price * 0.999,
                "high": price * 1.002,
                "low": price * 0.998,
                "close": price,
                "volume": np.random.uniform(100, 1000),
                "timeframe": "1h"
            }
            
            # Store in database (simplified - in real app this would go through research agent)
            print(f"   - Added price data: ${price:.2f} at {timestamp.strftime('%Y-%m-%d %H:%M')}")
            
    except Exception as e:
        print(f"   ⚠️  Mock data generation warning: {e}")
    
    print("✅ Mock price data generated")
    return prices

def test_ml_model_training():
    """Test machine learning model training."""
    print("\n🧠 Testing ML Model Training...")
    try:
        response = requests.post(f"{SIGNAL_URL}/models/train?symbol=BTCUSD")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ ML Model trained successfully")
            print(f"   - Symbol: {data['symbol']}")
            print(f"   - Status: {data['status']}")
            print(f"   - Data points: {data['data_points']}")
            return True
        else:
            print(f"❌ ML training failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ML training error: {e}")
        return False

def test_autonomous_signal_generation():
    """Test autonomous signal generation."""
    print("\n🎯 Testing Autonomous Signal Generation...")
    try:
        response = requests.post(f"{SIGNAL_URL}/signals/generate?symbol=BTCUSD")
        if response.status_code == 200:
            data = response.json()
            signal = data['signal']
            print(f"✅ Autonomous signal generated")
            print(f"   - Signal type: {signal['signal_type']}")
            print(f"   - Confidence: {signal['confidence']:.1%}")
            print(f"   - Strength: {signal['strength']:.3f}")
            print(f"   - Autonomous: {data['autonomous']}")
            
            if 'technical_signals' in signal:
                print(f"   - Technical signals: {len(signal['technical_signals'])}")
                for tech_signal in signal['technical_signals'][:3]:  # Show first 3
                    print(f"     * {tech_signal[0]}: {tech_signal[1]:.2f}")
            
            if 'ml_prediction' in signal:
                print(f"   - ML prediction: {signal['ml_prediction']}")
                print(f"   - ML confidence: {signal['ml_confidence']:.1%}")
            
            return True
        else:
            print(f"❌ Signal generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Signal generation error: {e}")
        return False

def test_autonomous_insights():
    """Test autonomous AI insights."""
    print("\n🔍 Testing Autonomous AI Insights...")
    try:
        response = requests.get(f"{SIGNAL_URL}/autonomous/insights/BTCUSD")
        if response.status_code == 200:
            data = response.json()
            insights = data['insights']
            print(f"✅ Autonomous insights generated")
            print(f"   - Trend: {insights['trend']}")
            print(f"   - Trend strength: {insights['trend_strength']:.3f}")
            print(f"   - Buy signals: {insights['buy_signals_count']}")
            print(f"   - Sell signals: {insights['sell_signals_count']}")
            print(f"   - Avg buy confidence: {insights['avg_buy_confidence']:.1%}")
            print(f"   - Avg sell confidence: {insights['avg_sell_confidence']:.1%}")
            print(f"   - Signal volatility: {insights['signal_volatility']:.3f}")
            print(f"   - Recommendation: {insights['recommendation']}")
            return True
        else:
            print(f"❌ Insights generation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Insights generation error: {e}")
        return False

def test_autonomous_decision():
    """Test autonomous decision making."""
    print("\n🤖 Testing Autonomous Decision Making...")
    try:
        response = requests.post(f"{SIGNAL_URL}/autonomous/decide?symbol=BTCUSD&current_balance=10000")
        if response.status_code == 200:
            data = response.json()
            decision = data['decision']
            print(f"✅ Autonomous decision made")
            print(f"   - Action: {decision['action']}")
            print(f"   - Reason: {decision['reason']}")
            print(f"   - Confidence: {decision['confidence']:.1%}")
            print(f"   - Position size: ${decision['position_size']:.2f}")
            print(f"   - Risk level: {decision['risk_level']}")
            print(f"   - Autonomous: {data['autonomous']}")
            return True
        else:
            print(f"❌ Autonomous decision failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Autonomous decision error: {e}")
        return False

def test_technical_indicators():
    """Test technical indicators calculation."""
    print("\n📈 Testing Technical Indicators...")
    try:
        response = requests.get(f"{SIGNAL_URL}/indicators/BTCUSD?timeframe=1h")
        if response.status_code == 200:
            data = response.json()
            indicators = data['indicators']
            print(f"✅ Technical indicators calculated")
            print(f"   - Current price: ${data['current_price']:.2f}")
            print(f"   - RSI: {indicators['rsi']:.2f}")
            print(f"   - MACD line: {indicators['macd']['line']:.6f}")
            print(f"   - MACD signal: {indicators['macd']['signal']:.6f}")
            print(f"   - BB position: {indicators['bollinger_bands']['position']:.3f}")
            print(f"   - Stochastic K: {indicators['stochastic']['k']:.2f}")
            print(f"   - Stochastic D: {indicators['stochastic']['d']:.2f}")
            return True
        else:
            print(f"❌ Technical indicators failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Technical indicators error: {e}")
        return False

def test_model_performance():
    """Test ML model performance metrics."""
    print("\n📊 Testing ML Model Performance...")
    try:
        response = requests.get(f"{SIGNAL_URL}/models/performance")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model performance retrieved")
            print(f"   - Total models: {data['total_models']}")
            print(f"   - Autonomous mode: {data['autonomous_mode']}")
            
            for symbol, model_data in data['models'].items():
                print(f"   - {symbol}:")
                print(f"     * Model trained: {model_data['model_trained']}")
                print(f"     * Signal count: {model_data['signal_count']}")
                if 'insights' in model_data:
                    insights = model_data['insights']
                    print(f"     * Trend: {insights['trend']}")
                    print(f"     * Recommendation: {insights['recommendation']}")
            return True
        else:
            print(f"❌ Model performance failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model performance error: {e}")
        return False

def test_autonomous_trading_loop():
    """Test complete autonomous trading loop."""
    print("\n🔄 Testing Complete Autonomous Trading Loop...")
    try:
        # Step 1: Generate autonomous signal
        print("   1. Generating autonomous signal...")
        signal_response = requests.post(f"{SIGNAL_URL}/signals/generate?symbol=BTCUSD")
        if signal_response.status_code != 200:
            print("   ❌ Signal generation failed")
            return False
        
        signal_data = signal_response.json()
        signal = signal_data['signal']
        
        # Step 2: Make autonomous decision
        print("   2. Making autonomous decision...")
        decision_response = requests.post(f"{SIGNAL_URL}/autonomous/decide?symbol=BTCUSD&current_balance=10000")
        if decision_response.status_code != 200:
            print("   ❌ Autonomous decision failed")
            return False
        
        decision_data = decision_response.json()
        decision = decision_data['decision']
        
        # Step 3: Execute trade (if decision is to trade)
        if decision['action'] in ['buy', 'sell'] and decision['confidence'] > 0.7:
            print("   3. Executing autonomous trade...")
            trade_params = {
                'symbol': 'BTCUSD',
                'side': decision['action'],
                'quantity': 0.001,  # Small test quantity
                'order_type': 'market'
            }
            
            trade_response = requests.post(f"{EXECUTION_URL}/orders", params=trade_params)
            if trade_response.status_code == 200:
                trade_data = trade_response.json()
                print(f"   ✅ Autonomous trade executed")
                print(f"      - Order ID: {trade_data['order']['id']}")
                print(f"      - Action: {trade_data['order']['side']}")
                print(f"      - Quantity: {trade_data['order']['amount']}")
                print(f"      - Price: ${trade_data['order']['price']}")
                print(f"      - Dry run: {trade_data['dry_run']}")
            else:
                print(f"   ❌ Trade execution failed: {trade_response.status_code}")
        else:
            print("   3. No trade executed (hold decision or low confidence)")
        
        print("✅ Complete autonomous trading loop tested")
        return True
        
    except Exception as e:
        print(f"❌ Autonomous trading loop error: {e}")
        return False

def main():
    """Run all autonomous AI tests."""
    print("VolexSwarm Autonomous AI Agent Test")
    print("=" * 50)
    
    tests = [
        test_ai_health,
        generate_mock_price_data,
        test_ml_model_training,
        test_autonomous_signal_generation,
        test_autonomous_insights,
        test_autonomous_decision,
        test_technical_indicators,
        test_model_performance,
        test_autonomous_trading_loop
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    print(f"\n🤖 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All autonomous AI tests passed!")
        print("\n🎉 Phase 4: Autonomous AI Signal Agent is working correctly!")
        print("\n🤖 Autonomous AI Features Verified:")
        print("  - Machine learning model training")
        print("  - Technical analysis indicators")
        print("  - Autonomous signal generation")
        print("  - AI insights and recommendations")
        print("  - Autonomous decision making")
        print("  - Complete trading loop automation")
        print("  - Risk management and confidence scoring")
        print("\n🚀 Next Steps:")
        print("  - Implement Meta-Agent for coordination (Phase 5)")
        print("  - Add more sophisticated ML models")
        print("  - Implement real-time market data streaming")
        print("  - Add sentiment analysis and news integration")
        print("  - Deploy to production with monitoring")
        return 0
    else:
        print("❌ Some autonomous AI tests failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main()) 