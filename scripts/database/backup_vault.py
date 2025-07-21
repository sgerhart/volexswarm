#!/usr/bin/env python3
"""
Secure Vault backup script for VolexSwarm.
Creates encrypted backups of Vault secrets with sensitive data encryption.
"""

import os
import sys
import subprocess
import json
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import base64
import secrets

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Configuration
BACKUP_DIR = Path("backup/vault")
SENSITIVE_FIELDS = {
    "api_key", "secret_key", "password", "token", "private_key", "secret"
}

class VaultBackupCrypto:
    """Cryptographic utilities for Vault backup encryption."""
    
    def __init__(self, master_key: str):
        """Initialize with master key."""
        self.master_key = master_key.encode('utf-8')
        self.backend = default_backend()
    
    def derive_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master key and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        return kdf.derive(self.master_key)
    
    def encrypt_field(self, data: str) -> str:
        """Encrypt a sensitive field."""
        try:
            # Generate salt and nonce
            salt = secrets.token_bytes(16)
            nonce = secrets.token_bytes(12)  # 96 bits for GCM
            
            # Derive key
            key = self.derive_key(salt)
            
            # Encrypt data
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=self.backend)
            encryptor = cipher.encryptor()
            
            ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
            tag = encryptor.tag
            
            # Combine salt + nonce + tag + ciphertext
            encrypted_data = salt + nonce + tag + ciphertext
            
            # Return base64 encoded
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            print(f"Warning: Failed to encrypt field: {e}")
            return data
    
    def decrypt_field(self, encrypted_data: str) -> str:
        """Decrypt a sensitive field."""
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract components
            salt = data[:16]
            nonce = data[16:28]
            tag = data[28:44]
            ciphertext = data[44:]
            
            # Derive key
            key = self.derive_key(salt)
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=self.backend)
            decryptor = cipher.decryptor()
            
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            print(f"Warning: Failed to decrypt field, returning as-is: {e}")
            return encrypted_data

def run_vault_command(command: str) -> str:
    """Run a Vault CLI command."""
    try:
        full_command = f"docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=root volexswarm-vault vault {command}"
        result = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Warning: Command failed: {result.stderr}")
        return result.stdout
    except Exception as e:
        print(f"Error running Vault command: {e}")
        return ""

def get_vault_secrets(path: str = "") -> Dict[str, Any]:
    """Recursively get all secrets from Vault."""
    secrets_data = {}
    
    try:
        # List secrets at current path
        list_result = run_vault_command(f"kv list secret/{path}")
        if not list_result or "Keys" not in list_result:
            return secrets_data
        
        # Parse the list output
        lines = list_result.strip().split('\n')
        keys_started = False
        keys = []
        
        for line in lines:
            if line.strip() == "Keys":
                keys_started = True
                continue
            elif keys_started and line.strip() == "----":
                continue
            elif keys_started and line.strip():
                keys.append(line.strip())
        
        print(f"Found keys at {path}: {keys}")
        
        # Process each key
        for key in keys:
            current_path = f"{path}/{key}" if path else key
            
            # Check if it's a directory (ends with /)
            if key.endswith('/'):
                # Recursively get secrets from subdirectory
                sub_secrets = get_vault_secrets(current_path.rstrip('/'))
                if sub_secrets:
                    secrets_data[key.rstrip('/')] = sub_secrets
            else:
                # Get the secret data
                get_result = run_vault_command(f"kv get secret/{current_path}")
                if get_result and ("===== Data =====" in get_result or "========== Data ==========" in get_result or "======= Data =======" in get_result or "== Data ==" in get_result):
                    # Parse the secret data
                    secret_data = parse_vault_secret(get_result)
                    if secret_data:
                        secrets_data[key] = secret_data
                        print(f"  Retrieved secret: {current_path}")
                else:
                    print(f"  No data found for: {current_path}")
                    print(f"    Output: {get_result[:200]}...")
    
    except Exception as e:
        print(f"Error getting secrets from {path}: {e}")
    
    return secrets_data

