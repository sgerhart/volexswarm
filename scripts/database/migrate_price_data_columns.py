#!/usr/bin/env python3
"""
Migration script to rename price_data columns to match the updated model.
This script safely renames columns without dropping the database.
"""

import subprocess
import sys
import os

def execute_sql(sql: str) -> bool:
    """Execute SQL command on the database."""
    try:
        cmd = [
            "docker", "exec", "volexstorm-db", "psql",
            "-U", "volex",
            "-d", "volextrades",
            "-c", sql
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ SQL executed successfully: {sql[:50]}...")
            return True
        else:
            print(f"❌ SQL execution failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ SQL execution error: {e}")
        return False

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    sql = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = '{table_name}' 
        AND column_name = '{column_name}'
    );
    """
    
    cmd = [
        "docker", "exec", "volexstorm-db", "psql",
        "-U", "volex",
        "-d", "volextrades",
        "-t", "-c", sql
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip() == "t"

def main():
    """Migrate price_data columns."""
    print("🔄 Migrating price_data columns")
    print("=" * 40)
    
    # Check current column names
    print("🔍 Checking current column names...")
    
    old_columns = ['open_price', 'high_price', 'low_price', 'close_price']
    new_columns = ['open', 'high', 'low', 'close']
    
    # Check which columns exist
    existing_old = []
    existing_new = []
    
    for col in old_columns:
        if check_column_exists('price_data', col):
            existing_old.append(col)
            print(f"✅ Found old column: {col}")
    
    for col in new_columns:
        if check_column_exists('price_data', col):
            existing_new.append(col)
            print(f"✅ Found new column: {col}")
    
    # If new columns already exist, we're done
    if len(existing_new) == 4:
        print("✅ All new columns already exist. Migration not needed.")
        return True
    
    # If no old columns exist, we need to create new ones
    if len(existing_old) == 0:
        print("❌ No old columns found. Cannot migrate.")
        return False
    
    # Perform migration
    print("🔄 Starting column migration...")
    
    # Rename columns one by one
    for old_col, new_col in zip(old_columns, new_columns):
        if old_col in existing_old and new_col not in existing_new:
            print(f"🔄 Renaming {old_col} to {new_col}...")
            sql = f"ALTER TABLE price_data RENAME COLUMN {old_col} TO {new_col};"
            if not execute_sql(sql):
                print(f"❌ Failed to rename {old_col} to {new_col}")
                return False
    
    print("✅ Column migration completed successfully!")
    
    # Verify the migration
    print("🔍 Verifying migration...")
    for col in new_columns:
        if check_column_exists('price_data', col):
            print(f"✅ Verified column: {col}")
        else:
            print(f"❌ Missing column: {col}")
            return False
    
    print("🎉 Migration completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 