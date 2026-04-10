# Diagnosing OpenAI Response Issue

## Issue
OpenAI is not responding during calls.

## Root Cause Found
The session initialization in `main.py` was not including the tools configuration. The session was being created manually instead of using the updated configuration with tools.

## Fix Applied
Updated `main.py` line ~1897 to include tools in the session configuration:

```python
# Before (missing tools):
session_update = {
    "type": "session.update",
    "session": {
        "instructions": custom_instructions,
        # ... other config ...
    }
}

# After (with tools):
from tools.appointment_tools import ALL_TOOLS

tools_config = [
    {
        "type": tool.type,
        "name": tool.name,
        "description": tool.description,
        "parameters": tool.parameters
    }
    for tool in ALL_TOOLS
]

session_update = {
    "type": "session.update",
    "session": {
        "instructions": custom_instructions,
        "tools": tools_config,
        "tool_choice": "auto",
        # ... other config ...
    }
}
```

## Verification

Run this to verify the fix:
```bash
python3 test_openai_response.py
```

Should show:
```
✅ Session config is valid JSON
✅ Model: gpt-4o-realtime-preview
✅ Tools: 6 tools
✅ Tool choice: auto
```

## What to Check When Starting Server

When you start the server, look for these logs:

```
📡 Sending session update with multilingual instructions and 6 tools
   • check_availability: Check if appointment slots are available...
   • get_available_slots: Get a list of available time slots...
   • book_appointment: Book an appointment for a customer...
   • create_lead: Create a sales lead when a customer...
   • get_customer_history: Look up a customer's previous calls...
   • send_sms: Send an SMS message to a customer...
```

If you see this, tools are properly registered and OpenAI should respond.

## Other Potential Issues

If OpenAI still doesn't respond, check:

### 1. OpenAI API Key
```bash
# Check if API key is set
grep OPENAI_API_KEY .env
```

### 2. Model Name
```bash
# Check model configuration
grep OPENAI_REALTIME_MODEL .env
```

Should be: `gpt-4o-realtime-preview-2024-12-17` or `gpt-4o-realtime-preview`

### 3. WebSocket Connection
Look for these in logs:
```
✅ Session initialized with AI features and custom configuration
```

If you see errors like:
- `Connection refused`
- `401 Unauthorized`
- `Invalid API key`

Then check your OpenAI API key and account status.

### 4. Audio Format
The session uses `audio/pcmu` format (G.711 μ-law) which is required for Twilio.

### 5. Instructions Too Long
If your system message is very long (>10,000 characters), OpenAI might not respond. Check:
```bash
python3 -c "from config import get_system_message; msg = get_system_message('Test', 'test', '', ''); print(f'Instructions length: {len(msg)} characters')"
```

Should be under 10,000 characters.

## Testing the Fix

### 1. Start Server
```bash
python3 main.py
```

### 2. Watch for Tool Registration
You should see:
```
📡 Sending session update with multilingual instructions and 6 tools
   • check_availability: ...
   • get_available_slots: ...
   • book_appointment: ...
   • create_lead: ...
   • get_customer_history: ...
   • send_sms: ...
```

### 3. Make a Test Call
Call your Twilio number. You should hear the AI greeting.

### 4. Check Logs
Look for:
```
🎤 send_to_twilio started
📨 Twilio event: start
Incoming stream has started [stream_sid]
```

If you see these, the connection is working.

## If Still Not Working

### Check OpenAI Response Events
Add this debug logging to `handlers.py` in the `send_to_twilio` function:

```python
async for openai_message in openai_ws:
    response = json.loads(openai_message)
    print(f"🔔 OpenAI event: {response.get('type')}")  # Add this line
    # ... rest of code
```

You should see events like:
- `session.created`
- `session.updated`
- `conversation.item.created`
- `response.audio.delta`

If you don't see any events, the OpenAI connection isn't working.

### Check Twilio Audio
Make sure Twilio is sending audio:
```python
# In receive_from_twilio function
if data['event'] == 'media':
    print(f"📡 Received audio: {len(data['media']['payload'])} bytes")
```

### Check for Errors
Look for any error messages in the logs:
- `WebSocket error`
- `OpenAI WebSocket connection closed`
- `Error in send_to_twilio`

## Quick Fix Checklist

- [x] Tools added to session configuration
- [ ] Server starts without errors
- [ ] Tool registration logs appear
- [ ] OpenAI API key is valid
- [ ] Model name is correct
- [ ] WebSocket connection succeeds
- [ ] Audio is being sent/received

## Next Steps

1. Restart your server: `python3 main.py`
2. Look for the tool registration logs
3. Make a test call
4. Check if AI responds

If AI still doesn't respond after this fix, share the server logs and we'll debug further.