def parse_vault_secret(vault_output: str) -> Dict[str, str]:
    """Parse Vault secret output into key-value pairs."""
    secret_data = {}
    
    try:
        lines = vault_output.strip().split('\n')
        in_data_section = False
        header_passed = False
        
        for line in lines:
            line = line.strip()
            if (line == "===== Data =====" or 
                line == "========== Data ==========" or 
                line == "======= Data =======" or
                line == "== Data =="):
                in_data_section = True
                continue
            elif line == "======= Metadata ======":
                break
            elif in_data_section and line:
                if "Key" in line and "Value" in line:
                    header_passed = True
                    continue
                elif "---" in line and "----" in line:
                    continue  # Skip separator line
                elif header_passed and line and not line.startswith("---"):
                    # Parse key-value pairs - look for tab or multiple spaces
                    if "\t" in line:
                        # Split on tab
                        parts = line.split("\t", 1)
                        if len(parts) == 2:
                            key, value = parts
                            secret_data[key.strip()] = value.strip()
                    elif "    " in line:
                        # Split on 4 spaces (common in Vault output)
                        parts = line.split("    ", 1)
                        if len(parts) == 2:
                            key, value = parts
                            secret_data[key.strip()] = value.strip()
                    elif "   " in line:
                        # Split on 3 spaces
                        parts = line.split("   ", 1)
                        if len(parts) == 2:
                            key, value = parts
                            secret_data[key.strip()] = value.strip()
                    elif "  " in line:
                        # Split on 2 spaces
                        parts = line.split("  ", 1)
                        if len(parts) == 2:
                            key, value = parts
                            secret_data[key.strip()] = value.strip()
        
        print(f"    Parsed {len(secret_data)} fields: {list(secret_data.keys())}")
    
    except Exception as e:
        print(f"Error parsing Vault secret: {e}")
    
    return secret_data

def encrypt_sensitive_data(data: Any, crypto: VaultBackupCrypto) -> Any:
    """Recursively encrypt sensitive fields in the data."""
    if isinstance(data, dict):
        encrypted_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                encrypted_data[key] = encrypt_sensitive_data(value, crypto)
            elif isinstance(value, str) and key.lower() in SENSITIVE_FIELDS:
                encrypted_data[key] = crypto.encrypt_field(value)
            else:
                encrypted_data[key] = value
        return encrypted_data
    elif isinstance(data, list):
        return [encrypt_sensitive_data(item, crypto) for item in data]
    else:
        return data

def create_backup_directory() -> bool:
    """Create backup directory if it doesn't exist."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating backup directory: {e}")
        return False

def get_backup_filename() -> str:
    """Generate backup filename with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"vault_backup_{timestamp}.json.gz"

def create_backup_metadata(backup_file: Path, secrets_count: int) -> Dict[str, Any]:
    """Create backup metadata."""
    return {
        "backup_info": {
            "created_at": datetime.now().isoformat(),
            "backup_file": backup_file.name,
            "secrets_count": secrets_count,
            "encrypted_fields": list(SENSITIVE_FIELDS),
            "encryption": "AES-256-GCM with PBKDF2",
            "version": "1.0"
        },
        "vault_info": {
            "address": "http://127.0.0.1:8200",
            "engine": "kv-v2",
            "mount_point": "secret"
        }
    }

def main():
    """Main backup function."""
    print("🔐 Secure Vault Backup")
    print("=" * 40)
    
    # Check if Vault container is running
    try:
        result = subprocess.run(
            "docker ps --filter name=volexswarm-vault --format '{{.Names}}'",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if "volexswarm-vault" not in result.stdout:
            print("Error: Vault container is not running!")
            print("Please start the infrastructure first:")
            print("  docker-compose up -d vault")
            sys.exit(1)
    except Exception as e:
        print(f"Error checking Vault container: {e}")
        sys.exit(1)
    
    # Get master key for encryption
    master_key = input("Enter master key for encryption: ").strip()
    if not master_key:
        print("Error: Master key is required for encryption")
        sys.exit(1)
    
    print(f"Using master key: {master_key[:4]}...{master_key[-4:] if len(master_key) > 8 else '****'}")
    
    # Initialize crypto
    crypto = VaultBackupCrypto(master_key)
    
    # Create backup directory
    if not create_backup_directory():
        sys.exit(1)
    
    print("📥 Fetching secrets from Vault...")
    
    # Get all secrets
    secrets_data = get_vault_secrets()
    
    if not secrets_data:
        print("❌ No secrets found in Vault")
        sys.exit(1)
    
    print(f"✅ Found {len(secrets_data)} top-level secret paths")
    
    # Count total secrets
    def count_secrets(data: Any) -> int:
        if isinstance(data, dict):
            return sum(count_secrets(v) for v in data.values())
        else:
            return 1
    
    total_secrets = count_secrets(secrets_data)
    print(f"📊 Total secrets: {total_secrets}")
    
    # Encrypt sensitive data
    print("🔒 Encrypting sensitive data...")
    encrypted_data = encrypt_sensitive_data(secrets_data, crypto)
    
    # Create backup data
    backup_data = {
        "metadata": create_backup_metadata(Path(""), total_secrets),
        "secrets": encrypted_data
    }
    
    # Generate backup filename
    backup_filename = get_backup_filename()
    backup_file = BACKUP_DIR / backup_filename
    
    # Compress and save backup
    print(f"💾 Saving encrypted backup to {backup_file}...")
    try:
        with gzip.open(backup_file, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        # Get file size
        file_size = backup_file.stat().st_size
        print(f"✅ Backup created successfully!")
        print(f"   File: {backup_file}")
        print(f"   Size: {file_size / 1024:.1f} KB")
        print(f"   Secrets: {total_secrets}")
        print(f"   Encrypted fields: {len(SENSITIVE_FIELDS)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 