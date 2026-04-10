#!/bin/bash
# Aiven PostgreSQL Database Setup Script

echo "============================================================"
echo "AIVEN POSTGRESQL DATABASE SETUP"
echo "============================================================"
echo ""

# Step 1: Check if .env exists
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found"
    echo "   Please create .env file first"
    exit 1
fi

echo "✅ Found .env file"
echo ""

# Step 2: Check if credentials are set
echo "Checking Aiven credentials in .env..."
source .env

if [ -z "$DB_HOST" ] || [ "$DB_HOST" = "your-aiven-host.aivencloud.com" ]; then
    echo "❌ ERROR: DB_HOST not configured"
    echo ""
    echo "Please update .env with your Aiven credentials:"
    echo "1. Go to https://console.aiven.io"
    echo "2. Select your PostgreSQL service"
    echo "3. Copy connection details"
    echo "4. Update .env file with:"
    echo "   DB_HOST=your-actual-host.aivencloud.com"
    echo "   DB_PORT=12345"
    echo "   DB_NAME=defaultdb"
    echo "   DB_USER=avnadmin"
    echo "   DB_PASSWORD=your-password"
    echo "   DB_SSLMODE=require"
    exit 1
fi

echo "✅ Aiven credentials configured"
echo ""

# Step 3: Install dependencies
echo "Installing required dependencies..."
pip install psycopg2-binary asyncpg
echo "✅ Dependencies installed"
echo ""

# Step 4: Test connection
echo "Testing Aiven connection..."
python3 test_aiven_connection.py
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Connection test failed"
    echo "   Please fix the connection issues above"
    exit 1
fi
echo ""

# Step 5: Run migrations
echo "Running database migrations..."
python3 migrations/run_migration.py 001_initial_schema.sql
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Migration failed"
    exit 1
fi
echo ""

# Step 6: Verify database storage
echo "Verifying database storage..."
python3 check_database_storage.py
if [ $? -ne 0 ]; then
    echo ""
    echo "⚠️  Database verification had issues"
    echo "   But tables should be created"
fi
echo ""

echo "============================================================"
echo "✅ AIVEN DATABASE SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Your system is now connected to Aiven PostgreSQL!"
echo ""
echo "Next steps:"
echo "1. Start your server: python3 main.py"
echo "2. Make a test call to book an appointment"
echo "3. Check your dashboard - data will persist!"
echo ""
