#!/usr/bin/env python3
"""
Database backup script for VolexSwarm TimescaleDB.
Creates compressed backups of the entire database with metadata.
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

# Backup configuration
BACKUP_DIR = Path("backup/database")
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
BACKUP_FILE = BACKUP_DIR / f"volexswarm_db_backup_{TIMESTAMP}.sql"
COMPRESSED_FILE = BACKUP_DIR / f"volexswarm_db_backup_{TIMESTAMP}.sql.gz"
METADATA_FILE = BACKUP_DIR / f"volexswarm_db_backup_{TIMESTAMP}_metadata.json"

def get_database_info() -> Dict[str, Any]:
    """Get database information and statistics."""
    try:
        # Connect to database and get info
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", DB_CONFIG["database"],
            "-c", """
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as size,
                    current_database() as database_name,
                    version() as postgres_version,
                    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as table_count
            """
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the output
        lines = result.stdout.strip().split('\n')
        if len(lines) >= 4:
            size_line = lines[2].split('|')
            if len(size_line) >= 2:
                db_size = size_line[1].strip()
                table_count = size_line[3].strip() if len(size_line) > 3 else "Unknown"
            else:
                db_size = "Unknown"
                table_count = "Unknown"
        else:
            db_size = "Unknown"
            table_count = "Unknown"
        
        return {
            "database_name": DB_CONFIG["database"],
            "database_size": db_size,
            "table_count": table_count,
            "postgres_version": "PostgreSQL 14 (TimescaleDB)",
            "backup_timestamp": datetime.now().isoformat(),
            "backup_type": "full_database"
        }
        
    except Exception as e:
        print(f"Warning: Could not get database info: {e}")
        return {
            "database_name": DB_CONFIG["database"],
            "database_size": "Unknown",
            "table_count": "Unknown",
            "postgres_version": "PostgreSQL 14 (TimescaleDB)",
            "backup_timestamp": datetime.now().isoformat(),
            "backup_type": "full_database"
        }

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

def create_backup_directory() -> bool:
    """Create backup directory if it doesn't exist."""
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        print(f"✅ Backup directory ready: {BACKUP_DIR}")
        return True
    except Exception as e:
        print(f"❌ Failed to create backup directory: {e}")
        return False

def backup_database() -> bool:
    """Create a full database backup."""
    try:
        print("🔄 Creating database backup...")
        
        # Create backup using pg_dump
        cmd = [
            "docker", "exec", "volexstorm-db", "pg_dump",
            "-U", DB_CONFIG["user"],
            "-d", DB_CONFIG["database"],
            "--verbose",
            "--clean",
            "--if-exists",
            "--create",
            "--no-owner",
            "--no-privileges"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        with open(BACKUP_FILE, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database backup created: {BACKUP_FILE}")
            return True
        else:
            print(f"❌ Database backup failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Database backup error: {e}")
        return False

def compress_backup() -> bool:
    """Compress the backup file."""
    try:
        print("🗜️  Compressing backup...")
        
        with open(BACKUP_FILE, 'rb') as f_in:
            with gzip.open(COMPRESSED_FILE, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Get file sizes
        original_size = BACKUP_FILE.stat().st_size
        compressed_size = COMPRESSED_FILE.stat().st_size
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        print(f"✅ Backup compressed: {COMPRESSED_FILE}")
        print(f"   Original size: {original_size / 1024 / 1024:.2f} MB")
        print(f"   Compressed size: {compressed_size / 1024 / 1024:.2f} MB")
        print(f"   Compression ratio: {compression_ratio:.1f}%")
        
        # Remove uncompressed file
        BACKUP_FILE.unlink()
        print(f"🗑️  Removed uncompressed file: {BACKUP_FILE}")
        
        return True
        
    except Exception as e:
        print(f"❌ Compression error: {e}")
        return False

def create_metadata(backup_success: bool) -> bool:
    """Create backup metadata file."""
    try:
        metadata = get_database_info()
        metadata.update({
            "backup_success": backup_success,
            "backup_file": str(COMPRESSED_FILE) if backup_success else None,
            "backup_size_mb": COMPRESSED_FILE.stat().st_size / 1024 / 1024 if backup_success and COMPRESSED_FILE.exists() else 0,
            "backup_script_version": "1.0.0"
        })
        
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Metadata created: {METADATA_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Metadata creation error: {e}")
        return False

def cleanup_old_backups(keep_days: int = 30) -> None:
    """Clean up old backup files."""
    try:
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        for file_path in BACKUP_DIR.glob("volexswarm_db_backup_*"):
            if file_path.stat().st_mtime < cutoff_date:
                file_path.unlink()
                print(f"🗑️  Cleaned up old backup: {file_path.name}")
                
    except Exception as e:
        print(f"Warning: Could not cleanup old backups: {e}")

def list_backups() -> None:
    """List available backup files."""
    try:
        backup_files = list(BACKUP_DIR.glob("volexswarm_db_backup_*.sql.gz"))
        
        if not backup_files:
            print("No database backups found.")
            return
        
        print(f"\n📋 Available database backups ({len(backup_files)}):")
        print("-" * 80)
        
        for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            stat = backup_file.stat()
            size_mb = stat.st_size / 1024 / 1024
            date_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            # Try to find corresponding metadata file
            metadata_file = backup_file.with_suffix('.sql_metadata.json')
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    db_size = metadata.get('database_size', 'Unknown')
                except:
                    db_size = 'Unknown'
            else:
                db_size = 'Unknown'
            
            print(f"📁 {backup_file.name}")
            print(f"   Size: {size_mb:.2f} MB | Date: {date_str} | DB Size: {db_size}")
            print()
            
    except Exception as e:
        print(f"Error listing backups: {e}")

def main():
    """Main backup function."""
    print("🗄️  VolexSwarm Database Backup")
    print("=" * 50)
    
    # Check if Docker container is running
    if not check_docker_container():
        print("❌ Database container 'volexstorm-db' is not running!")
        print("   Please start the database container first:")
        print("   docker-compose up -d db")
        return False
    
    # Create backup directory
    if not create_backup_directory():
        return False
    
    # Get database info
    print("📊 Database Information:")
    db_info = get_database_info()
    for key, value in db_info.items():
        if key != "backup_timestamp":
            print(f"   {key}: {value}")
    print()
    
    # Create backup
    backup_success = backup_database()
    
    if backup_success:
        # Compress backup
        if compress_backup():
            # Create metadata
            create_metadata(True)
            
            print("\n🎉 Database backup completed successfully!")
            print(f"📁 Backup file: {COMPRESSED_FILE}")
            print(f"📄 Metadata: {METADATA_FILE}")
            
            # Cleanup old backups
            cleanup_old_backups()
            
            return True
        else:
            create_metadata(False)
            return False
    else:
        create_metadata(False)
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backup VolexSwarm database")
    parser.add_argument("--list", action="store_true", help="List existing backups")
    parser.add_argument("--cleanup", type=int, metavar="DAYS", help="Clean up backups older than DAYS")
    
    args = parser.parse_args()
    
    if args.list:
        list_backups()
    elif args.cleanup:
        cleanup_old_backups(args.cleanup)
    else:
        success = main()
        sys.exit(0 if success else 1) 