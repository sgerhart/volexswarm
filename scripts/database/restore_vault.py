#!/usr/bin/env python3
"""
Secure Vault restore script for VolexSwarm.
Restores Vault secrets from encrypted backup files.
"""

import os
import sys
import subprocess
import json
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
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

def list_backups() -> List[Path]:
    """List available backup files."""
    if not BACKUP_DIR.exists():
        return []
    
    backup_files = []
    for file in BACKUP_DIR.glob("vault_backup_*.json.gz"):
        backup_files.append(file)
    
    return sorted(backup_files, reverse=True)

def get_backup_info(backup_file: Path) -> Optional[Dict[str, Any]]:
    """Get information about a backup file."""
    try:
        with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
            return backup_data.get('metadata', {})
    except Exception as e:
        print(f"Error reading backup file {backup_file}: {e}")
        return None

def decrypt_sensitive_data(data: Any, crypto: VaultBackupCrypto) -> Any:
    """Recursively decrypt sensitive fields in the data."""
    if isinstance(data, dict):
        decrypted_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                decrypted_data[key] = decrypt_sensitive_data(value, crypto)
            elif isinstance(value, str) and key.lower() in SENSITIVE_FIELDS:
                # Check if this looks like encrypted data (base64)
                try:
                    base64.b64decode(value.encode('utf-8'))
                    decrypted_data[key] = crypto.decrypt_field(value)
                except:
                    # Not encrypted, keep as-is
                    decrypted_data[key] = value
            else:
                decrypted_data[key] = value
        return decrypted_data
    elif isinstance(data, list):
        return [decrypt_sensitive_data(item, crypto) for item in data]
    else:
        return data

def store_secret(path: str, data: Dict[str, Any]) -> bool:
    """Store a secret using Vault CLI with proper JSON formatting."""
    try:
        # Convert data to key=value pairs for Vault CLI
        kv_pairs = []
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                # Convert lists and dicts to JSON strings
                kv_pairs.append(f'{key}=\'{json.dumps(value)}\'')
            else:
                kv_pairs.append(f'{key}={value}')
        
        # Join all key-value pairs
        kv_string = ' '.join(kv_pairs)
        
        # Store the secret
        command = f"kv put secret/{path} {kv_string}"
        result = run_vault_command(command)
        
        return "Success" in result or "created_time" in result
    except Exception as e:
        print(f"Error storing secret {path}: {e}")
        return False

def restore_secrets_recursive(secrets_data: Dict[str, Any], base_path: str = "") -> int:
    """Recursively restore secrets to Vault."""
    restored_count = 0
    
    for key, value in secrets_data.items():
        current_path = f"{base_path}/{key}" if base_path else key
        
        if isinstance(value, dict):
            # Check if this looks like a secret (has string values)
            has_string_values = any(isinstance(v, str) for v in value.values())
            
            if has_string_values:
                # This is a secret, store it
                if store_secret(current_path, value):
                    print(f"  ✅ Restored: {current_path}")
                    restored_count += 1
                else:
                    print(f"  ❌ Failed to restore: {current_path}")
            else:
                # This is a directory, recurse
                restored_count += restore_secrets_recursive(value, current_path)
    
    return restored_count

def interactive_backup_selection() -> Optional[Path]:
    """Let user select a backup file interactively."""
    backup_files = list_backups()
    
    if not backup_files:
        print("❌ No backup files found in backup/vault/")
        return None
    
    print("📋 Available Vault backups:")
    print("-" * 60)
    
    for i, backup_file in enumerate(backup_files, 1):
        backup_info = get_backup_info(backup_file)
        if backup_info:
            created_at = backup_info.get('backup_info', {}).get('created_at', 'Unknown')
            secrets_count = backup_info.get('backup_info', {}).get('secrets_count', 'Unknown')
            file_size = backup_file.stat().st_size / 1024  # KB
            
            print(f"{i:2d}. {backup_file.name}")
            print(f"    Created: {created_at}")
            print(f"    Secrets: {secrets_count}")
            print(f"    Size: {file_size:.1f} KB")
        else:
            print(f"{i:2d}. {backup_file.name} (info unavailable)")
        print()
    
    while True:
        try:
            choice = input(f"Select backup to restore (1-{len(backup_files)}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(backup_files):
                return backup_files[choice_num - 1]
            else:
                print(f"Please enter a number between 1 and {len(backup_files)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\nRestore cancelled")
            return None

def main():
    """Main restore function."""
    print("🔐 Secure Vault Restore")
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
    
    # Get backup file
    if len(sys.argv) > 1:
        backup_file = Path(sys.argv[1])
        if not backup_file.exists():
            print(f"Error: Backup file {backup_file} not found")
            sys.exit(1)
    else:
        backup_file = interactive_backup_selection()
        if not backup_file:
            sys.exit(1)
    
    # Get backup info
    backup_info = get_backup_info(backup_file)
    if not backup_info:
        print(f"Error: Could not read backup file {backup_file}")
        sys.exit(1)
    
    print(f"📁 Selected backup: {backup_file.name}")
    print(f"📅 Created: {backup_info.get('backup_info', {}).get('created_at', 'Unknown')}")
    print(f"📊 Secrets: {backup_info.get('backup_info', {}).get('secrets_count', 'Unknown')}")
    
    # Get master key for decryption
    master_key = input("Enter master key for decryption: ").strip()
    if not master_key:
        print("Error: Master key is required for decryption")
        sys.exit(1)
    
    # Initialize crypto
    crypto = VaultBackupCrypto(master_key)
    
    # Load and decrypt backup
    print("📥 Loading backup file...")
    try:
        with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        secrets_data = backup_data.get('secrets', {})
        if not secrets_data:
            print("❌ No secrets found in backup file")
            sys.exit(1)
        
        print("🔓 Decrypting sensitive data...")
        decrypted_data = decrypt_sensitive_data(secrets_data, crypto)
        
        # Confirm restore
        print(f"\n⚠️  This will overwrite existing secrets in Vault!")
        confirm = input("Type 'YES' to confirm restore: ").strip()
        if confirm != "YES":
            print("Restore cancelled")
            sys.exit(0)
        
        # Restore secrets
        print("🔄 Restoring secrets to Vault...")
        restored_count = restore_secrets_recursive(decrypted_data)
        
        print(f"\n✅ Restore completed successfully!")
        print(f"   Restored secrets: {restored_count}")
        print(f"   Backup file: {backup_file.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during restore: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 