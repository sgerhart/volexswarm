#!/usr/bin/env python3
"""
Database restore script for VolexSwarm TimescaleDB.
Restores database from compressed backup files.
"""

import os
import sys
import subprocess
import json
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "volextrades",
    "user": "volex",
    "password": "volex_pass"
}

# Backup directory
BACKUP_DIR = Path("backup/database")

def check_docker_container() -> bool:
    """Check if the database container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=volexstorm-db", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True
        )
        return "volexstorm-db" in result.stdout.strip()
    except Exception as e:
        print(f"Error checking Docker container: {e}")
        return False

def list_backups() -> list:
    """List available backup files."""
    try:
        backup_files = list(BACKUP_DIR.glob("volexswarm_db_backup_*.sql.gz"))
        return sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)
    except Exception as e:
        print(f"Error listing backups: {e}")
        return []

def get_backup_info(backup_file: Path) -> Dict[str, Any]:
    """Get information about a backup file."""
    try:
        # Try to find corresponding metadata file
        metadata_file = backup_file.with_suffix('.sql_metadata.json')
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            return metadata
        else:
            # Basic info from file stats
            stat = backup_file.stat()
            return {
                "backup_file": str(backup_file),
                "backup_timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "backup_size_mb": stat.st_size / 1024 / 1024,
                "database_name": "Unknown",
                "database_size": "Unknown",
                "table_count": "Unknown"
            }
    except Exception as e:
        print(f"Error getting backup info: {e}")
        return {}

def decompress_backup(backup_file: Path) -> Optional[Path]:
    """Decompress a backup file."""
    try:
        decompressed_file = backup_file.with_suffix('')  # Remove .gz
        print(f"🗜️  Decompressing {backup_file.name}...")
        
        with gzip.open(backup_file, 'rb') as f_in:
            with open(decompressed_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        print(f"✅ Decompressed to: {decompressed_file}")
        return decompressed_file
        
    except Exception as e:
        print(f"❌ Decompression error: {e}")
        return None

def drop_database() -> bool:
    """Drop the existing database."""
    try:
        print("🗑️  Dropping existing database...")
        
        # Connect to postgres database to drop volextrades
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", "postgres",
            "-c", f"DROP DATABASE IF EXISTS {DB_CONFIG['database']};"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database dropped successfully")
            return True
        else:
            print(f"❌ Failed to drop database: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error dropping database: {e}")
        return False

def create_database() -> bool:
    """Create a new database."""
    try:
        print("🏗️  Creating new database...")
        
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", "postgres",
            "-c", f"CREATE DATABASE {DB_CONFIG['database']};"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database created successfully")
            return True
        else:
            print(f"❌ Failed to create database: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False

def restore_database(backup_file: Path) -> bool:
    """Restore database from backup file."""
    try:
        print("🔄 Restoring database...")
        
        # Decompress backup
        decompressed_file = decompress_backup(backup_file)
        if not decompressed_file:
            return False
        
        try:
            # Restore using psql
            cmd = [
                "docker", "exec", "-i", "volexstorm-db", "psql",
                "-U", DB_CONFIG["user"],
                "-d", DB_CONFIG["database"]
            ]
            
            print(f"Running: {' '.join(cmd)}")
            
            with open(decompressed_file, 'r') as f:
                result = subprocess.run(cmd, stdin=f, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Database restored successfully")
                return True
            else:
                print(f"❌ Database restore failed: {result.stderr}")
                return False
                
        finally:
            # Clean up decompressed file
            if decompressed_file.exists():
                decompressed_file.unlink()
                print(f"🗑️  Cleaned up decompressed file: {decompressed_file}")
        
    except Exception as e:
        print(f"❌ Database restore error: {e}")
        return False

def verify_restore() -> bool:
    """Verify the database restore was successful."""
    try:
        print("🔍 Verifying restore...")
        
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", DB_CONFIG["database"],
            "-c", """
                SELECT 
                    table_name,
                    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as total_tables
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database verification successful")
            print("📊 Tables found:")
            lines = result.stdout.strip().split('\n')
            for line in lines[2:-1]:  # Skip header and footer
                if '|' in line:
                    table_name = line.split('|')[0].strip()
                    if table_name:
                        print(f"   - {table_name}")
            return True
        else:
            print(f"❌ Database verification failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def interactive_backup_selection() -> Optional[Path]:
    """Interactive backup selection."""
    backup_files = list_backups()
    
    if not backup_files:
        print("❌ No backup files found!")
        return None
    
    print(f"\n📋 Available backups ({len(backup_files)}):")
    print("-" * 80)
    
    for i, backup_file in enumerate(backup_files, 1):
        info = get_backup_info(backup_file)
        date_str = datetime.fromtimestamp(backup_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        size_mb = backup_file.stat().st_size / 1024 / 1024
        
        print(f"{i:2d}. {backup_file.name}")
        print(f"    Date: {date_str} | Size: {size_mb:.2f} MB")
        if info.get('database_size'):
            print(f"    DB Size: {info['database_size']} | Tables: {info.get('table_count', 'Unknown')}")
        print()
    
    while True:
        try:
            choice = input(f"Select backup to restore (1-{len(backup_files)}): ").strip()
            if not choice:
                print("❌ No selection made")
                return None
            
            index = int(choice) - 1
            if 0 <= index < len(backup_files):
                return backup_files[index]
            else:
                print(f"❌ Invalid selection. Please choose 1-{len(backup_files)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            print("\n❌ Restore cancelled")
            return None

def main():
    """Main restore function."""
    print("🗄️  VolexSwarm Database Restore")
    print("=" * 50)
    
    # Check if Docker container is running
    if not check_docker_container():
        print("❌ Database container 'volexstorm-db' is not running!")
        print("   Please start the database container first:")
        print("   docker-compose up -d db")
        return False
    
    # Get backup file
    if len(sys.argv) > 1:
        backup_file = Path(sys.argv[1])
        if not backup_file.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False
    else:
        backup_file = interactive_backup_selection()
        if not backup_file:
            return False
    
    # Show backup info
    print(f"\n📁 Selected backup: {backup_file.name}")
    info = get_backup_info(backup_file)
    for key, value in info.items():
        if key not in ['backup_file', 'backup_timestamp']:
            print(f"   {key}: {value}")
    
    # Confirm restore
    print(f"\n⚠️  WARNING: This will completely replace the current database!")
    print(f"   Current database: {DB_CONFIG['database']}")
    print(f"   Backup file: {backup_file.name}")
    
    confirm = input("\nAre you sure you want to proceed? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ Restore cancelled")
        return False
    
    # Drop existing database
    if not drop_database():
        return False
    
    # Create new database
    if not create_database():
        return False
    
    # Restore from backup
    if not restore_database(backup_file):
        return False
    
    # Verify restore
    if not verify_restore():
        return False
    
    print("\n🎉 Database restore completed successfully!")
    print("   The database has been restored from the backup.")
    print("   You may need to restart your agents to pick up the restored data.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 