#!/usr/bin/env python3
"""
Configure OpenAI API Key in Vault
This script helps configure the OpenAI API key in HashiCorp Vault for VolexSwarm agents.
"""

import os
import sys
import getpass
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from common.vault import VaultClient
from common.logging import get_logger

logger = get_logger("configure_openai_vault")

def configure_openai_api_key():
    """Configure OpenAI API key in Vault."""
    try:
        logger.info("🔧 Configuring OpenAI API Key in Vault...")
        
        # Initialize Vault client
        vault_client = VaultClient()
        
        # Check if OpenAI API key is already configured
        try:
            existing_key = vault_client.get_secret("openai", "api_key")
            if existing_key and len(existing_key) > 10:
                logger.info("✅ OpenAI API key is already configured in Vault")
                logger.info(f"   Key preview: {existing_key[:8]}...")
                
                # Test the key by making a simple API call
                import openai
                openai.api_key = existing_key
                
                try:
                    # Simple test call
                    response = openai.Model.list()
                    logger.info("✅ OpenAI API key is valid and working")
                    return True
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI API key exists but may be invalid: {e}")
                    
        except Exception as e:
            logger.info("ℹ️ No existing OpenAI API key found in Vault")
        
        # Prompt for OpenAI API key
        print("\n" + "="*60)
        print("🔑 OpenAI API Key Configuration")
        print("="*60)
        print("To enable LLM-driven decision making, please provide your OpenAI API key.")
        print("You can get one from: https://platform.openai.com/api-keys")
        print("The key will be securely stored in HashiCorp Vault.")
        print()
        
        api_key = getpass.getpass("Enter your OpenAI API key (input hidden): ").strip()
        
        if not api_key:
            logger.error("❌ No API key provided")
            return False
        
        if not api_key.startswith("sk-"):
            logger.error("❌ Invalid OpenAI API key format (should start with 'sk-')")
            return False
        
        # Store in Vault
        logger.info("💾 Storing OpenAI API key in Vault...")
        vault_client.store_secret("openai", {"api_key": api_key})
        
        # Verify storage
        stored_key = vault_client.get_secret("openai", "api_key")
        if stored_key == api_key:
            logger.info("✅ OpenAI API key successfully stored in Vault")
            
            # Test the key
            logger.info("🧪 Testing OpenAI API key...")
            import openai
            openai.api_key = api_key
            
            try:
                response = openai.Model.list()
                logger.info("✅ OpenAI API key is valid and working")
                logger.info("🎯 LLM functionality is now enabled for VolexSwarm agents")
                return True
            except Exception as e:
                logger.error(f"❌ OpenAI API key test failed: {e}")
                logger.error("💡 Please check your API key and try again")
                return False
        else:
            logger.error("❌ Failed to store OpenAI API key in Vault")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to configure OpenAI API key: {e}")
        return False

def restart_agents():
    """Restart agents to pick up new OpenAI configuration."""
    try:
        logger.info("🔄 Restarting agents to pick up OpenAI configuration...")
        
        import subprocess
        
        # Restart the agent containers
        agent_services = [
            "volexswarm-news-sentiment",
            "volexswarm-strategy-discovery", 
            "volexswarm-meta-agent",
            "volexswarm-execution",
            "volexswarm-monitor"
        ]
        
        for service in agent_services:
            try:
                logger.info(f"🔄 Restarting {service}...")
                result = subprocess.run(
                    ["docker", "restart", service],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    logger.info(f"✅ {service} restarted successfully")
                else:
                    logger.warning(f"⚠️ Failed to restart {service}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"⏰ Timeout restarting {service}")
            except Exception as e:
                logger.warning(f"⚠️ Error restarting {service}: {e}")
        
        logger.info("🎯 Agent restart completed")
        logger.info("💡 Agents should now have access to OpenAI API")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to restart agents: {e}")
        return False

def main():
    """Main configuration function."""
    try:
        print("🚀 VolexSwarm OpenAI Configuration")
        print("="*50)
        
        # Configure OpenAI API key
        if configure_openai_api_key():
            print("\n✅ OpenAI API key configured successfully!")
            
            # Ask if user wants to restart agents
            restart = input("\nRestart agents to enable LLM functionality? (y/N): ").strip().lower()
            if restart in ['y', 'yes']:
                if restart_agents():
                    print("\n🎉 Configuration complete!")
                    print("🎯 VolexSwarm agents now have LLM capabilities enabled")
                    print("🧪 Run the direct agent test to verify LLM integration")
                else:
                    print("\n⚠️ Agent restart failed - you may need to restart manually")
            else:
                print("\n💡 Remember to restart agents to enable LLM functionality:")
                print("   docker-compose restart")
        else:
            print("\n❌ OpenAI configuration failed")
            return 1
            
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Configuration cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Configuration failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
