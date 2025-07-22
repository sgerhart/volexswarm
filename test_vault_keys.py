#!/usr/bin/env python3
"""
Test script to check Vault API key configuration.
"""

import sys
import os

# Add the common module to the path
sys.path.insert(0, '/app/common')

def test_vault_keys():
    """Test Vault API key retrieval."""
    
    print("=== Vault API Key Test ===")
    
    try:
        from vault import get_vault_client
        
        # Get Vault client
        vault_client = get_vault_client()
        print("✅ Vault client created successfully")
        
        # Test OpenAI API key
        print("\n1. Testing OpenAI API key:")
        openai_config = vault_client.get_secret("api_keys/openai")
        if openai_config:
            print(f"   ✅ OpenAI config found: {type(openai_config)}")
            print(f"   Keys: {list(openai_config.keys()) if isinstance(openai_config, dict) else 'Not a dict'}")
            if isinstance(openai_config, dict) and 'api_key' in openai_config:
                api_key = openai_config['api_key']
                print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else 'short'}")
            else:
                print(f"   ❌ API key not found in config: {openai_config}")
        else:
            print("   ❌ OpenAI config not found")
        
        # Test Binance API key
        print("\n2. Testing Binance API key:")
        binance_config = vault_client.get_secret("api_keys/binanceus")
        if binance_config:
            print(f"   ✅ Binance config found: {type(binance_config)}")
            print(f"   Keys: {list(binance_config.keys()) if isinstance(binance_config, dict) else 'Not a dict'}")
            if isinstance(binance_config, dict):
                if 'api_key' in binance_config:
                    api_key = binance_config['api_key']
                    print(f"   API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else 'short'}")
                if 'secret_key' in binance_config:
                    secret_key = binance_config['secret_key']
                    print(f"   Secret Key: {secret_key[:10]}...{secret_key[-4:] if len(secret_key) > 14 else 'short'}")
            else:
                print(f"   ❌ Config is not a dict: {binance_config}")
        else:
            print("   ❌ Binance config not found")
        
        # List all secrets
        print("\n3. Available secrets:")
        try:
            secrets = vault_client.list_secrets("api_keys")
            print(f"   API Keys: {secrets}")
        except Exception as e:
            print(f"   ❌ Error listing secrets: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vault_keys() 