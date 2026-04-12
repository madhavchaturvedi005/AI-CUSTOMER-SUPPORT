# System Architecture

## Complete System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                              │
│  http://localhost:5050/                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ 1. Request /
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Server                            │
│                  (main.py - Port 5050)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend Routes:                                             │
│  ├─ GET /              → Redirect to /login.html             │
│  ├─ GET /login.html    → Serve login page                    │
│  └─ GET /index.html    → Serve dashboard                     │
│                                                               │
│  Authentication API:                                          │
│  ├─ POST /api/login           → Validate & generate token    │
│  ├─ POST /api/logout          → Invalidate session           │
│  └─ GET /api/verify-session   → Check token validity         │
│                                                               │
│  Data API:                                                    │
│  ├─ GET /api/calls            → Fetch calls from DB          │
│  ├─ GET /api/leads            → Fetch leads from DB          │
│  ├─ GET /api/appointments     → Fetch appointments from DB   │
│  ├─ GET /api/stats            → Fetch statistics from DB     │
│  └─ GET /api/calls/{id}       → Fetch call details from DB   │
│                                                               │
│  Voice API:                                                   │
│  ├─ POST /incoming-call       → Twilio webhook               │
│  └─ WebSocket /media-stream   → Real-time audio             │
│                                                               │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Database queries
             ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (Aiven)                     │
│  pg-1c535dfd-madhavchaturvedimac-9806.j.aivencloud.com      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Tables:                                                      │
│  ├─ calls (13 records)                                       │
│  │  └─ id, call_sid, caller_phone, status, intent,          │
│  │     started_at, ended_at, duration_seconds, etc.          │
│  │                                                            │
│  ├─ leads (2 records)                                        │
│  │  └─ id, call_id, name, phone, email, lead_score,         │
│  │     budget_indication, timeline, etc.                     │
│  │                                                            │
│  ├─ appointments (6 records)                                 │
│  │  └─ id, call_id, customer_name, customer_phone,          │
│  │     appointment_datetime, service_type, status, etc.      │
│  │                                                            │
│  └─ transcripts                                              │
│     └─ id, call_id, speaker, text, timestamp_ms, etc.        │
│                                                               │
│  Connection Pool:                                             │
│  ├─ Min connections: 1                                       │
│  ├─ Max connections: 3                                       │
│  └─ SSL Mode: require                                        │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌──────────┐
│ Browser  │
└────┬─────┘
     │
     │ 1. Visit http://localhost:5050/
     ↓
┌────────────────┐
│  GET /         │
│  Redirect 307  │
└────┬───────────┘
     │
     │ 2. Redirect to /login.html
     ↓
┌─────────────────────┐
│  GET /login.html    │
│  FileResponse       │
│  (login page HTML)  │
└────┬────────────────┘
     │
     │ 3. User enters: madhav5 / M@dhav0505@#
     ↓
┌──────────────────────────────┐
│  POST /api/login             │
│  {username, password}        │
│  ↓                           │
│  Validate credentials        │
│  ↓                           │
│  Generate session token      │
│  ↓                           │
│  Store in active_sessions{}  │
│  ↓                           │
│  Return {token, username}    │
└────┬─────────────────────────┘
     │
     │ 4. Save to localStorage
     │ 5. Redirect to /index.html
     ↓
┌─────────────────────────┐
│  GET /index.html        │
│  FileResponse           │
│  (dashboard HTML)       │
│  ↓                      │
│  JavaScript executes:   │
│  - Get token            │
│  - Verify session       │
└────┬────────────────────┘
     │
     │ 6. Verify token
     ↓
┌──────────────────────────────┐
│  GET /api/verify-session     │
│  ?token=xxx                  │
│  ↓                           │
│  Check active_sessions{}     │
│  ↓                           │
│  Return {valid: true}        │
└────┬─────────────────────────┘
     │
     │ 7. Token valid → Load dashboard
     ↓
┌──────────────────────────────┐
│  Dashboard loads data:       │
│  ├─ GET /api/stats           │
│  ├─ GET /api/calls           │
│  ├─ GET /api/leads           │
│  └─ GET /api/appointments    │
└──────────────────────────────┘
```

## Data Flow (Dashboard)

```
┌─────────────────────────────────────────────────────────────┐
│                      Dashboard (index.html)                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  On Page Load:                                                │
│  1. Check authentication                                      │
│  2. Fetch statistics                                          │
│  3. Fetch recent calls                                        │
│  4. Fetch recent leads                                        │
│  5. Fetch upcoming appointments                               │
│  6. Render charts and tables                                  │
│                                                               │
└────────────┬────────────────────────────────────────────────┘
             │
             │ API Requests
             ↓
