#!/usr/bin/env python3
"""
Script to update all in-progress calls to completed status.
Run this to fix calls that are stuck in 'initiated' or 'in_progress' status.
"""

import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
import asyncpg

load_dotenv()

async def update_call_statuses():
    """Update all non-completed calls to completed status."""
    
    # Try DATABASE_URL first, then fall back to individual parameters
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Build connection string from individual parameters
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        db_sslmode = os.getenv('DB_SSLMODE', 'require')
        
        if not all([db_host, db_port, db_name, db_user, db_password]):
            print("❌ Database configuration not found in .env file")
            print("   Required: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
            print("   Or: DATABASE_URL")
            return
        
        database_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    
    try:
        # Connect to database
        print("🔌 Connecting to database...")
        conn = await asyncpg.connect(database_url)
        
        # Get all calls that are not completed
        print("� Finding calls to update...")
        calls = await conn.fetch("""
            SELECT id, call_sid, status, started_at, ended_at, duration_seconds
            FROM calls
            WHERE status IN ('initiated', 'in_progress')
            ORDER BY started_at DESC
        """)
        
        if not calls:
            print("✅ No calls need updating. All calls are already completed!")
            await conn.close()
            return
        
        print(f"📋 Found {len(calls)} calls to update:")
        print()
        
        updated_count = 0
        
        for call in calls:
            call_id = str(call['id'])
            call_sid = call['call_sid']
            started_at = call['started_at']
            
            # Calculate ended_at and duration
            # If call has no ended_at, assume it ended 3 minutes after start
            if call['ended_at']:
                ended_at = call['ended_at']
            else:
                # Assume 3 minute call
                from datetime import timedelta
                ended_at = started_at + timedelta(minutes=3)
            
            # Calculate duration
            if call['duration_seconds']:
                duration_seconds = call['duration_seconds']
            else:
                duration_seconds = int((ended_at - started_at).total_seconds())
            
            # Update call status
            await conn.execute("""
                UPDATE calls
                SET status = 'completed',
                    ended_at = $1,
                    duration_seconds = $2,
                    updated_at = NOW()
                WHERE id = $3
            """, ended_at, duration_seconds, call_id)
            
            updated_count += 1
            print(f"✅ Updated call {call_sid[:20]}... → completed ({duration_seconds}s)")
        
        print()
        print(f"🎉 Successfully updated {updated_count} calls to completed status!")
        
        await conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("📞 Call Status Updater")
    print("=" * 60)
    print()
    
    asyncio.run(update_call_statuses())
    
    print()
    print("=" * 60)
    print("✅ Done!")
    print("=" * 60)
