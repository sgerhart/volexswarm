#!/usr/bin/env python3
"""
Script to update Binance API keys in Vault
"""

import os
import sys
import hvac
from getpass import getpass

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from common.vault import get_vault_client

def update_binance_keys():
    """Update Binance API keys in Vault."""
    try:
        # Get Vault client
        vault_client = get_vault_client()
        
        print("🔐 Updating Binance API Keys in Vault")
        print("=" * 50)
        
        # Get current keys
        current_keys = vault_client.get_exchange_credentials("binance")
        if current_keys:
            print(f"Current API Key: {current_keys.get('api_key', 'Not found')[:20]}...")
            print(f"Current Secret Key: {current_keys.get('secret_key', 'Not found')[:20]}...")
        else:
            print("No current Binance keys found in Vault")
        
        print("\n📝 Enter new Binance API credentials:")
        print("(Press Enter to keep current values)")
        
        # Get new API key
        new_api_key = input("New API Key: ").strip()
        if not new_api_key and current_keys:
            new_api_key = current_keys.get('api_key')
        
        # Get new secret key
        new_secret_key = getpass("New Secret Key: ").strip()
        if not new_secret_key and current_keys:
            new_secret_key = current_keys.get('secret_key')
        
        if not new_api_key or not new_secret_key:
            print("❌ Both API key and secret key are required")
            return False
        
        # Update Vault
        new_credentials = {
            'api_key': new_api_key,
            'secret_key': new_secret_key
        }
        
        success = vault_client.put_secret("api_keys/binance", new_credentials)
        
        if success:
            print("✅ Binance API keys updated successfully in Vault")
            print(f"New API Key: {new_api_key[:20]}...")
            return True
        else:
            print("❌ Failed to update Binance API keys in Vault")
            return False
            
    except Exception as e:
        print(f"❌ Error updating Binance API keys: {str(e)}")
        return False

def test_binance_connection():
    """Test the Binance connection with current keys."""
    try:
        import ccxt.async_support as ccxt_async
        import asyncio
        
        print("\n🧪 Testing Binance Connection...")
        
        # Get credentials from Vault
        vault_client = get_vault_client()
        credentials = vault_client.get_exchange_credentials("binance")
        
        if not credentials:
            print("❌ No Binance credentials found in Vault")
            return False
        
        async def test_connection():
            try:
                # Initialize exchange
                exchange = ccxt_async.binance({
                    'apiKey': credentials.get('api_key'),
                    'secret': credentials.get('secret_key'),
                    'sandbox': False,  # Test with real API
                    'enableRateLimit': True,
                })
                
                # Test connection
                await exchange.load_markets()
                print("✅ Successfully connected to Binance")
                
                # Test market data (no API key required)
                ticker = await exchange.fetch_ticker('BTC/USDT')
                print(f"✅ Market data working: BTC/USDT = ${ticker['last']}")
                
                # Test account balance (requires API key)
                try:
                    balance = await exchange.fetch_balance()
                    print("✅ Account balance access working")
                    usdt_balance = balance.get('USDT', {}).get('free', 0)
                    print(f"   USDT Balance: {usdt_balance}")
                except Exception as e:
                    print(f"⚠️  Account balance access failed: {str(e)}")
                    print("   This is expected if API key doesn't have read permissions")
                
                await exchange.close()
                return True
                
            except Exception as e:
                print(f"❌ Binance connection failed: {str(e)}")
                return False
        
        # Run the test
        result = asyncio.run(test_connection())
        return result
        
    except Exception as e:
        print(f"❌ Error testing Binance connection: {str(e)}")
        return False

if __name__ == "__main__":
    print("🏦 Binance API Key Management")
    print("=" * 50)
    
    # Update keys
    if update_binance_keys():
        print("\n" + "=" * 50)
        # Test connection
        test_binance_connection()
    
    print("\n📋 Next Steps:")
    print("1. If account balance access failed, update your Binance API key permissions")
    print("2. Enable 'Enable Reading' permission in Binance API Management")
    print("3. Disable IP restrictions or add your server's IP address")
    print("4. Restart the execution agent: docker-compose restart execution") 