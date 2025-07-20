"""
Crypto utilities for encrypting/decrypting sensitive data in Vault backups.
Uses AES-256-GCM for authenticated encryption.
"""

import os
import base64
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import getpass
import sys

class VaultBackupCrypto:
    """Handles encryption/decryption of Vault backup data."""
    
    def __init__(self, master_key=None):
        """
        Initialize crypto handler.
        
        Args:
            master_key: Optional master key. If not provided, will prompt user.
        """
        self.master_key = master_key or self._get_master_key()
        self.salt = b'volexswarm_backup_salt_2024'  # Fixed salt for consistency
    
    def _get_master_key(self):
        """Get master key from user input."""
        print("🔐 Enter master key for backup encryption:")
        print("   This key will be used to encrypt/decrypt sensitive data.")
        print("   Store this key securely - you'll need it to restore backups.")
        print()
        
        while True:
            key1 = getpass.getpass("Master key: ")
            key2 = getpass.getpass("Confirm master key: ")
            
            if key1 == key2:
                if len(key1) < 8:
                    print("❌ Master key must be at least 8 characters long.")
                    continue
                return key1
            else:
                print("❌ Keys don't match. Please try again.")
    
    def _derive_key(self, key, salt):
        """Derive encryption key from master key using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(key.encode())
    
    def _generate_nonce(self):
        """Generate a random nonce for GCM mode."""
        return os.urandom(12)
    
    def encrypt_data(self, data):
        """
        Encrypt sensitive data.
        
        Args:
            data: Dictionary containing sensitive data
            
        Returns:
            Dictionary with encrypted data and metadata
        """
        # Convert data to JSON string
        json_data = json.dumps(data, sort_keys=True)
        
        # Generate encryption key
        key = self._derive_key(self.master_key, self.salt)
        nonce = self._generate_nonce()
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt data
        ciphertext = encryptor.update(json_data.encode()) + encryptor.finalize()
        
        # Combine nonce, ciphertext, and tag
        encrypted_data = nonce + encryptor.tag + ciphertext
        
        # Return encrypted data with metadata
        return {
            "version": "1.0",
            "algorithm": "AES-256-GCM",
            "salt": base64.b64encode(self.salt).decode(),
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "timestamp": self._get_timestamp()
        }
    
    def decrypt_data(self, encrypted_dict):
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_dict: Dictionary containing encrypted data
            
        Returns:
            Original data dictionary
        """
        try:
            # Extract components
            encrypted_data = base64.b64decode(encrypted_dict["encrypted_data"])
            nonce = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Generate decryption key
            key = self._derive_key(self.master_key, self.salt)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Decrypt data
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Parse JSON
            return json.loads(plaintext.decode())
            
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def is_encrypted(self, data):
        """
        Check if data is encrypted.
        
        Args:
            data: Data to check
            
        Returns:
            True if data appears to be encrypted
        """
        return (
            isinstance(data, dict) and
            "version" in data and
            "encrypted_data" in data and
            "algorithm" in data
        )

def prompt_for_master_key():
    """Prompt user for master key."""
    print("🔐 Enter master key for backup decryption:")
    return getpass.getpass("Master key: ")

def encrypt_sensitive_fields(data, sensitive_patterns=None, crypto_instance=None):
    """
    Recursively encrypt sensitive fields in data structure.
    
    Args:
        data: Data structure to process
        sensitive_patterns: List of patterns that indicate sensitive data
        crypto_instance: Pre-initialized VaultBackupCrypto instance (optional)
        
    Returns:
        Data structure with sensitive fields encrypted
    """
    if sensitive_patterns is None:
        sensitive_patterns = [
            'api_key', 'secret_key', 'password', 'token', 'secret',
            'private_key', 'privatekey', 'apikey', 'secretkey'
        ]
    
    # Create crypto instance if not provided
    if crypto_instance is None:
        crypto_instance = VaultBackupCrypto()
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            # Check if this key indicates sensitive data
            key_lower = key.lower()
            is_sensitive = any(pattern in key_lower for pattern in sensitive_patterns)
            
            if is_sensitive and isinstance(value, str):
                # Encrypt sensitive string values using the same crypto instance
                result[key] = crypto_instance.encrypt_data({"value": value})
            elif isinstance(value, (dict, list)):
                # Recursively process nested structures
                result[key] = encrypt_sensitive_fields(value, sensitive_patterns, crypto_instance)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [encrypt_sensitive_fields(item, sensitive_patterns, crypto_instance) for item in data]
    else:
        return data

def decrypt_sensitive_fields(data, master_key):
    """
    Recursively decrypt sensitive fields in data structure.
    
    Args:
        data: Data structure to process
        master_key: Master key for decryption
        
    Returns:
        Data structure with sensitive fields decrypted
    """
    crypto = VaultBackupCrypto(master_key)
    
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if crypto.is_encrypted(value):
                # Decrypt encrypted data
                try:
                    decrypted = crypto.decrypt_data(value)
                    result[key] = decrypted.get("value", decrypted)
                except Exception as e:
                    print(f"⚠️  Warning: Failed to decrypt {key}: {e}")
                    result[key] = value  # Keep encrypted if decryption fails
            elif isinstance(value, (dict, list)):
                # Recursively process nested structures
                result[key] = decrypt_sensitive_fields(value, master_key)
            else:
                result[key] = value
        return result
    elif isinstance(data, list):
        return [decrypt_sensitive_fields(item, master_key) for item in data]
    else:
        return data 