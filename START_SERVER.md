# Server Startup Guide

## Problem
Twilio is returning `{"detail": "Not Found"}` when trying to reach your webhook. This means the `/incoming-call` endpoint is not accessible.

## Root Cause
The issue is that either:
1. The FastAPI server is not running
2. ngrok is not running or not forwarding correctly
3. The ngrok URL has changed and Twilio webhook needs updating

## Solution: Start Everything Correctly

### Step 1: Start the FastAPI Server

Open a terminal and run:

```bash
python main.py
```

You should see:
```
🚀 Initializing AI Voice Automation services...
   ✅ Connected to PostgreSQL database
   ✅ Connected to Redis cache
✅ AI Voice Automation services initialized!
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:5050
```

**Keep this terminal open!** The server must stay running.

### Step 2: Start ngrok

Open a **NEW** terminal (don't close the first one) and run:

```bash
ngrok http 5050
```

You should see:
```
Session Status                online
Forwarding                    https://xxxx-xxxx-xxxx.ngrok-free.app -> http://localhost:5050
```

**Copy the HTTPS URL** (the one that starts with `https://`)

**Keep this terminal open too!**

### Step 3: Test the Connection

Open a **THIRD** terminal and run:

```bash
python test_ngrok_connection.py
```

This will verify:
- ✅ Local server is running
- ✅ ngrok is running
- ✅ ngrok URL is accessible
- ✅ /incoming-call endpoint works

If all tests pass, you'll see your ngrok URL.

### Step 4: Update Twilio Webhook

1. Go to: https://console.twilio.com/
2. Navigate to: **Phone Numbers > Manage > Active Numbers**
3. Click on your phone number
4. Scroll to **Voice Configuration**
5. Set **"A CALL COMES IN"** to:
   ```
   https://YOUR-NGROK-URL/incoming-call
   ```
   (Replace YOUR-NGROK-URL with the URL from ngrok)
6. Make sure HTTP method is **POST**
7. Click **Save**

### Step 5: Make a Test Call

Call your Twilio number. You should see in the server terminal:

```
📞 /incoming-call endpoint HIT!
📞 Incoming call from +1234567890 (SID: CAxxxx)
🔄 Initiating call in system...
✅ Call initiated in system: <call-id>
```

## Troubleshooting

### Server won't start
- Check if port 5050 is already in use: `lsof -i :5050`
- Kill existing process: `kill -9 <PID>`
- Try again: `python main.py`

### ngrok won't start
- Check if ngrok is installed: `ngrok version`
- Install if needed: https://ngrok.com/download
- Make sure you're authenticated: `ngrok authtoken YOUR_TOKEN`

### Tests fail
Run the comprehensive diagnostic:
```bash
python diagnose_ngrok.py
```

This will tell you exactly what's wrong and how to fix it.

### Calls still not working
1. Check server logs for errors
2. Verify ngrok URL hasn't changed (it changes every time you restart ngrok)
3. Make sure Twilio webhook is updated with the current ngrok URL
4. Check that both terminals (server and ngrok) are still running

## Quick Reference

**Terminal 1 (Server):**
```bash
python main.py
```

**Terminal 2 (ngrok):**
```bash
ngrok http 5050
```

**Terminal 3 (Testing):**
```bash
python test_ngrok_connection.py
```

## Important Notes

1. **ngrok URL changes** every time you restart ngrok (unless you have a paid plan)
2. You must **update Twilio webhook** every time ngrok URL changes
3. Both server and ngrok must be **running simultaneously**
4. The fallback in WebSocket handler will create calls even if `/incoming-call` is missed, but it's better to fix the root cause

## What Happens When It Works

When everything is set up correctly:

1. Caller dials your Twilio number
2. Twilio sends POST request to `https://YOUR-NGROK-URL/incoming-call`
3. ngrok forwards to `http://localhost:5050/incoming-call`
4. FastAPI server receives request and creates call in database
5. Server returns TwiML to connect to WebSocket
6. Conversation begins
7. When call ends, AI analyzes conversation and extracts:
   - Appointments (saved to database)
   - Leads (saved to database)
   - Call insights (sentiment, intent, resolution)

You can then see everything in the dashboard at: http://localhost:5050/frontend/index.html
