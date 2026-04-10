# Log Analysis & Transcript Extraction Guide

## Problem
Call transcripts are not being saved to the database due to initialization issues. This workaround extracts transcripts directly from server logs using OpenAI.

## Solution
Use OpenAI to analyze server logs and extract conversation transcripts, then save them to the database.

## Setup

### Step 1: Start Server with Log Capture
```bash
# Start server and save logs to file
python main.py 2>&1 | tee server.log
```

This will:
- Run your server normally
- Display output in terminal
- Save all output to `server.log` file

### Step 2: Monitor Logs in Real-Time (Optional)
In a separate terminal:
```bash
# Monitor logs and auto-extract transcripts
python live_log_monitor.py server.log
```

This will:
- Watch the log file for new entries
- Detect when calls end
- Automatically extract and save transcripts

### Step 3: Analyze Existing Logs
```bash
# Analyze a specific log file
python log_analyzer.py server.log

# Or analyze recent logs
python log_analyzer.py
```

## How It Works

1. **Log Capture**: Server logs contain OpenAI response events with transcripts
2. **AI Analysis**: OpenAI GPT-4 analyzes the logs and extracts:
   - Call SID
   - Conversation turns (speaker + text)
   - Timestamps
   - Metadata (language, duration, etc.)
3. **Database Save**: Extracted data is saved to your database
4. **Frontend Display**: Frontend can now query the database for transcripts

## Example Log Pattern

The logs contain transcript data like this:
```json
{
  "type": "response.done",
  "response": {
    "output": [{
      "content": [{
        "transcript": "Thank you for calling. How can I help you?"
      }]
    }]
  }
}
```

## API Endpoint for Frontend

Add this endpoint to `main.py` to serve transcripts:

```python
@app.get("/api/calls/{call_id}/transcript")
async def get_call_transcript(call_id: str):
    """Get transcript for a specific call."""
    if not database_service:
        return JSONResponse({"error": "Database not available"}, status_code=503)
    
    try:
        async with database_service.pool.acquire() as conn:
            # Get call info
            call = await conn.fetchrow(
                "SELECT * FROM calls WHERE id = $1 OR call_sid = $1",
                call_id
            )
            
            if not call:
                return JSONResponse({"error": "Call not found"}, status_code=404)
            
            # Get transcripts
            transcripts = await conn.fetch(
                "SELECT speaker, text, timestamp_ms FROM transcripts WHERE call_id = $1 ORDER BY timestamp_ms",
                str(call['id'])
            )
            
            return JSONResponse({
                "call_sid": call['call_sid'],
                "conversation": [
                    {
                        "speaker": t['speaker'],
                        "text": t['text'],
                        "timestamp_ms": t['timestamp_ms']
                    }
                    for t in transcripts
                ]
            })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
```

## Frontend Integration

Update your frontend to fetch transcripts:

```javascript
async function loadCallTranscript(callId) {
    try {
        const response = await fetch(`/api/calls/${callId}/transcript`);
        const data = await response.json();
        
        // Display transcript
        const transcriptDiv = document.getElementById('transcript');
        transcriptDiv.innerHTML = data.conversation.map(turn => `
            <div class="transcript-turn ${turn.speaker}">
                <strong>${turn.speaker}:</strong> ${turn.text}
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading transcript:', error);
    }
}
```

## Automated Workflow

For fully automated transcript extraction:

```bash
# Terminal 1: Run server with logging
python main.py 2>&1 | tee server.log

# Terminal 2: Monitor and auto-extract
python live_log_monitor.py server.log
```

Now every call will automatically:
1. Generate logs
2. Be detected when it ends
3. Have transcript extracted via OpenAI
4. Be saved to database
5. Be available in frontend

## Manual Extraction

If you already have log files:

```bash
# Extract from specific call logs
python log_analyzer.py old_server.log

# The script will:
# 1. Read the log file
# 2. Send to OpenAI for analysis
# 3. Extract structured transcript data
# 4. Save to database
# 5. Print results
```

## Cost Considerations

- Uses GPT-4o-mini for analysis (~$0.15 per 1M tokens)
- Average log analysis: ~2000 tokens per call
- Cost: ~$0.0003 per call analyzed
- Very affordable for this workaround

## Benefits

✅ Works even when call initialization fails
✅ Can recover transcripts from old logs
✅ No code changes to main call flow
✅ Uses AI to intelligently extract data
✅ Saves to database for frontend access
✅ Can be automated with monitoring script

## Limitations

⚠️ Requires logs to contain transcript data
⚠️ Slight delay (few seconds) for AI analysis
⚠️ Depends on OpenAI API availability
⚠️ Not real-time (processes after call ends)

## Recommendation

This is a WORKAROUND. The proper fix is still to:
1. Configure Twilio webhook correctly
2. Ensure `/incoming-call` endpoint is called
3. Fix call initialization in the start event handler

But this solution lets you capture transcripts immediately while debugging the root cause!
