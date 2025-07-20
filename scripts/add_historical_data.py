#!/usr/bin/env python3
"""
Add historical price data to database for ML training.
"""

import sys
import os
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.db import get_db_client
from common.models import PriceData


def add_historical_data():
    """Add historical price data to the database."""
    try:
        db_client = get_db_client()
        session = db_client.get_session()
        
        # Generate realistic historical price data
        np.random.seed(42)
        base_price = 50000  # BTC starting price
        days = 30
        prices = []
        
        print("📊 Generating historical price data...")
        
        for i in range(days * 24):  # Hourly data
            # Random walk with trend
            change = np.random.normal(0, 0.02)  # 2% volatility
            if i > 0:
                base_price *= (1 + change)
            prices.append(max(base_price, 1000))  # Minimum price
        
        # Add price data to database with different timestamps
        for i, price in enumerate(prices):
            # Create timestamps going backwards from now
            timestamp = datetime.now() - timedelta(hours=len(prices)-i)
            
            # Create price data entry
            price_data = PriceData(
                time=timestamp,
                symbol="BTCUSD",
                exchange="binanceus",
                open=price * 0.999,
                high=price * 1.002,
                low=price * 0.998,
                close=price,
                volume=np.random.uniform(100, 1000),
                timeframe="1h"
            )
            
            session.add(price_data)
            
            if i % 100 == 0:
                print(f"   - Added {i+1}/{len(prices)} historical price data points")
        
        session.commit()
        session.close()
        
        print(f"✅ Successfully added {len(prices)} historical price data points to database")
        print(f"   - Symbol: BTCUSD")
        print(f"   - Timeframe: 1h")
        print(f"   - Date range: {timestamp.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to add historical data: {e}")
        return False


if __name__ == "__main__":
    print("Adding Historical Price Data for ML Training")
    print("=" * 45)
    
    if add_historical_data():
        print("\n✅ Historical data added successfully!")
        print("\nNext steps:")
        print("1. Test ML model training: curl -X POST 'http://localhost:8003/models/train?symbol=BTCUSD'")
        print("2. Test signal generation: curl -X POST 'http://localhost:8003/signals/generate?symbol=BTCUSD'")
        print("3. Run full AI test: python scripts/test_autonomous_ai.py")
    else:
        print("\n❌ Failed to add historical data!")
        sys.exit(1) 