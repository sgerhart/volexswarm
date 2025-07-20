"""
Vault integration for VolexSwarm.
Provides secure credential management using HashiCorp Vault.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import hvac
from hvac.exceptions import VaultError

logger = logging.getLogger(__name__)


class VaultClient:
    """Client for interacting with HashiCorp Vault."""
    
    def __init__(self, vault_addr: Optional[str] = None, vault_token: Optional[str] = None):
        """Initialize Vault client."""
        self.vault_addr = vault_addr or os.getenv('VAULT_ADDR', 'http://localhost:8200')
        self.vault_token = vault_token or os.getenv('VAULT_TOKEN')
        
        if not self.vault_token:
            raise ValueError("VAULT_TOKEN environment variable is required")
        
        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.vault_token
        )
        
        # Test connection
        if not self.client.is_authenticated():
            raise VaultError("Failed to authenticate with Vault")
    
    def health_check(self) -> bool:
        """Check Vault connection health."""
        try:
            return self.client.is_authenticated()
        except Exception as e:
            logger.error(f"Vault health check failed: {e}")
            return False
    
    def get_secret(self, path: str, mount_point: str = 'secret') -> Optional[Dict[str, Any]]:
        """Get a secret from Vault."""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to get secret {path}: {e}")
            return None
    
    def put_secret(self, path: str, data: Dict[str, Any], mount_point: str = 'secret') -> bool:
        """Store a secret in Vault."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret_dict=data,
                mount_point=mount_point
            )
            return True
        except Exception as e:
            logger.error(f"Failed to put secret {path}: {e}")
            return False
    
    def list_secrets(self, path: str = '', mount_point: str = 'secret') -> List[str]:
        """List secrets at a path."""
        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=mount_point
            )
            return response['data']['keys']
        except Exception as e:
            logger.error(f"Failed to list secrets at {path}: {e}")
            return []
    
    def get_api_key(self, exchange: str, key_type: str = 'api_key') -> Optional[str]:
        """Get API key for a specific exchange."""
        try:
            secret = self.get_secret(f"api_keys/{exchange}")
            if secret:
                return secret.get(key_type)
            return None
        except Exception as e:
            logger.error(f"Failed to get API key for {exchange}: {e}")
            return None
    
    def get_exchange_credentials(self, exchange: str) -> Optional[Dict[str, str]]:
        """Get all credentials for an exchange."""
        try:
            return self.get_secret(f"api_keys/{exchange}")
        except Exception as e:
            logger.error(f"Failed to get credentials for {exchange}: {e}")
            return None
    
    def get_database_credentials(self, db_name: str = 'default') -> Optional[Dict[str, str]]:
        """Get database credentials."""
        try:
            return self.get_secret(f"databases/{db_name}")
        except Exception as e:
            logger.error(f"Failed to get database credentials for {db_name}: {e}")
            return None
    
    def get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration."""
        try:
            config = self.get_secret(f"agents/{agent_name}")
            if config:
                # Convert string values to appropriate types
                processed_config = {}
                for key, value in config.items():
                    if isinstance(value, str):
                        # Try to convert to list if it looks like a list
                        if value.startswith('[') and value.endswith(']'):
                            try:
                                # Simple list parsing - in production, use ast.literal_eval
                                processed_config[key] = [item.strip().strip("'\"") for item in value[1:-1].split(',')]
                            except:
                                processed_config[key] = value
                        # Try to convert to int
                        elif value.isdigit():
                            processed_config[key] = int(value)
                        # Try to convert to float
                        elif value.replace('.', '').isdigit():
                            processed_config[key] = float(value)
                        # Try to convert to boolean
                        elif value.lower() in ['true', 'false']:
                            processed_config[key] = value.lower() == 'true'
                        else:
                            processed_config[key] = value
                    else:
                        processed_config[key] = value
                return processed_config
            return None
        except Exception as e:
            logger.error(f"Failed to get agent config for {agent_name}: {e}")
            return None


# Global Vault client instance
_vault_client = None


def get_vault_client() -> VaultClient:
    """Get the global Vault client instance."""
    global _vault_client
    if _vault_client is None:
        _vault_client = VaultClient()
    return _vault_client


def get_api_key(exchange: str, key_type: str = 'api_key') -> Optional[str]:
    """Get API key for a specific exchange."""
    try:
        vault_client = get_vault_client()
        return vault_client.get_api_key(exchange, key_type)
    except Exception as e:
        logger.error(f"Failed to get API key: {e}")
        return None


def get_exchange_credentials(exchange: str) -> Optional[Dict[str, str]]:
    """Get all credentials for an exchange."""
    try:
        vault_client = get_vault_client()
        return vault_client.get_exchange_credentials(exchange)
    except Exception as e:
        logger.error(f"Failed to get exchange credentials: {e}")
        return None


def get_database_credentials(db_name: str = 'default') -> Optional[Dict[str, str]]:
    """Get database credentials."""
    try:
        vault_client = get_vault_client()
        return vault_client.get_database_credentials(db_name)
    except Exception as e:
        logger.error(f"Failed to get database credentials: {e}")
        return None


def get_agent_config(agent_name: str) -> Optional[Dict[str, Any]]:
    """Get agent configuration."""
    try:
        vault_client = get_vault_client()
        return vault_client.get_agent_config(agent_name)
    except Exception as e:
        logger.error(f"Failed to get agent config: {e}")
        return None


def list_secrets(path: str = '') -> List[str]:
    """List available secrets."""
    try:
        vault_client = get_vault_client()
        return vault_client.list_secrets(path)
    except Exception as e:
        logger.error(f"Failed to list secrets: {e}")
        return []


def health_check() -> bool:
    """Check Vault connection status."""
    try:
        vault_client = get_vault_client()
        return vault_client.health_check()
    except Exception as e:
        logger.error(f"Vault health check failed: {e}")
        return False 