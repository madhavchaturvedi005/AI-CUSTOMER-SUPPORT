#!/bin/bash

# Setup script for AI Voice Automation Database Integration

echo "🚀 AI Voice Automation - Database Setup"
echo "========================================"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed"
    echo "   Install with: brew install postgresql"
    exit 1
fi

echo "✅ PostgreSQL is installed"

# Check if Redis is installed
if ! command -v redis-cli &> /dev/null; then
    echo "❌ Redis is not installed"
    echo "   Install with: brew install redis"
    exit 1
fi

echo "✅ Redis is installed"

# Start PostgreSQL
echo ""
echo "Starting PostgreSQL..."
brew services start postgresql
sleep 2

# Start Redis
echo "Starting Redis..."
brew services start redis
sleep 2

# Create database if it doesn't exist
echo ""
echo "Creating database..."
createdb voice_automation 2>/dev/null || echo "   Database already exists"

# Run migrations
echo ""
echo "Running database migrations..."
python3 migrations/run_migration.py

# Update .env file
echo ""
echo "Configuring environment..."

if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Twilio Configuration
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_phone_number

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
USE_REAL_DB=true
DB_HOST=localhost
DB_PORT=5432
DB_NAME=voice_automation
DB_USER=postgres
DB_PASSWORD=

# Redis Configuration
USE_REAL_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379

# Server Configuration
PORT=5050
TEMPERATURE=0.8
EOF
    echo "✅ Created .env file (please update with your credentials)"
else
    # Update existing .env file
    if ! grep -q "USE_REAL_DB" .env; then
        echo "" >> .env
        echo "# Database Configuration" >> .env
        echo "USE_REAL_DB=true" >> .env
        echo "DB_HOST=localhost" >> .env
        echo "DB_PORT=5432" >> .env
        echo "DB_NAME=voice_automation" >> .env
        echo "DB_USER=postgres" >> .env
        echo "DB_PASSWORD=" >> .env
        echo "" >> .env
        echo "# Redis Configuration" >> .env
        echo "USE_REAL_REDIS=true" >> .env
        echo "REDIS_HOST=localhost" >> .env
        echo "REDIS_PORT=6379" >> .env
    fi
    echo "✅ Updated .env file with database configuration"
fi

echo ""
echo "========================================"
echo "✅ Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your Twilio and OpenAI credentials"
echo "2. Start the server: python3 main.py"
echo "3. Open dashboard: http://localhost:5050/frontend/index.html"
echo ""
echo "To use demo mode (mock data), set USE_REAL_DB=false in .env"
echo ""
