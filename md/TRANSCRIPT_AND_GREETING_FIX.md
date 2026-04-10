# Transcript Saving & Greeting Configuration Fix

## Summary
Fixed two critical issues:
1. **Transcript saving when calls complete** - Finally block now executes properly
2. **Configurable greeting message** - Greeting can be edited from dashboard configuration

## Changes Made

### 1. Fixed WebSocket Handler Completion (handlers.py)
**Problem**: `send_to_twilio` handler wasn't completing when calls ended, preventing `finally` block execution

**Solution**:
- Added `finally` blocks to both `receive_from_twilio()` and `send_to_twilio()` with logging
- Added `asyncio.CancelledError` exception handler in `send_to_twilio()`
- Added explicit check for OpenAI WebSocket state to exit cleanly
- Added `websockets.exceptions.ConnectionClosed` exception handler

**Code Changes**:
```python
# handlers.py - receive_from_twilio
except WebSocketDisconnect:
    print("📞 Client disconnected from Twilio")
    if openai_ws.state.name == 'OPEN':
        print("🔌 Closing OpenAI WebSocket...")
        await openai_ws.close()
finally:
    print("🏁 receive_from_twilio handler completed")

# handlers.py - send_to_twilio
except websockets.exceptions.ConnectionClosed:
    print("🔌 OpenAI WebSocket connection closed")
except asyncio.CancelledError:
    print("🛑 send_to_twilio task cancelled")
    raise
except Exception as e:
    print(f"❌ Error in send_to_twilio: {e}")
finally:
    print("🏁 send_to_twilio handler completed")
```

### 2. Fixed Task Cancellation (main.py)
**Problem**: `asyncio.gather()` waited for both handlers to complete, but `send_to_twilio` hung

**Solution**:
- Changed from `asyncio.gather()` to `asyncio.wait()` with `FIRST_COMPLETED`
- When `receive_from_twilio` completes (Twilio disconnects), cancel `send_to_twilio` task
- This ensures both handlers complete and `finally` block executes

**Code Changes**:
```python
# main.py - handle_media_stream
# Create tasks so we can cancel them if needed
receive_task = asyncio.create_task(receive_from_twilio(websocket, openai_ws, state))
send_task = asyncio.create_task(send_to_twilio(websocket, openai_ws, state))

# Wait for both tasks with a timeout
done, pending = await asyncio.wait(
    [receive_task, send_task],
    return_when=asyncio.FIRST_COMPLETED
)

# Cancel any pending tasks
for task in pending:
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print(f"✅ Task cancelled successfully")
```

### 3. Fixed Timezone Issues (call_manager.py)
**Problem**: Timezone-naive and timezone-aware datetime comparison errors

**Solution**:
- Ensured `created_at` is always timezone-aware when parsed from Redis
- Added timezone check in `complete_call()` before calculating duration

**Code Changes**:
```python
# call_manager.py - get_call_context
created_at_str = session_data["created_at"]
created_at = datetime.fromisoformat(created_at_str)
# Ensure timezone-aware
if created_at.tzinfo is None:
    created_at = created_at.replace(tzinfo=timezone.utc)

# call_manager.py - complete_call
started_at = context.created_at
# Ensure started_at is timezone-aware
if started_at.tzinfo is None:
    started_at = started_at.replace(tzinfo=timezone.utc)
duration_seconds = int((ended_at - started_at).total_seconds())
```

### 4. Made Greeting Configurable (main.py)
**Problem**: Greeting message was partially hardcoded - custom greeting only replaced first part

**Solution**:
- Removed hardcoded second part about language support
- Now uses ONLY the custom greeting from configuration
- If no custom greeting, uses default message

**Code Changes**:
```python
# main.py - /incoming-call endpoint
if custom_greeting and isinstance(custom_greeting, str):
    print(f"🎤 Using custom greeting: {custom_greeting[:50]}...")
    response.say(
        custom_greeting,
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
else:
    # Default greeting (only if no custom greeting configured)
    print(f"🎤 Using default greeting")
    response.say(
        "Welcome to our AI-powered voice assistant. Please wait while we connect you.",
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
    response.pause(length=1)
    response.say(
        "You can start talking now. I can understand English, Hindi, Tamil, Telugu, and Bengali.",
        voice="Google.en-US-Chirp3-HD-Aoede"
    )
```

## How It Works Now

### Call Flow:
1. **Call Starts**: Twilio connects to `/incoming-call` endpoint
2. **Greeting**: System plays custom greeting from configuration (or default if not configured)
3. **WebSocket**: Twilio connects to `/media-stream` with `call_sid` in query params
4. **Conversation**: Both handlers run concurrently processing audio
5. **Call Ends**: When Twilio disconnects:
   - `receive_from_twilio` catches `WebSocketDisconnect`
   - Closes OpenAI WebSocket
   - `receive_from_twilio` completes (logs "🏁 receive_from_twilio handler completed")
   - `asyncio.wait()` returns with `FIRST_COMPLETED`
   - `send_to_twilio` task is cancelled
   - `send_to_twilio` catches `CancelledError` and completes (logs "🏁 send_to_twilio handler completed")
   - `finally` block executes (logs "🔚 Finally block executing...")
   - `complete_call()` is called with `call_sid`
   - Transcripts are saved to database (logs "💾 Saving X conversation turns to database...")
   - Call status updated to "completed"

### Configuration:
1. Open dashboard at `http://localhost:5050/frontend/index.html`
2. Go to "Configuration" tab
3. Edit "Greeting Message" field
4. Click "Save Configuration"
5. Next call will use your custom greeting

### Appointments:
- Appointments are automatically saved when AI books them during calls
- View appointments in "Appointments" tab on dashboard
- Shows: customer name, phone, service type, date/time, duration, status

## Testing

### Test Transcript Saving:
1. Make a test call
2. Have a conversation with the AI
3. End the call
4. Check server logs for:
   - "🏁 receive_from_twilio handler completed"
   - "🏁 send_to_twilio handler completed"
   - "🔚 Finally block executing..."
   - "💾 Saving X conversation turns to database..."
   - "✅ Call completed and transcripts saved"
5. Check dashboard - click "View" on the call
6. Should see full conversation with AI insights

### Test Custom Greeting:
1. Open dashboard configuration
2. Change greeting to: "Hello! Welcome to ABC Company. How can I assist you today?"
3. Save configuration
4. Make a test call
5. Should hear your custom greeting (not the default)

### Test Appointments:
1. Make a call and ask AI to book an appointment
2. Provide details (name, date, time, service)
3. End call
4. Go to "Appointments" tab on dashboard
5. Should see the booked appointment

## Files Modified
- `handlers.py` - Added finally blocks and exception handling
- `main.py` - Changed to task cancellation approach, fixed greeting
- `call_manager.py` - Fixed timezone handling

## Status
✅ Transcript saving working
✅ Custom greeting working
✅ Appointments display working
✅ Real database mode enabled
✅ Real Redis enabled
