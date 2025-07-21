#!/usr/bin/env python3
"""
Simple Vault test script using direct CLI commands.
"""

import subprocess
import sys

def run_vault_command(command: str) -> tuple[bool, str]:
    """Run a Vault CLI command and return success status and output."""
    try:
        full_command = f"docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=root volexswarm-vault vault {command}"
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode == 0, result.stdout
    except Exception as e:
        return False, str(e)

def test_vault_status():
    """Test Vault status."""
    print("Testing Vault status...")
    success, output = run_vault_command("status")
    if success:
        print("✓ Vault is running and accessible")
        return True
    else:
        print(f"✗ Vault status failed: {output}")
        return False

def test_secret_listing():
    """Test listing secrets."""
    print("Testing secret listing...")
    success, output = run_vault_command("kv list secret")
    if success and "Keys" in output:
        print("✓ Secret listing successful")
        print(f"  Found: {output.strip()}")
        return True
    else:
        print(f"✗ Secret listing failed: {output}")
        return False

def test_api_keys():
    """Test API key retrieval."""
    print("Testing API key retrieval...")
    success, output = run_vault_command("kv get secret/api_keys/binance")
    if success and "api_key" in output:
        print("✓ API key retrieval successful")
        return True
    else:
        print(f"✗ API key retrieval failed: {output}")
        return False

def test_agent_config():
    """Test agent configuration retrieval."""
    print("Testing agent configuration...")
    success, output = run_vault_command("kv get secret/agents/research")
    if success and ("enabled_pairs" in output or "data_sources" in output):
        print("✓ Agent configuration retrieval successful")
        return True
    else:
        print(f"✗ Agent configuration retrieval failed: {output}")
        return False

def main():
    """Run all Vault tests."""
    print("🔐 Simple Vault Test")
    print("=" * 30)
    
    tests = [
        test_vault_status,
        test_secret_listing,
        test_api_keys,
        test_agent_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Vault is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Check Vault setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 