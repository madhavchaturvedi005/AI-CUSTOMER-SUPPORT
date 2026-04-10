"""Check the most recent call and its conversation history."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def check_recent_call():
    """Check the most recent call in the database."""
    
    print("🔍 Checking Most Recent Call\n")
    print("="*60)
    
    use_real_db = os.getenv("USE_REAL_DB", "false").lower() == "true"
    
    if not use_real_db:
        print("⚠️  Real database is NOT enabled!")
        return
    
    try:
        from database import initialize_database
        
        print("📡 Connecting to database...")
        db = await initialize_database()
        print("✅ Connected\n")
        
        async with db.pool.acquire() as conn:
            # Get most recent call
            call = await conn.fetchrow("""
                SELECT 
                    id, call_sid, caller_phone, caller_name,
                    started_at, ended_at, duration_seconds,
                    status, intent, language, metadata
                FROM calls
                ORDER BY started_at DESC
                LIMIT 1
            """)
            
            if not call:
                print("❌ No calls found in database")
                return
            
            print("📞 Most Recent Call:")
            print(f"   Call ID: {call['id']}")
            print(f"   Call SID: {call['call_sid']}")
            print(f"   Caller: {call['caller_phone']}")
            print(f"   Name: {call['caller_name']}")
            print(f"   Started: {call['started_at']}")
            print(f"   Ended: {call['ended_at']}")
            print(f"   Duration: {call['duration_seconds']} seconds")
            print(f"   Status: {call['status']}")
            print(f"   Intent: {call['intent']}")
            print(f"   Language: {call['language']}")
            
            # Check metadata for AI insights
            metadata = call.get('metadata', {})
            if metadata and 'ai_insights' in metadata:
                print(f"\n✅ AI Insights Found:")
                insights = metadata['ai_insights']
                print(f"   Intent: {insights.get('primary_intent')}")
                print(f"   Sentiment: {insights.get('sentiment')}")
                print(f"   Resolution: {insights.get('resolution_status')}")
                print(f"   Satisfaction: {insights.get('customer_satisfaction')}")
            else:
                print(f"\n⚠️  No AI insights in metadata")
                print(f"   Metadata: {metadata}")
            
            # Get conversation transcript
            print(f"\n💬 Conversation Transcript:")
            transcripts = await conn.fetch("""
                SELECT speaker, text, timestamp_ms
                FROM transcripts
                WHERE call_id = $1
                ORDER BY timestamp_ms ASC
            """, call['id'])
            
            if transcripts:
                print(f"   Found {len(transcripts)} conversation turns:\n")
                for i, turn in enumerate(transcripts, 1):
                    speaker = turn['speaker'].title()
                    text = turn['text'][:100] + "..." if len(turn['text']) > 100 else turn['text']
                    print(f"   {i}. {speaker}: {text}")
            else:
                print(f"   ❌ No transcripts found")
                print(f"   This means conversation history wasn't saved")
            
            # Check for appointments linked to this call
            print(f"\n📅 Appointments for this call:")
            appointments = await conn.fetch("""
                SELECT id, customer_name, service_type, appointment_datetime, status
                FROM appointments
                WHERE call_id = $1
            """, call['id'])
            
            if appointments:
                print(f"   ✅ Found {len(appointments)} appointment(s):")
                for appt in appointments:
                    print(f"      - {appt['customer_name']}: {appt['service_type']}")
                    print(f"        Time: {appt['appointment_datetime']}")
                    print(f"        Status: {appt['status']}")
            else:
                print(f"   ❌ No appointments found for this call")
            
            # Check for leads linked to this call
            print(f"\n👤 Leads for this call:")
            leads = await conn.fetch("""
                SELECT id, name, phone, inquiry_details, lead_score
                FROM leads
                WHERE call_id = $1
            """, call['id'])
            
            if leads:
                print(f"   ✅ Found {len(leads)} lead(s):")
                for lead in leads:
                    print(f"      - {lead['name']}: Score {lead['lead_score']}/10")
                    print(f"        Inquiry: {lead['inquiry_details'][:80]}...")
            else:
                print(f"   ❌ No leads found for this call")
            
            print("\n" + "="*60)
            
            # Diagnosis
            print("\n🔍 DIAGNOSIS:")
            
            if call['status'] != 'completed':
                print(f"   ⚠️  Call status is '{call['status']}', not 'completed'")
                print(f"   → Conversation analysis only runs when call completes")
            
            if not transcripts:
                print(f"   ⚠️  No conversation transcripts saved")
                print(f"   → Check if conversation history is being captured")
                print(f"   → Look for 'add_conversation_turn' in server logs")
            
            if transcripts and not appointments and not leads:
                print(f"   ⚠️  Transcripts exist but no appointments/leads extracted")
                print(f"   → Check server logs for:")
                print(f"      - '🤖 Analyzing conversation with AI...'")
                print(f"      - '📊 Conversation analysis complete'")
                print(f"      - Any error messages")
            
            if appointments or leads:
                print(f"   ✅ Conversation analysis worked!")
                print(f"   → Data was successfully extracted and saved")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_recent_call())
