# Twilio Webhook Configuration Guide

## Current Issue
Your Twilio phone number is NOT calling the `/incoming-call` endpoint, which means calls are not being properly initialized in the database.

## Required Configuration

### Step 1: Get Your ngrok URL
First, make sure your ngrok tunnel is running and get the URL:

```bash
# In a separate terminal, run:
ngrok http 5050

# You'll see output like:
# Forwarding: https://abc123.ngrok.io -> http://localhost:5050
```

Copy the `https://` URL (e.g., `https://abc123.ngrok.io`)

### Step 2: Configure Twilio Webhook

1. **Go to Twilio Console:**
   - Visit: https://console.twilio.com/
   - Navigate to: **Phone Numbers** > **Manage** > **Active Numbers**

2. **Select Your Phone Number:**
   - Click on your Twilio phone number

3. **Configure Voice Settings:**
   - Scroll down to **"Voice Configuration"** section
   - Under **"A call comes in"**:
     - Select: **Webhook**
     - Enter URL: `https://[YOUR-NGROK-URL]/incoming-call`
       - Example: `https://abc123.ngrok.io/incoming-call`
     - Select: **HTTP POST**
   
4. **Optional - Configure Fallback (Recommended):**
   - Under **"Primary handler fails"**:
     - Select: **Webhook**
     - Enter URL: `https://[YOUR-NGROK-URL]/incoming-call`
     - Select: **HTTP POST**

5. **Save Configuration:**
   - Click **Save** at the bottom of the page

## Correct Configuration Example

```
Voice Configuration
├── A call comes in
│   ├── Type: Webhook
│   ├── URL: https://abc123.ngrok.io/incoming-call
│   └── Method: HTTP POST
│
└── Primary handler fails (optional)
    ├── Type: Webhook
    ├── URL: https://abc123.ngrok.io/incoming-call
    └── Method: HTTP POST
```

## What This Does

When a call comes in, Twilio will:
1. **Call your `/incoming-call` endpoint** with call details
2. Your server will:
   - Create call record in database
   - Store call context in Redis
   - Return TwiML with WebSocket connection instructions
3. Twilio will then:
   - Connect to your `/media-stream` WebSocket
   - Stream audio bidirectionally

## Testing the Configuration

### Test 1: Check if endpoint is accessible
```bash
# From your terminal:
curl https://[YOUR-NGROK-URL]/incoming-call

# You should see a TwiML response (XML)
```

### Test 2: Make a test call
1. Call your Twilio number
2. Watch your server logs for:
   ```
   📞 /incoming-call endpoint HIT!
   📞 Incoming call from +1234567890 (SID: CA...)
   🔄 Initiating call in system...
   ✅ Call initiated in system: <uuid>
   ```

### Test 3: Verify call was saved
```bash
# Check Redis:
redis-cli KEYS "session:*"

# Check Database:
psql -d voice_automation -c "SELECT call_sid, status FROM calls ORDER BY started_at DESC LIMIT 5;"
```

## Common Issues

### Issue 1: ngrok URL changes
**Problem:** ngrok URL changes every time you restart it (free tier)

**Solution:** 
- Update Twilio webhook URL every time ngrok restarts
- OR upgrade to ngrok paid plan for static URL
- OR use a custom domain

### Issue 2: "Webhook Error - 502 Bad Gateway"
**Problem:** Server is not running or ngrok is not connected

**Solution:**
1. Make sure your FastAPI server is running: `python main.py`
2. Make sure ngrok is running: `ngrok http 5050`
3. Check ngrok dashboard: http://localhost:4040

### Issue 3: "Webhook Error - 404 Not Found"
**Problem:** Wrong endpoint URL

**Solution:**
- Make sure URL ends with `/incoming-call` (not `/media-stream`)
- Check for typos in the URL

## Fallback Mechanism (Already Implemented)

Even if you don't configure the webhook correctly, our code now has a fallback that will:
1. Detect that `/incoming-call` wasn't called
2. Automatically create the call when the WebSocket connects
3. Log a warning message

However, it's STRONGLY RECOMMENDED to configure the webhook correctly for the best experience.

## Verification Checklist

- [ ] ngrok is running and showing your local server
- [ ] Twilio webhook is set to `https://[ngrok-url]/incoming-call`
- [ ] Webhook method is set to `HTTP POST`
- [ ] Server is running on port 5050
- [ ] Test call shows "📞 /incoming-call endpoint HIT!" in logs
- [ ] Call is saved in database
- [ ] Transcripts are saved after call ends

## Quick Test Command

```bash
# Test if your endpoint is reachable:
curl -X POST https://[YOUR-NGROK-URL]/incoming-call \
  -d "From=+1234567890" \
  -d "CallSid=TEST123" \
  -d "To=+1987654321"

# You should see TwiML XML response
```

## Need Help?

If you're still having issues:
1. Check server logs for errors
2. Check ngrok dashboard at http://localhost:4040 for incoming requests
3. Check Twilio debugger at https://console.twilio.com/monitor/logs/debugger
4. Make sure your server is accessible from the internet via ngrok
