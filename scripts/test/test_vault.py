#!/usr/bin/env python3
"""
Test script for VolexSwarm Vault integration.
"""

import os
import sys
import asyncio

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.vault import VaultClient, get_vault_client


def test_vault_connection():
    """Test basic Vault connection."""
    print("Testing Vault connection...")
    
    try:
        client = VaultClient()
        if client.health_check():
            print("✓ Vault connection successful")
            return True
        else:
            print("✗ Vault connection failed")
            return False
    except Exception as e:
        print(f"✗ Vault connection error: {e}")
        return False


def test_secret_retrieval():
    """Test secret retrieval functionality."""
    print("\nTesting secret retrieval...")
    
    try:
        client = get_vault_client()
        
        # Test getting a specific secret
        secret = client.get_secret("api_keys/binance")
        if secret:
            print("✓ Secret retrieval successful")
            print(f"  Found keys: {list(secret.keys())}")
        else:
            print("✗ Secret retrieval failed")
        
        # Test getting API key
        api_key = client.get_api_key("binance", "api_key")
        if api_key:
            print("✓ API key retrieval successful")
        else:
            print("✗ API key retrieval failed")
        
        # Test getting exchange credentials
        creds = client.get_exchange_credentials("binance")
        if creds:
            print("✓ Exchange credentials retrieval successful")
            print(f"  Credential types: {list(creds.keys())}")
        else:
            print("✗ Exchange credentials retrieval failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Secret retrieval error: {e}")
        return False


def test_agent_config():
    """Test agent configuration retrieval."""
    print("\nTesting agent configuration...")
    
    try:
        client = get_vault_client()
        
        # Test getting research agent config
        config = client.get_agent_config("research")
        if config:
            print("✓ Agent configuration retrieval successful")
            print(f"  Config keys: {list(config.keys())}")
        else:
            print("✗ Agent configuration retrieval failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent configuration error: {e}")
        return False


def test_list_secrets():
    """Test listing secrets functionality."""
    print("\nTesting secret listing...")
    
    try:
        client = get_vault_client()
        
        # List top-level secrets
        secrets = client.list_secrets()
        if secrets:
            print("✓ Secret listing successful")
            print(f"  Found paths: {secrets}")
        else:
            print("✗ Secret listing failed")
        
        return True
        
    except Exception as e:
        print(f"✗ Secret listing error: {e}")
        return False


def main():
    """Run all tests."""
    print("VolexSwarm Vault Integration Test")
    print("=" * 40)
    
    # Check environment variables
    vault_addr = os.getenv('VAULT_ADDR', 'http://localhost:8200')
    vault_token = os.getenv('VAULT_TOKEN')
    
    print(f"VAULT_ADDR: {vault_addr}")
    print(f"VAULT_TOKEN: {'***' if vault_token else 'NOT SET'}")
    
    if not vault_token:
        print("Error: VAULT_TOKEN environment variable is required")
        sys.exit(1)
    
    # Run tests
    tests = [
        test_vault_connection,
        test_secret_retrieval,
        test_agent_config,
        test_list_secrets
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Vault integration is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check your Vault setup.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 