#!/usr/bin/env python3
"""Test Aiven PostgreSQL connection."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def test_connection():
    """Test connection to Aiven PostgreSQL."""
    print("\n" + "="*60)
    print("AIVEN POSTGRESQL CONNECTION TEST")
    print("="*60)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_sslmode = os.getenv("DB_SSLMODE")
    
    print(f"   DB_HOST: {db_host}")
    print(f"   DB_PORT: {db_port}")
    print(f"   DB_NAME: {db_name}")
    print(f"   DB_USER: {db_user}")
    print(f"   DB_PASSWORD: {'***' if db_password else 'Not set'}")
    print(f"   DB_SSLMODE: {db_sslmode}")
    
    if not all([db_host, db_port, db_name, db_user, db_password]):
        print("\n❌ ERROR: Missing required environment variables")
        print("\nPlease update your .env file with Aiven credentials:")
        print("  DB_HOST=your-aiven-host.aivencloud.com")
        print("  DB_PORT=12345")
        print("  DB_NAME=defaultdb")
        print("  DB_USER=avnadmin")
        print("  DB_PASSWORD=your-password")
        print("  DB_SSLMODE=require")
        return False
    
    # Test connection
    print("\n2. Testing connection to Aiven...")
    try:
        import asyncpg
        
        conn = await asyncpg.connect(
            host=db_host,
            port=int(db_port),
            database=db_name,
            user=db_user,
            password=db_password,
            ssl=db_sslmode
        )
        
        print("   ✅ Connection successful!")
        
        # Test query
        print("\n3. Testing database query...")
        version = await conn.fetchval("SELECT version()")
        print(f"   PostgreSQL version: {version.split(',')[0]}")
        
        # Check if tables exist
        print("\n4. Checking for tables...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            print(f"   Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("   ⚠️  No tables found")
            print("   Run migrations: python3 migrations/run_migration.py 001_initial_schema.sql")
        
        await conn.close()
        
        print("\n" + "="*60)
        print("✅ AIVEN CONNECTION TEST PASSED!")
        print("="*60)
        print("\nYour Aiven PostgreSQL database is ready to use!")
        
        if not tables:
            print("\nNext step: Run migrations to create tables")
            print("  python3 migrations/run_migration.py 001_initial_schema.sql")
        
        return True
        
    except asyncpg.InvalidPasswordError:
        print("   ❌ Authentication failed")
        print("\n   Check your DB_PASSWORD in .env file")
        return False
        
    except asyncpg.InvalidCatalogNameError:
        print("   ❌ Database does not exist")
        print(f"\n   Database '{db_name}' not found on Aiven")
        print("   Check DB_NAME in .env (usually 'defaultdb' for Aiven)")
        return False
        
    except asyncpg.CannotConnectNowError:
        print("   ❌ Cannot connect to database")
        print("\n   Possible issues:")
        print("   - Aiven service is not running")
        print("   - IP address not whitelisted")
        print("   - Firewall blocking connection")
        return False
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print("\n   Troubleshooting:")
        print("   1. Verify credentials in Aiven console")
        print("   2. Check if service is running")
        print("   3. Verify IP whitelisting (if enabled)")
        print("   4. Check DB_SSLMODE=require in .env")
        return False


async def main():
    """Main entry point."""
    success = await test_connection()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
