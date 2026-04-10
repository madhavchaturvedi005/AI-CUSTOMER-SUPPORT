"""Analyze server logs to extract call transcripts using OpenAI."""

import re
import os
from openai import OpenAI
from datetime import datetime
from typing import List, Dict, Any
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_transcripts_from_logs(log_text: str) -> Dict[str, Any]:
    """
    Use OpenAI to extract call transcripts from server logs.
    
    Args:
        log_text: Raw server log text
        
    Returns:
        Dictionary with call_sid, transcript, and metadata
    """
    
    prompt = f"""
You are analyzing server logs from a voice call system. Extract the following information:

1. Call SID (starts with CA)
2. All conversation transcripts (look for "transcript" fields in the logs)
3. Speaker identification (customer/assistant/caller)
4. Timestamps if available
5. Call duration
6. Any detected language

Format the output as JSON:
{{
    "call_sid": "CA...",
    "conversation": [
        {{"speaker": "assistant", "text": "...", "timestamp": "..."}},
        {{"speaker": "customer", "text": "...", "timestamp": "..."}}
    ],
    "metadata": {{
        "duration": "...",
        "language": "...",
        "status": "..."
    }}
}}

Server Logs:
{log_text}
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a log analyzer that extracts structured data from server logs."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error analyzing logs: {e}")
        return {
            "call_sid": "unknown",
            "conversation": [],
            "metadata": {"error": str(e)}
        }


def save_transcript_to_database(transcript_data: Dict[str, Any]):
    """Save extracted transcript to database."""
    import asyncio
    from database import DatabaseService
    
    async def _save():
        db = DatabaseService()
        await db.connect()
        
        call_sid = transcript_data.get("call_sid")
        conversation = transcript_data.get("conversation", [])
        
        # Create call record if it doesn't exist
        try:
            call_id = await db.create_call(
                call_sid=call_sid,
                caller_phone="unknown",
                direction="inbound",
                status="completed"
            )
            
            # Save each transcript turn
            for turn in conversation:
                await db.save_transcript(
                    call_id=call_id,
                    speaker=turn.get("speaker", "unknown"),
                    text=turn.get("text", ""),
                    timestamp_ms=0,
                    language="en",
                    confidence=1.0
                )
            
            print(f"✅ Saved {len(conversation)} transcript turns for call {call_sid}")
            return call_id
        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return None
    
    return asyncio.run(_save())


def analyze_log_file(log_file_path: str):
    """Analyze a log file and extract transcripts."""
    print(f"📖 Reading log file: {log_file_path}")
    
    with open(log_file_path, 'r') as f:
        log_text = f.read()
    
    print(f"📊 Analyzing {len(log_text)} characters of logs...")
    result = extract_transcripts_from_logs(log_text)
    
    print(f"\n✅ Analysis complete!")
    print(f"Call SID: {result.get('call_sid')}")
    print(f"Conversation turns: {len(result.get('conversation', []))}")
    
    # Save to database
    if result.get('conversation'):
        call_id = save_transcript_to_database(result)
        if call_id:
            print(f"✅ Transcript saved to database with call_id: {call_id}")
    
    return result


def analyze_recent_logs(lines: int = 500):
    """Analyze the most recent server logs."""
    print(f"📖 Analyzing last {lines} lines of server output...")
    print("⚠️  Make sure to pipe your server output to a file:")
    print("   python main.py 2>&1 | tee server.log")
    print()
    
    # Try to read from common log locations
    log_files = ["server.log", "nohup.out", "output.log"]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"✅ Found log file: {log_file}")
            return analyze_log_file(log_file)
    
    print("❌ No log file found. Please run:")
    print("   python main.py 2>&1 | tee server.log")
    return None


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Analyze specific log file
        log_file = sys.argv[1]
        result = analyze_log_file(log_file)
    else:
        # Analyze recent logs
        result = analyze_recent_logs()
    
    if result:
        # Pretty print the result
        print("\n" + "="*60)
        print("EXTRACTED TRANSCRIPT")
        print("="*60)
        print(json.dumps(result, indent=2))
