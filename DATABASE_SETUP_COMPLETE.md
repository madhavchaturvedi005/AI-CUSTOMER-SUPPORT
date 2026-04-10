# Database Setup - Ready for Aiven PostgreSQL

## Current Status

✅ System configured for real database (`USE_REAL_DB=true`)  
⚠️ Aiven credentials need to be added to `.env`  
✅ Required dependencies added to `requirements.txt`  
✅ Test scripts created  
✅ Setup automation ready  

## What You Need to Do

### 1. Get Your Aiven Credentials

Go to your Aiven console and copy your PostgreSQL connection details:
- Host (e.g., `pg-xxxxx.aivencloud.com`)
- Port (e.g., `12345`)
- Database name (usually `defaultdb`)
- Username (usually `avnadmin`)
- Password

### 2. Update .env File

Open `.env` and replace the placeholder values:

```bash
DB_HOST=pg-xxxxx.aivencloud.com    # Your actual Aiven host
DB_PORT=12345                       # Your actual port
DB_NAME=defaultdb                   # Your database name
DB_USER=avnadmin                    # Your username
DB_PASSWORD=your-actual-password    # Your password
DB_SSLMODE=require                  # Keep as 'require'
```

### 3. Run Setup Script

Once credentials are added, run:

```bash
./setup_aiven_database.sh
```

This will:
1. ✅ Verify credentials are set
2. ✅ Install dependencies (`psycopg2-binary`)
3. ✅ Test Aiven connection
4. ✅ Run database migrations (create tables)
5. ✅ Verify everything works

### 4. Manual Setup (Alternative)

If you prefer manual steps:

```bash
# Install dependencies
pip install psycopg2-binary

# Test connection
python3 test_aiven_connection.py

# Run migrations
python3 migrations/run_migration.py 001_initial_schema.sql

# Verify storage
python3 check_database_storage.py
```

## What Gets Created

The migration creates these tables in your Aiven database:

1. **calls** - Stores all phone call records
2. **appointments** - Stores booked appointments
3. **leads** - Stores customer leads
4. **transcripts** - Stores call transcripts

## After Setup

Once connected, your system will:

✅ Save appointments to Aiven PostgreSQL (persistent)  
✅ Save leads to Aiven PostgreSQL (persistent)  
✅ Dashboard shows real data from Aiven  
✅ Data survives server restarts  
✅ Real-time updates work automatically  

## Testing the Full Flow

1. Start server: `python3 main.py`
2. Call your Twilio number
3. Say: "I want to book an appointment for tomorrow at 2pm"
4. AI books appointment → Saved to Aiven
5. Dashboard refreshes → Shows appointment
6. Restart server → Appointment still there!

## Files Created

- `AIVEN_DATABASE_SETUP.md` - Detailed setup guide
- `test_aiven_connection.py` - Test Aiven connection
- `setup_aiven_database.sh` - Automated setup script
- `requirements.txt` - Updated with `psycopg2-binary`
- `.env` - Updated with Aiven placeholders

## Troubleshooting

### Connection fails?
- Verify credentials in Aiven console
- Check if service is running
- Verify IP whitelisting (if enabled)
- Ensure `DB_SSLMODE=require`

### Migration fails?
- Make sure connection test passes first
- Check database permissions
- Verify user has CREATE TABLE rights

### Data not saving?
- Run `python3 check_database_storage.py`
- Check server logs for errors
- Verify `USE_REAL_DB=true` in `.env`

## Need Help?

Run diagnostics:
```bash
python3 check_database_storage.py
```

This shows:
- Database connection status
- Tables existence
- Sample data
- Test operations

## Summary

Your system is ready for Aiven PostgreSQL! Just add your credentials to `.env` and run the setup script. Once connected, all appointments and leads will be stored persistently in the cloud.
