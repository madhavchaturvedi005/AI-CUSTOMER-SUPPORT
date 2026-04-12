#!/usr/bin/env python3
"""Check database tables and schema."""

import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()


async def main():
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 5432))
    db_name = os.getenv('DB_NAME', 'voice_assistant')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password
    )
    
    try:
        # List all tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print("\n📊 Database Tables:")
        print("=" * 50)
        for table in tables:
            print(f"  • {table['table_name']}")
        
        # Check transcripts table structure
        print("\n📋 Transcripts Table Structure:")
        print("=" * 50)
        columns = await conn.fetch("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'transcripts'
            ORDER BY ordinal_position
        """)
        
        if columns:
            for col in columns:
                print(f"  • {col['column_name']:<20} {col['data_type']:<20} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
        else:
            print("  Table 'transcripts' not found")
        
        # Count records in transcripts
        count = await conn.fetchval("SELECT COUNT(*) FROM transcripts")
        print(f"\n📈 Total transcript records: {count}")
        
        # Show sample if any exist
        if count > 0:
            sample = await conn.fetch("SELECT * FROM transcripts LIMIT 3")
            print("\n📝 Sample transcript records:")
            for i, rec in enumerate(sample, 1):
                print(f"\n  Record {i}:")
                for key, value in dict(rec).items():
                    print(f"    {key}: {value}")
    
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
