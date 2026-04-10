# Calls Database Storage Fix

## Issue
Calls were not being stored in the Aiven PostgreSQL database due to timezone mismatch errors.

## Root Cause
The database schema uses `TIMESTAMP` (timezone-naive) columns, but the code was passing `datetime.now(timezone.utc)` (timezone-aware) values, causing PostgreSQL to reject the inserts with the error:
```
can't subtract offset-naive and offset-aware datetimes
```

## Fix Applied

Updated `database.py` to convert all timezone-aware datetimes to naive UTC before inserting:

### 1. Fixed `create_call()` (line ~117)
```python
# Before:
datetime.now(timezone.utc)  # timezone-aware

# After:
started_at = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC
```

### 2. Fixed `update_call_status()` (line ~153)
```python
# Before:
if ended_at and ended_at.tzinfo is None:
    ended_at = ended_at.replace(tzinfo=timezone.utc)  # Adding timezone

# After:
if ended_at and ended_at.tzinfo is not None:
    ended_at = ended_at.astimezone(timezone.utc).replace(tzinfo=None)  # Remove timezone
```

### 3. Fixed `create_lead()` (line ~507)
```python
# Before:
datetime.now(timezone.utc)  # timezone-aware

# After:
created_at = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC
```

### 4. `create_appointment()` - Already Correct
Already using `datetime.utcnow()` which returns naive datetime.

## Testing

Run the test to verify:
```bash
python3 test_database_service.py
```

Expected output:
```
✅ ALL TESTS PASSED!
Database service is working correctly!
```

## What This Fixes

1. ✅ Calls will now be created in database when phone calls come in
2. ✅ Call records will appear in dashboard "Calls" tab
3. ✅ Call completion will work properly
4. ✅ Transcripts can be saved (linked to call_id)
5. ✅ Analytics will have real call data

## Next Steps

1. Restart your server:
   ```bash
   python3 main.py
   ```

2. Make a test call to your Twilio number

3. Check the dashboard - call should appear in "Calls" tab

4. Verify in database:
   ```bash
   python3 -c "
   import asyncio
   from dotenv import load_dotenv
   load_dotenv()
   
   async def check():
       from database import initialize_database
       db = await initialize_database()
       async with db.pool.acquire() as conn:
           count = await conn.fetchval('SELECT COUNT(*) FROM calls')
           print(f'Total calls: {count}')
   
   asyncio.run(check())
   "
   ```

## Database Schema Note

The database uses `TIMESTAMP` (not `TIMESTAMPTZ`) columns:
- Stores timestamps as naive UTC
- Application must convert timezone-aware to naive before inserting
- Application adds timezone info when reading (for consistency)

This is a common pattern to avoid timezone conversion issues across different database clients.
