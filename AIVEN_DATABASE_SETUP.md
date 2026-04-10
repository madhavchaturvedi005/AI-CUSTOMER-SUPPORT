# Aiven PostgreSQL Database Setup Guide

## Current Status
Your system is configured to use a real database (`USE_REAL_DB=true`) but the Aiven connection details need to be filled in.

## Step 1: Get Aiven Connection Details

1. Log in to your Aiven console: https://console.aiven.io
2. Select your PostgreSQL service
3. Go to the "Overview" tab
4. Copy the connection information

You'll see something like:
```
Host: pg-xxxxx-yyyy.aivencloud.com
Port: 12345
User: avnadmin
Password: your-password-here
Database: defaultdb
SSL Mode: require
```

## Step 2: Update .env File

Open your `.env` file and replace the placeholder values:

```bash
# Database Configuration
USE_REAL_DB=true

# Aiven PostgreSQL Connection
DB_HOST=pg-xxxxx-yyyy.aivencloud.com    # Replace with your Aiven host
DB_PORT=12345                            # Replace with your Aiven port
DB_NAME=defaultdb                        # Usually defaultdb for Aiven
DB_USER=avnadmin                         # Usually avnadmin for Aiven
DB_PASSWORD=your-actual-password         # Replace with your Aiven password
DB_SSLMODE=require                       # Keep as 'require' for Aiven
```

## Step 3: Install Required Dependencies

Make sure you have the PostgreSQL adapter installed:

```bash
pip install psycopg2-binary
```

Or if you prefer the compiled version:

```bash
pip install psycopg2
```

## Step 4: Run Database Migrations

Once your `.env` is configured, create the database tables:

```bash
python3 migrations/run_migration.py 001_initial_schema.sql
```

This will create:
- `calls` table - Stores call records
- `appointments` table - Stores booked appointments
- `leads` table - Stores customer leads
- `transcripts` table - Stores call transcripts

## Step 5: Verify Database Connection

Run the diagnostic script to verify everything is working:

```bash
python3 check_database_storage.py
```

You should see:
- ✅ Database connection successful
- ✅ All tables exist
- ✅ Test appointment creation works
- ✅ Test lead creation works

## Step 6: Restart Your Server

```bash
python3 main.py
```

## Troubleshooting

### SSL Connection Error
If you get SSL errors, make sure `DB_SSLMODE=require` is set in your `.env` file.

### Connection Timeout
- Check that your Aiven service is running
- Verify your IP is whitelisted in Aiven (if IP filtering is enabled)
- Check firewall settings

### Authentication Failed
- Double-check your password in `.env`
- Make sure there are no extra spaces in the password
- Verify the username is correct (usually `avnadmin`)

### Database Does Not Exist
- Aiven usually creates a default database called `defaultdb`
- Check your Aiven console for the correct database name

## What Happens After Setup

Once connected:

1. **Phone calls** → AI books appointments → Saved to Aiven PostgreSQL
2. **Dashboard** → Fetches real data from Aiven PostgreSQL
3. **Data persists** → Survives server restarts
4. **Real-time updates** → Dashboard refreshes when new appointments are booked

## Testing the Full Flow

1. Make a test call to your Twilio number
2. Say: "I want to book an appointment for tomorrow at 2pm"
3. AI will book the appointment
4. Check your dashboard - appointment should appear
5. Restart server - appointment still there (persisted in Aiven!)

## Need Help?

If you encounter issues:
1. Check `.env` file for typos
2. Run `python3 check_database_storage.py` for diagnostics
3. Check Aiven console to verify service is running
4. Review server logs for connection errors
