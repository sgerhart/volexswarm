#!/usr/bin/env python3
"""
Initialize OpenAI configuration in Vault for VolexSwarm GPT integration.
"""

import os
import sys
import getpass
from typing import Optional

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from common.vault import get_vault_client
from common.logging import get_logger

logger = get_logger("openai_init")


def init_openai_config():
    """Initialize OpenAI configuration in Vault."""
    print("🤖 VolexSwarm OpenAI GPT Integration Setup")
    print("=" * 50)
    
    try:
        # Get Vault client
        vault_client = get_vault_client()
        
        # Check if OpenAI config already exists
        existing_config = vault_client.get_secret("api_keys/openai")
        if existing_config and existing_config.get("api_key"):
            print("✅ OpenAI configuration already exists in Vault")
            print(f"   API Key: {existing_config['api_key'][:10]}...")
            
            update = input("Do you want to update the configuration? (y/N): ").lower().strip()
            if update != 'y':
                print("Configuration unchanged.")
                return
        
        # Get OpenAI API key
        print("\n📝 OpenAI Configuration:")
        print("You need an OpenAI API key to enable GPT integration.")
        print("Get your API key from: https://platform.openai.com/api-keys")
        print()
        
        api_key = getpass.getpass("Enter your OpenAI API key: ").strip()
        
        if not api_key:
            print("❌ No API key provided. Skipping OpenAI configuration.")
            return
        
        # Validate API key format (basic check)
        if not api_key.startswith("sk-"):
            print("⚠️  Warning: API key doesn't start with 'sk-'. Please verify your key.")
            continue_anyway = input("Continue anyway? (y/N): ").lower().strip()
            if continue_anyway != 'y':
                return
        
        # Get model preference
        print("\n🤖 Model Selection:")
        print("Available models:")
        print("1. gpt-4o-mini (recommended - fast, cost-effective)")
        print("2. gpt-4o (more capable, higher cost)")
        print("3. gpt-3.5-turbo (legacy, lower cost)")
        print()
        
        model_choice = input("Select model (1-3, default: 1): ").strip()
        
        model_map = {
            "1": "gpt-4o-mini",
            "2": "gpt-4o", 
            "3": "gpt-3.5-turbo"
        }
        
        selected_model = model_map.get(model_choice, "gpt-4o-mini")
        
        # Get configuration options
        print("\n⚙️  Configuration Options:")
        
        max_tokens = input("Max tokens per response (default: 2000): ").strip()
        max_tokens = int(max_tokens) if max_tokens.isdigit() else 2000
        
        temperature = input("Temperature (0.0-1.0, default: 0.3): ").strip()
        try:
            temperature = float(temperature) if temperature else 0.3
            temperature = max(0.0, min(1.0, temperature))
        except ValueError:
            temperature = 0.3
        
        # Store configuration in Vault
        openai_config = {
            "api_key": api_key,
            "model": selected_model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "enabled": True
        }
        
        print(f"\n💾 Storing OpenAI configuration in Vault...")
        vault_client.store_secret("api_keys/openai", openai_config)
        
        # Test the configuration
        print("🧪 Testing OpenAI configuration...")
        test_result = test_openai_config(vault_client)
        
        if test_result:
            print("✅ OpenAI configuration stored and tested successfully!")
            print(f"   Model: {selected_model}")
            print(f"   Max Tokens: {max_tokens}")
            print(f"   Temperature: {temperature}")
            print("\n🚀 GPT integration is now ready!")
            print("   The system will use GPT for:")
            print("   • Market commentary generation")
            print("   • Advanced trading decision reasoning")
            print("   • Strategy insights and optimization")
        else:
            print("❌ OpenAI configuration test failed!")
            print("   Please check your API key and try again.")
            
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI configuration: {e}")
        print(f"❌ Error: {e}")


def test_openai_config(vault_client) -> bool:
    """Test OpenAI configuration by making a simple API call."""
    try:
        from common.openai_client import VolexSwarmOpenAIClient
        
        # Create test client
        test_client = VolexSwarmOpenAIClient()
        
        if not test_client.is_available():
            print("   ❌ OpenAI client not available")
            return False
        
        # Test with a simple prompt
        test_response = test_client.client.chat.completions.create(
            model=test_client.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant."
                },
                {
                    "role": "user", 
                    "content": "Respond with 'VolexSwarm GPT test successful'"
                }
            ],
            max_tokens=50,
            temperature=0.0
        )
        
        response_text = test_response.choices[0].message.content
        if "VolexSwarm GPT test successful" in response_text:
            print("   ✅ API connection successful")
            return True
        else:
            print(f"   ⚠️  Unexpected response: {response_text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False


def show_openai_status():
    """Show current OpenAI configuration status."""
    print("🤖 OpenAI Configuration Status")
    print("=" * 40)
    
    try:
        vault_client = get_vault_client()
        openai_config = vault_client.get_secret("api_keys/openai")
        
        if not openai_config or not openai_config.get("api_key"):
            print("❌ OpenAI configuration not found")
            print("   Run this script to set up GPT integration")
            return
        
        print("✅ OpenAI configuration found:")
        print(f"   Model: {openai_config.get('model', 'gpt-4o-mini')}")
        print(f"   Max Tokens: {openai_config.get('max_tokens', 2000)}")
        print(f"   Temperature: {openai_config.get('temperature', 0.3)}")
        print(f"   Enabled: {openai_config.get('enabled', True)}")
        print(f"   API Key: {openai_config['api_key'][:10]}...")
        
        # Test availability
        from common.openai_client import is_openai_available
        if is_openai_available():
            print("   🟢 GPT integration is active and ready")
        else:
            print("   🔴 GPT integration is configured but not working")
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize OpenAI configuration for VolexSwarm")
    parser.add_argument("--status", action="store_true", help="Show current OpenAI status")
    parser.add_argument("--init", action="store_true", help="Initialize OpenAI configuration")
    
    args = parser.parse_args()
    
    if args.status:
        show_openai_status()
    elif args.init:
        init_openai_config()
    else:
        # Default behavior
        show_openai_status()
        print()
        init_choice = input("Do you want to initialize OpenAI configuration? (y/N): ").lower().strip()
        if init_choice == 'y':
            init_openai_config()


if __name__ == "__main__":
    main() 