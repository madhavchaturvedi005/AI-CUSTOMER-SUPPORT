# Quick Start Guide

## Prerequisites
- Python 3.8+
- PostgreSQL database (Aiven configured)
- Redis (optional, will use in-memory if not available)

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment
Check `.env` file has:
```env
USE_REAL_DB=true
DATABASE_URL=postgres://...
DB_HOST=pg-1c535dfd-madhavchaturvedimac-9806.j.aivencloud.com
DB_PORT=14641
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=AVNS_35aiv44hUxwJ9Kq_eE5
DB_SSLMODE=require
```

## Step 3: Test Database Connection
```bash
python3 -c "
import asyncio
from database import initialize_database

async def test():
    db = await initialize_database()
    print('✅ Database connected')
    await db.disconnect()

asyncio.run(test())
"
```

## Step 4: Start the Server
```bash
python3 main.py
```

Expected output:
```
🚀 Initializing AI Voice Automation services...
   ✅ Connected to PostgreSQL database
   ✅ Connected to Redis cache
   • CallManager: Ready
   • IntentDetector: Ready
   • LanguageManager: Ready
   • CallRouter: Ready
   • AppointmentManager: Ready (tool calling enabled)
   • Database: PostgreSQL
   • Cache: Redis

============================================================
🎙️  AI Voice Automation Server
============================================================
   Server: http://localhost:5050
   Twilio Webhook: http://your-domain/incoming-call
   Dashboard: http://localhost:5050/
============================================================
```

## Step 5: Access Dashboard
1. Open browser: `http://localhost:5050/`
2. Login:
   - Username: `madhav5`
   - Password: `M@dhav0505@#`
3. View dashboard with real data

## Step 6: Test API (Optional)
```bash
# In another terminal
python3 test_api_endpoints.py
```

## Common Issues

### "too many clients already"
- Stop server (Ctrl+C)
- Wait 30 seconds
- Restart server

### Mock data showing instead of real data
- Check `.env` has `USE_REAL_DB=true`
- Check server logs for database connection errors
- Verify database credentials

### Login page not found
- Make sure server is running
- Access: `http://localhost:5050/` (not `/frontend/login.html`)

### Dashboard shows no data
- Check database has data: `python3 check_db_tables.py`
- Check API endpoints: `curl http://localhost:5050/api/calls`
- Check browser console (F12) for errors

## Testing Checklist

- [ ] Database connects successfully
- [ ] Server starts without errors
- [ ] Login page loads at `http://localhost:5050/`
- [ ] Can login with credentials
- [ ] Dashboard shows real data (not mock)
- [ ] Calls tab shows actual calls
- [ ] Leads tab shows actual leads
- [ ] Appointments tab shows actual appointments
- [ ] View button works on calls
- [ ] Logout works

## Next Steps

1. Configure Twilio webhook
2. Make test calls
3. Verify data appears in dashboard
4. Test appointment booking
5. Test lead capture
6. Review analytics

## Support Files

- `DATABASE_FIX_SUMMARY.md` - Database connection fix details
- `LOGIN_SYSTEM_GUIDE.md` - Login system documentation
- `test_api_endpoints.py` - API testing script
- `test_login_routes.py` - Login route testing script
