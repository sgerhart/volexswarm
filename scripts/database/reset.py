#!/usr/bin/env python3
"""
Automated database reset - drops and recreates the database without user confirmation.
"""

import subprocess
import sys

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "volextrades",
    "user": "volex",
    "password": "volex_pass"
}

def execute_sql(sql: str, database: str = None) -> bool:
    """Execute SQL command on the database."""
    try:
        db = database or DB_CONFIG["database"]
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", DB_CONFIG["user"],
            "-d", db,
            "-c", sql
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            print(f"SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"SQL execution error: {e}")
        return False

def main():
    """Automated database reset."""
    print("🗄️  Automated VolexSwarm Database Reset")
    print("=" * 50)
    
    # Drop the database (connect to postgres database first)
    print("🗑️  Dropping volextrades database...")
    drop_sql = "DROP DATABASE IF EXISTS volextrades;"
    
    if not execute_sql(drop_sql, "postgres"):
        print("❌ Failed to drop database")
        return False
    
    # Create new database
    print("🏗️  Creating new volextrades database...")
    create_sql = "CREATE DATABASE volextrades;"
    
    if not execute_sql(create_sql, "postgres"):
        print("❌ Failed to create database")
        return False
    
    # Create TimescaleDB extension
    print("🔧 Creating TimescaleDB extension...")
    extension_sql = "CREATE EXTENSION IF NOT EXISTS timescaledb;"
    
    if not execute_sql(extension_sql):
        print("❌ Failed to create TimescaleDB extension")
        return False
    
    print("✅ Database reset completed successfully!")
    print("   Database is now completely fresh.")
    print("   Run 'python scripts/database/setup_schema.py' to set up the schema.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 