┌─────────────────────────────────────────────────────────────┐
│                    API Endpoints (main.py)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  GET /api/stats:                                              │
│  ├─ Query: SELECT COUNT(*) FROM calls                        │
│  ├─ Query: SELECT COUNT(*) FROM leads                        │
│  ├─ Query: SELECT COUNT(*) FROM appointments                 │
│  └─ Return: {total_calls, new_leads, appointments}           │
│                                                               │
│  GET /api/calls:                                              │
│  ├─ Query: SELECT * FROM calls ORDER BY started_at DESC      │
│  └─ Return: [{id, caller_phone, status, intent, ...}]        │
│                                                               │
│  GET /api/leads:                                              │
│  ├─ Query: SELECT * FROM leads ORDER BY created_at DESC      │
│  └─ Return: [{id, name, phone, lead_score, ...}]             │
│                                                               │
│  GET /api/appointments:                                       │
│  ├─ Query: SELECT * FROM appointments WHERE datetime >= NOW  │
│  └─ Return: [{id, customer_name, datetime, ...}]             │
│                                                               │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Database Queries
             ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database (Aiven)                     │
│                                                               │
│  Connection Pool (1-3 connections):                           │
│  ├─ Connection 1: Active query                               │
│  ├─ Connection 2: Idle                                       │
│  └─ Connection 3: Available                                  │
│                                                               │
│  Returns data:                                                │
│  ├─ 13 calls                                                 │
│  ├─ 2 leads                                                  │
│  └─ 6 appointments                                           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Voice Call Flow

```
┌──────────────┐
│  Phone Call  │
└──────┬───────┘
       │
       │ Incoming call
       ↓
┌──────────────────┐
│  Twilio          │
│  Voice Service   │
└──────┬───────────┘
       │
       │ POST /incoming-call
       ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (main.py)                        │
│                                                               │
│  1. Receive call webhook                                      │
│  2. Create call record in database                            │
│  3. Detect intent (CallManager)                               │
│  4. Detect language (LanguageManager)                         │
│  5. Route call (CallRouter)                                   │
│  6. Connect to OpenAI Realtime API                            │
│  7. Stream audio via WebSocket                                │
│  8. Save transcript to database                               │
│  9. Update call status                                        │
│  10. Create lead/appointment if applicable                    │
│                                                               │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Save to database
             ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL Database                             │
│                                                               │
│  New records created:                                         │
│  ├─ calls table: New call record                             │
│  ├─ transcripts table: Conversation turns                    │
│  ├─ leads table: If sales inquiry                            │
│  └─ appointments table: If booking made                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### Frontend
- `frontend/login.html` - Login page with authentication
- `frontend/index.html` - Dashboard with tabs (Overview, Calls, Leads, Appointments)
- `frontend/dashboard.js` - Dashboard logic and API calls

### Backend
- `main.py` - FastAPI server with routes and WebSocket
- `database.py` - PostgreSQL connection and queries
- `call_manager.py` - Call handling and management
- `intent_detector.py` - Intent detection using OpenAI
- `language_manager.py` - Multi-language support
- `appointment_manager.py` - Appointment booking logic
- `lead_manager.py` - Lead capture and scoring

### Database
- PostgreSQL on Aiven Cloud
- Connection pool: 1-3 connections
- SSL required
- Tables: calls, leads, appointments, transcripts

### Authentication
- Session-based with in-memory storage
- Token generation and validation
- Login/logout endpoints
- Protected dashboard routes

## Connection Limits

### Aiven Free Tier
- Max connections: 3-5
- Connection timeout: 30 seconds
- Idle timeout: 5 minutes

### Application Pool
- Min connections: 1
- Max connections: 3
- Fits within Aiven limits
- Prevents "too many clients" error

## Security Notes

### Current (Development)
- Hardcoded credentials
- In-memory session storage
- No HTTPS
- No rate limiting

### Production Recommendations
- Database-backed user management
- Hashed passwords (bcrypt)
- Redis for session storage
- HTTPS/TLS encryption
- Rate limiting
- CSRF protection
- Session expiration
- Refresh tokens
