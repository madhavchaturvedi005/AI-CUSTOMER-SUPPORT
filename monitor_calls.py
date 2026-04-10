#!/usr/bin/env python3
"""
Real-time call monitoring script.
Watches for new calls and shows their status as they progress.
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'

async def get_recent_calls(pool, limit=5):
    """Get recent calls from database."""
    query = """
        SELECT 
            id, call_sid, caller_phone, caller_name,
            started_at, ended_at, duration_seconds,
            status, intent, language
        FROM calls
        ORDER BY started_at DESC
        LIMIT $1
    """
    
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, limit)
        return [dict(row) for row in rows]

async def get_call_stats(pool, call_id):
    """Get stats for a specific call."""
    async with pool.acquire() as conn:
        # Count transcripts
        transcript_count = await conn.fetchval(
            "SELECT COUNT(*) FROM transcripts WHERE call_id = $1",
            call_id
        )
        
        # Count appointments
        appointment_count = await conn.fetchval(
            "SELECT COUNT(*) FROM appointments WHERE call_id = $1",
            call_id
        )
        
        # Count leads
        lead_count = await conn.fetchval(
            "SELECT COUNT(*) FROM leads WHERE call_id = $1",
            call_id
        )
        
        return {
            'transcripts': transcript_count,
            'appointments': appointment_count,
            'leads': lead_count
        }

def format_duration(seconds):
    """Format duration in human-readable format."""
    if seconds is None:
        return "N/A"
    
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    return f"{minutes}m {remaining_seconds}s"

def format_status(status):
    """Format status with color."""
    if status == 'completed':
        return f"{GREEN}{status}{RESET}"
    elif status == 'initiated':
        return f"{YELLOW}{status}{RESET}"
    elif status == 'in_progress':
        return f"{CYAN}{status}{RESET}"
    elif status == 'failed':
        return f"{RED}{status}{RESET}"
    else:
        return status

def format_time_ago(dt):
    """Format time ago."""
    if dt is None:
        return "N/A"
    
    # Ensure timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.seconds < 60:
        return f"{diff.seconds}s ago"
    elif diff.seconds < 3600:
        return f"{diff.seconds // 60}m ago"
    elif diff.seconds < 86400:
        return f"{diff.seconds // 3600}h ago"
    else:
        return f"{diff.days}d ago"

async def monitor_calls():
    """Monitor calls in real-time."""
    # Connect to database
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'voice_automation'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}{'REAL-TIME CALL MONITOR':^80}{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    print(f"Connecting to database: {db_config['database']}@{db_config['host']}...")
    
    try:
        pool = await asyncpg.create_pool(**db_config)
        print(f"{GREEN}✅ Connected{RESET}\n")
        
        last_call_id = None
        
        while True:
            try:
                # Get recent calls
                calls = await get_recent_calls(pool, limit=5)
                
                # Clear screen (optional - comment out if you want history)
                # print("\033[2J\033[H")
                
                print(f"\n{CYAN}{'─'*80}{RESET}")
                print(f"{CYAN}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
                print(f"{CYAN}{'─'*80}{RESET}\n")
                
                if not calls:
                    print(f"{YELLOW}No calls found. Waiting for incoming calls...{RESET}")
                else:
                    # Check if there's a new call
                    if calls[0]['id'] != last_call_id:
                        last_call_id = calls[0]['id']
                        print(f"{GREEN}🔔 NEW CALL DETECTED!{RESET}\n")
                    
                    for i, call in enumerate(calls, 1):
                        call_id = str(call['id'])
                        stats = await get_call_stats(pool, call_id)
                        
                        print(f"{BLUE}Call #{i}{RESET}")
                        print(f"  SID: {call['call_sid']}")
                        print(f"  Caller: {call['caller_phone']}", end="")
                        if call['caller_name']:
                            print(f" ({call['caller_name']})")
                        else:
                            print()
                        
                        print(f"  Status: {format_status(call['status'])}")
                        print(f"  Started: {format_time_ago(call['started_at'])}")
                        
                        if call['ended_at']:
                            print(f"  Ended: {format_time_ago(call['ended_at'])}")
                        
                        print(f"  Duration: {format_duration(call['duration_seconds'])}")
                        
                        if call['intent']:
                            print(f"  Intent: {call['intent'].replace('_', ' ').title()}")
                        
                        if call['language']:
                            lang_names = {
                                'en': 'English', 'hi': 'Hindi', 'ta': 'Tamil',
                                'te': 'Telugu', 'bn': 'Bengali'
                            }
                            print(f"  Language: {lang_names.get(call['language'], call['language'])}")
                        
                        # Show stats
                        print(f"  Data: ", end="")
                        parts = []
                        if stats['transcripts'] > 0:
                            parts.append(f"{GREEN}{stats['transcripts']} transcripts{RESET}")
                        if stats['appointments'] > 0:
                            parts.append(f"{GREEN}{stats['appointments']} appointments{RESET}")
                        if stats['leads'] > 0:
                            parts.append(f"{GREEN}{stats['leads']} leads{RESET}")
                        
                        if parts:
                            print(", ".join(parts))
                        else:
                            print(f"{YELLOW}No data yet{RESET}")
                        
                        print()
                
                # Wait before next check
                await asyncio.sleep(3)
                
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
                await asyncio.sleep(5)
        
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Monitoring stopped{RESET}")
    except Exception as e:
        print(f"\n{RED}Failed to connect: {e}{RESET}")
        print(f"\nCheck your database configuration in .env file:")
        print(f"  DB_HOST={db_config['host']}")
        print(f"  DB_PORT={db_config['port']}")
        print(f"  DB_NAME={db_config['database']}")
        print(f"  DB_USER={db_config['user']}")
    finally:
        if 'pool' in locals():
            await pool.close()

if __name__ == "__main__":
    try:
        asyncio.run(monitor_calls())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Exiting...{RESET}")
