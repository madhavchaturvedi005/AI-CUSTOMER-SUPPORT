# 🚨 QUICK FIX: Calls Not Being Created

## Problem
Calls show "initiated" but never "completed". The `/incoming-call` endpoint is never being hit by Twilio.

## Root Cause
**The FastAPI server is not running or not responding on port 5050.**

Your ngrok shows `0 connections`, which confirms the server isn't receiving requests.

---

## ✅ SOLUTION (Follow These Steps)

### Step 1: Run Diagnostics
```bash
python3 diagnose_server.py
```

This will tell you exactly what's wrong.

### Step 2: Start the Server

**Terminal 1 - Start FastAPI Server:**
```bash
python3 main.py
```

**Wait for this message:**
```
INFO:     Uvicorn running on http://0.0.0.0:5050 (Press CTRL+C to quit)
```

**Keep this terminal open!** Don't close it.

### Step 3: Start ngrok (if not running)

**Terminal 2 - Start ngrok:**
```bash
ngrok http 5050
```

You should see:
```
Forwarding    https://kerry-isenthalpic-juristically.ngrok-free.dev -> http://localhost:5050
```

**Keep this terminal open too!**

### Step 4: Test the Server

**Terminal 3 - Test Health Endpoint:**
```bash
curl http://localhost:5050/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-04-10T...",
  "database": "connected",
  "redis": "connected"
}
```

**Test through ngrok:**
```bash
curl https://kerry-isenthalpic-juristically.ngrok-free.dev/health
```

Should return the same JSON (not "Not Found").

### Step 5: Make a Test Call

Call your Twilio number and watch Terminal 1 (server logs).

**You should see:**
```
📞 /incoming-call endpoint HIT!
✅ Call created in database: <uuid>
```

**If you see this, it's working!** 🎉

---

## 🔍 Troubleshooting

### If server won't start:
```bash
# Check if port 5050 is in use
lsof -i :5050

# If something is using it, kill it:
kill -9 <PID>

# Then start server again
python3 main.py
```

### If you get database errors:
```bash
# Check PostgreSQL is running
psql -U madhavchaturvedi -d voice_automation -c "SELECT 1;"

# If it fails, start PostgreSQL:
brew services start postgresql
# or
pg_ctl -D /usr/local/var/postgres start
```

### If ngrok shows 0 connections:
1. Make sure server is running first (Step 2)
2. Test health endpoint locally (Step 4)
3. Then test through ngrok
4. If still failing, restart ngrok

### If /incoming-call still not hit:
1. Check Twilio webhook configuration:
   - Go to Twilio Console
   - Phone Numbers → Your Number
   - Voice Configuration → A Call Comes In
   - Should be: `https://kerry-isenthalpic-juristically.ngrok-free.dev/incoming-call`
   - Method: `POST` or `GET` (both work)

2. Check ngrok URL matches Twilio webhook

3. Make sure ngrok is forwarding to port 5050

---

## 📊 What Should Happen

### Correct Flow:
1. **Twilio receives call** → Sends webhook to `/incoming-call`
2. **Server creates call** in database with status "initiated"
3. **Server returns TwiML** → Twilio connects to `/media-stream` WebSocket
4. **Conversation happens** → Transcripts saved in real-time
5. **Call ends** → `complete_call()` runs AI analysis
6. **AI extracts data** → Appointments, leads, insights saved

### Current Problem:
- Step 1 is failing (webhook not reaching server)
- Server never creates call in database
- WebSocket tries to complete non-existent call
- Error: "Call not found in database"

---

## 🎯 Expected Logs (When Working)

**When call comes in:**
```
📞 /incoming-call endpoint HIT!
📞 Incoming call from +1234567890 (SID: CA...)
🔄 Initiating call in system...
✅ Call created in database: <uuid>
```

**During call:**
```
🗣️  Speech started detected
📝 Transcript: "Hello, I'd like to book an appointment"
```

**When call ends:**
```
📞 Call ended, completing call: CA...
🤖 Analyzing conversation with AI...
✅ Appointment saved: <uuid> for John Doe
✅ Lead saved: <uuid> (score: 8)
✅ Call insights: appointment_booking - positive
✅ Call completed and transcripts saved
```

---

## 🆘 Still Not Working?

Run the diagnostic script again:
```bash
python3 diagnose_server.py
```

Check the output and follow the recommendations.

If you're still stuck, share:
1. Output of `diagnose_server.py`
2. Server logs from Terminal 1
3. Any error messages
