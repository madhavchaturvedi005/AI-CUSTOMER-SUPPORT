#!/usr/bin/env python3
"""
Script to retrieve call transcripts from the database.

Usage:
    python retrieve_transcript.py <call_id>
    python retrieve_transcript.py --list  # List all calls
    python retrieve_transcript.py --recent  # Show recent calls
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv
from database import DatabaseService

# Load environment variables
load_dotenv()


async def list_calls(db: DatabaseService, limit: int = 20):
    """List recent calls with basic info."""
    async with db.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, call_sid, caller_phone, caller_name, 
                   started_at, status, intent, duration_seconds
            FROM calls
            ORDER BY started_at DESC
            LIMIT $1
        """, limit)
        
        if not rows:
            print("No calls found in database.")
            return
        
        print(f"\n📞 Recent Calls (showing {len(rows)}):\n")
        print(f"{'ID':<38} {'Call SID':<20} {'Phone':<15} {'Status':<12} {'Intent':<20} {'Started':<20}")
        print("-" * 140)
        
        for row in rows:
            call_id = str(row['id'])
            call_sid = row['call_sid'] or 'N/A'
            phone = row['caller_phone'] or 'N/A'
            status = row['status']
            intent = row['intent'] or 'N/A'
            started = row['started_at'].strftime('%Y-%m-%d %H:%M:%S') if row['started_at'] else 'N/A'
            
            print(f"{call_id:<38} {call_sid:<20} {phone:<15} {status:<12} {intent:<20} {started:<20}")


async def get_transcript(db: DatabaseService, call_id: str):
    """Retrieve and display transcript for a specific call."""
    async with db.pool.acquire() as conn:
        # Get call details
        call_row = await conn.fetchrow("""
            SELECT id, call_sid, caller_phone, caller_name, 
                   started_at, ended_at, duration_seconds, 
                   status, intent, language, metadata
            FROM calls
            WHERE id = $1::uuid OR call_sid = $1
        """, call_id)
        
        if not call_row:
            print(f"❌ Call not found: {call_id}")
            return
        
        # Get transcript entries
        transcript_rows = await conn.fetch("""
            SELECT speaker, text, timestamp_ms, language, confidence
            FROM transcripts
            WHERE call_id = $1::uuid
            ORDER BY timestamp_ms ASC
        """, str(call_row['id']))
        
        # Display call details
        print("\n" + "=" * 80)
        print("📞 CALL DETAILS")
        print("=" * 80)
        print(f"Call ID:       {call_row['id']}")
        print(f"Call SID:      {call_row['call_sid']}")
        print(f"Caller:        {call_row['caller_phone']}")
        if call_row['caller_name']:
            print(f"Name:          {call_row['caller_name']}")
        print(f"Status:        {call_row['status']}")
        print(f"Intent:        {call_row['intent'] or 'N/A'}")
        print(f"Language:      {call_row['language'] or 'N/A'}")
        print(f"Started:       {call_row['started_at']}")
        if call_row['ended_at']:
            print(f"Ended:         {call_row['ended_at']}")
        if call_row['duration_seconds']:
            print(f"Duration:      {call_row['duration_seconds']} seconds")
        
        # Display transcript
        print("\n" + "=" * 80)
        print("💬 CONVERSATION TRANSCRIPT")
        print("=" * 80)
        
        if not transcript_rows:
            print("No transcript entries found.")
        else:
            for row in transcript_rows:
                speaker = row['speaker']
                text = row['text']
                timestamp_ms = row['timestamp_ms']
                
                # Format speaker
                speaker_label = "🗣️  Caller" if speaker == "caller" else "🤖 Assistant"
                
                # Format timestamp
                seconds = timestamp_ms / 1000
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                time_str = f"[{minutes:02d}:{secs:02d}]"
                
                print(f"\n{time_str} {speaker_label}:")
                print(f"  {text}")
        
        print("\n" + "=" * 80)
        print(f"Total transcript entries: {len(transcript_rows)}")
        print("=" * 80 + "\n")


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python retrieve_transcript.py <call_id>")
        print("  python retrieve_transcript.py --list")
        print("  python retrieve_transcript.py --recent")
        sys.exit(1)
    
    # Load database config from environment
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 5432))
    db_name = os.getenv('DB_NAME', 'voice_assistant')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    # Initialize database with minimal pool size
    db = DatabaseService(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
        min_pool_size=1,
        max_pool_size=2
    )
    
    try:
        await db.connect()
        print("✅ Connected to database")
        
        arg = sys.argv[1]
        
        if arg in ["--list", "--recent"]:
            await list_calls(db)
        else:
            await get_transcript(db, arg)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
