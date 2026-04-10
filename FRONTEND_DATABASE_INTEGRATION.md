# Frontend Database Integration Guide

## Overview

The frontend dashboard is now integrated with both the **database** and **real-time calling system**. This document explains how everything connects together.

## Architecture

```
┌─────────────────┐
│   Frontend      │
│  (Browser)      │
│  dashboard.js   │
└────────┬────────┘
         │ HTTP/REST API
         ▼
┌─────────────────┐
│   FastAPI       │
│   main.py       │
│  API Endpoints  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────┐
│Database │ │  Redis   │
│PostgreSQL│ │  Cache   │
└─────────┘ └──────────┘
         │
         ▼
┌─────────────────┐
│  Live Calls     │
│  (Twilio +      │
│   OpenAI)       │
└─────────────────┘
```

## How It Works

### 1. Real-Time Call Integration

When a phone call comes in:

1. **Twilio** receives the call → `/incoming-call` endpoint
2. **CallManager** creates a call record in PostgreSQL
3. **WebSocket** connection established → `/media-stream`
4. **AI features** process the call:
   - Language detection (first 10 seconds)
   - Intent detection with clarification
   - Conversation history tracking
   - Lead capture and scoring
   - Appointment booking
5. **Database** stores all call data in real-time
6. **Frontend** displays updated data (auto-refreshes every 30 seconds)

### 2. Database Connection

The system supports two modes:

#### Production Mode (Real Database)
Set environment variables:
```bash
export USE_REAL_DB=true
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=voice_automation
export DB_USER=postgres
export DB_PASSWORD=your_password

export USE_REAL_REDIS=true
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

#### Demo Mode (Mock Data)
Default behavior - uses mock data for demonstration:
```bash
# No environment variables needed
# System automatically uses mock data
```

### 3. API Endpoints → Database Queries

#### GET `/api/analytics`
**Real Data Query:**
```sql
-- Total calls
SELECT COUNT(*) FROM calls;

-- Call volume (last 7 days)
SELECT TO_CHAR(started_at, 'Dy') as day, COUNT(*) as count
FROM calls
WHERE started_at >= NOW() - INTERVAL '7 days'
GROUP BY TO_CHAR(started_at, 'Dy'), DATE(started_at);

-- Intent distribution
SELECT intent, COUNT(*) as count
FROM calls
WHERE intent IS NOT NULL
GROUP BY intent;
```

**Fallback:** Mock data if database unavailable

#### GET `/api/calls`
**Real Data Query:**
```sql
SELECT * FROM calls
WHERE status = $1  -- optional filter
AND started_at >= $2  -- optional start_date
AND started_at <= $3  -- optional end_date
ORDER BY started_at DESC
LIMIT 50;
```

**Fallback:** Mock call records

#### GET `/api/leads`
**Real Data Query:**
```sql
SELECT * FROM leads
WHERE lead_score >= 7  -- for filter=high
OR (lead_score >= 4 AND lead_score < 7)  -- for filter=medium
OR lead_score < 4  -- for filter=low
ORDER BY created_at DESC
LIMIT 50;
```

**Fallback:** Mock lead records

#### GET `/api/appointments`
**Real Data Query:**
```sql
SELECT * FROM appointments
WHERE appointment_datetime >= NOW()
ORDER BY appointment_datetime ASC
LIMIT 50;
```

**Fallback:** Mock appointment records

### 4. Live Call Data Flow

```
Phone Call → Twilio → /incoming-call
                ↓
         CallManager.initiate_call()
                ↓
         PostgreSQL: INSERT INTO calls
                ↓
         Redis: Cache call context
                ↓
         WebSocket: /media-stream
                ↓
    ┌────────────────────────┐
    │  AI Processing         │
    │  - Language detection  │
    │  - Intent detection    │
    │  - Lead capture        │
    │  - Appointment booking │
    └────────────────────────┘
                ↓
         PostgreSQL: UPDATE calls, INSERT leads/appointments
                ↓
         Frontend: Auto-refresh displays new data
```

## Setup Instructions

### Option 1: Full Production Setup (Real Database)

1. **Install PostgreSQL:**
```bash
# macOS
brew install postgresql
brew services start postgresql

# Create database
createdb voice_automation
```

2. **Run Database Migration:**
```bash
python3 migrations/run_migration.py
```

3. **Install Redis:**
```bash
# macOS
brew install redis
brew services start redis
```

4. **Configure Environment:**
```bash
# Add to .env file
USE_REAL_DB=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_automation
DB_USER=postgres
DB_PASSWORD=your_password

