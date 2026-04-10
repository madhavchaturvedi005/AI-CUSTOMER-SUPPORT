#!/usr/bin/env python3
"""
Database migration runner for AI Voice Automation system.

This script runs SQL migration files against a PostgreSQL database.
It supports both local development and production environments.

Usage:
    python migrations/run_migration.py [migration_file]
    
Examples:
    # Run initial schema migration
    python migrations/run_migration.py 001_initial_schema.sql
    
    # Run with custom database URL
    DATABASE_URL=postgresql://user:pass@localhost/dbname python migrations/run_migration.py 001_initial_schema.sql
"""

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Error: psycopg2 is not installed.")
    print("Install it with: pip install psycopg2-binary")
    sys.exit(1)


def get_database_url() -> str:
    """Get database URL from environment variables."""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Try to construct from individual components
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'voice_automation')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        if db_password:
            database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:
            database_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
    
    return database_url


def run_migration(migration_file: str, database_url: str) -> bool:
    """
    Run a SQL migration file against the database.
    
    Args:
        migration_file: Path to the SQL migration file
        database_url: PostgreSQL connection URL
        
    Returns:
        True if migration succeeded, False otherwise
    """
    migration_path = Path(migration_file)
    
    if not migration_path.exists():
        print(f"Error: Migration file not found: {migration_file}")
        return False
    
    print(f"Reading migration file: {migration_file}")
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = False
        cursor = conn.cursor()
        
        print(f"Executing migration: {migration_path.name}")
        cursor.execute(migration_sql)
        
        print("Committing transaction...")
        conn.commit()
        
        print("✓ Migration completed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        
        print(f"\nCreated tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\n✗ Migration failed!")
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error!")
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()
        return False


def main():
    """Main entry point for migration runner."""
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <migration_file>")
        print("\nExample:")
        print("  python migrations/run_migration.py 001_initial_schema.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    
    # If relative path provided, resolve from migrations directory
    if not os.path.isabs(migration_file):
        migrations_dir = Path(__file__).parent
        migration_file = migrations_dir / migration_file
    
    database_url = get_database_url()
    
    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)
    print(f"Migration: {migration_file}")
    print(f"Database: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    print("=" * 60)
    print()
    
    success = run_migration(str(migration_file), database_url)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