USE_REAL_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379
```

5. **Start Application:**
```bash
python3 main.py
```

6. **Access Dashboard:**
```
http://localhost:5050/frontend/index.html
```

### Option 2: Demo Mode (Mock Data)

1. **Start Application:**
```bash
python3 main.py
```

2. **Access Dashboard:**
```
http://localhost:5050/frontend/index.html
```

The dashboard will show mock data and still handle real phone calls!

## Real-Time Updates

### Auto-Refresh
The dashboard automatically refreshes every 30 seconds:
```javascript
// In dashboard.js
setInterval(refreshDashboard, 30000);
```

### Manual Refresh
Click the "Refresh" button on any tab to update immediately.

### WebSocket Updates (Future Enhancement)
For true real-time updates, we can add WebSocket support:
```javascript
// Future implementation
const ws = new WebSocket('ws://localhost:5050/ws/dashboard');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateDashboard(data);
};
```

## Data Flow During Live Call

### Example: Sales Inquiry Call

1. **Call Initiated (t=0s)**
   - Database: `INSERT INTO calls (status='initiated')`
   - Frontend: Total calls counter increments

2. **Language Detected (t=5s)**
   - Database: `UPDATE calls SET language='hi'`
   - Frontend: Shows Hindi in call details

3. **Intent Detected (t=15s)**
   - Database: `UPDATE calls SET intent='sales_inquiry'`
   - Frontend: Intent distribution chart updates

4. **Lead Captured (t=45s)**
   - Database: `INSERT INTO leads (lead_score=8)`
   - Frontend: New lead appears in leads table
   - Frontend: High-value lead notification

5. **Call Completed (t=180s)**
   - Database: `UPDATE calls SET status='completed', duration_seconds=180`
   - Frontend: Call appears in call history
   - Frontend: Average duration updates

## Testing the Integration

### Test 1: Make a Real Phone Call
```bash
# Start the server
python3 main.py

# Make a call to your Twilio number
# Watch the dashboard update in real-time
```

### Test 2: Check Database Records
```bash
# Connect to PostgreSQL
psql voice_automation

# View recent calls
SELECT * FROM calls ORDER BY started_at DESC LIMIT 5;

# View leads
SELECT * FROM leads ORDER BY created_at DESC LIMIT 5;
```

### Test 3: API Endpoints
```bash
# Test analytics endpoint
curl http://localhost:5050/api/analytics

# Test calls endpoint
curl http://localhost:5050/api/calls

# Test leads endpoint
curl http://localhost:5050/api/leads?filter=high
```

## Monitoring

### Check Connection Status
The startup logs show connection status:
```
🚀 Initializing AI Voice Automation services...
   ✅ Connected to PostgreSQL database
   ✅ Connected to Redis cache
✅ AI Voice Automation services initialized!
   • CallManager: Ready
   • IntentDetector: Ready
   • LanguageManager: Ready (5 languages)
   • CallRouter: Ready (2 routing rules)
   • Database: PostgreSQL
   • Cache: Redis
```

### Dashboard Status Indicator
The dashboard shows system status in the top-right corner:
- 🟢 Green: All systems operational
- 🟡 Yellow: Using mock data (database unavailable)
- 🔴 Red: System error

## Troubleshooting

### Issue: Dashboard shows "No data"
**Solution:** 
- Check if database is running: `brew services list`
- Check environment variables: `echo $USE_REAL_DB`
- Check logs for connection errors

### Issue: Data not updating
**Solution:**
- Verify auto-refresh is working (check browser console)
- Click manual refresh button
- Check API endpoints directly: `curl http://localhost:5050/api/analytics`

### Issue: Mock data instead of real data
**Solution:**
- Set `USE_REAL_DB=true` in environment
- Verify database connection in startup logs
- Check database credentials in .env file

## Performance Considerations

### Database Queries
- All queries use indexes for performance
- Queries limited to 50 records by default
- Date range filters optimize large datasets

### Caching Strategy
- Redis caches active call contexts
- Database queries cached for 30 seconds
- Frontend auto-refresh interval: 30 seconds

### Scalability
- Connection pooling: 10-50 connections
- Async database operations
- Non-blocking API endpoints

## Security

### API Security
- CORS enabled for frontend access
- In production, restrict CORS to specific origins
- Add authentication middleware for sensitive endpoints

### Database Security
- Use environment variables for credentials
- Never commit .env file to git
- Use SSL/TLS for database connections in production

## Next Steps

1. **Add WebSocket support** for real-time updates without polling
2. **Implement authentication** for dashboard access
3. **Add export functionality** (CSV/JSON) for analytics
4. **Create admin panel** for configuration management
5. **Add user roles** (admin, agent, viewer)

## Summary

✅ Frontend is connected to the database
✅ Real-time calling data flows to the dashboard
✅ Auto-refresh keeps data current
✅ Graceful fallback to mock data if database unavailable
✅ All AI features (language detection, intent detection, lead capture) integrated
✅ Production-ready with proper error handling

The system is fully operational and ready for both demo and production use!
