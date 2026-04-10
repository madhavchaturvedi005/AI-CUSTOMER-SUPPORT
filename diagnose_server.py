#!/usr/bin/env python3
"""
Comprehensive server diagnostics to identify why calls aren't being created.
"""

import os
import sys
import asyncio
import subprocess
from datetime import datetime

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def check_env_file():
    """Check if .env file exists and has required variables."""
    print_section("1. ENVIRONMENT CONFIGURATION")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return False
    
    print("✅ .env file exists")
    
    # Read and check key variables
    with open('.env', 'r') as f:
        env_content = f.read()
    
    required_vars = ['OPENAI_API_KEY', 'PORT', 'USE_REAL_DB', 'DB_HOST']
    missing = []
    
    for var in required_vars:
        if var in env_content:
            # Get the value
            for line in env_content.split('\n'):
                if line.startswith(var):
                    value = line.split('=', 1)[1] if '=' in line else ''
                    if value.strip():
                        print(f"✅ {var} is set")
                    else:
                        print(f"⚠️  {var} is empty")
                        missing.append(var)
                    break
        else:
            print(f"❌ {var} is missing")
            missing.append(var)
    
    return len(missing) == 0

def check_port():
    """Check if port 5050 is available or in use."""
    print_section("2. PORT AVAILABILITY")
    
    try:
        result = subprocess.run(
            ['lsof', '-i', ':5050'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout:
            print("⚠️  Port 5050 is IN USE:")
            print(result.stdout)
            print("\n💡 This could mean:")
            print("   1. Server is already running (good!)")
            print("   2. Another process is using the port (bad!)")
            return True
        else:
            print("✅ Port 5050 is AVAILABLE")
            print("⚠️  This means the server is NOT running")
            return False
    except FileNotFoundError:
        print("⚠️  'lsof' command not found, skipping port check")
        return None

def check_database():
    """Check if PostgreSQL is running and accessible."""
    print_section("3. DATABASE CONNECTION")
    
    try:
        result = subprocess.run(
            ['psql', '-U', 'madhavchaturvedi', '-d', 'voice_automation', '-c', 'SELECT 1;'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ PostgreSQL is running and accessible")
            return True
        else:
            print("❌ Cannot connect to PostgreSQL")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ PostgreSQL connection timeout")
        return False
    except FileNotFoundError:
        print("⚠️  'psql' command not found")
        return None

def check_ngrok():
    """Check if ngrok is running."""
    print_section("4. NGROK STATUS")
    
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'ngrok'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ ngrok is running")
            print(f"   Process ID: {result.stdout.strip()}")
            return True
        else:
            print("❌ ngrok is NOT running")
            return False
    except FileNotFoundError:
        print("⚠️  'pgrep' command not found")
        return None

def check_server_process():
    """Check if main.py is running."""
    print_section("5. SERVER PROCESS")
    
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'main.py'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ main.py is running")
            print(f"   Process ID: {result.stdout.strip()}")
            return True
        else:
            print("❌ main.py is NOT running")
            return False
    except FileNotFoundError:
        print("⚠️  'pgrep' command not found")
        return None

async def test_health_endpoint():
    """Test if the /health endpoint responds."""
    print_section("6. HEALTH ENDPOINT TEST")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:5050/health', timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ Server is responding!")
                        print(f"   Status: {data.get('status')}")
                        print(f"   Database: {data.get('database')}")
                        print(f"   Redis: {data.get('redis')}")
                        return True
                    else:
                        print(f"⚠️  Server responded with status {response.status}")
                        return False
            except asyncio.TimeoutError:
                print("❌ Health endpoint timeout (server not responding)")
                return False
            except aiohttp.ClientConnectorError:
                print("❌ Cannot connect to server (server not running)")
                return False
    except ImportError:
        print("⚠️  aiohttp not installed, skipping health check")
        print("   Install with: pip install aiohttp")
        return None

def print_recommendations(results):
    """Print recommendations based on diagnostic results."""
    print_section("RECOMMENDATIONS")
    
    env_ok, port_in_use, db_ok, ngrok_ok, server_ok, health_ok = results
    
    if not server_ok:
        print("🔴 CRITICAL: Server is not running!")
        print("\n📋 To start the server:")
        print("   1. Open a terminal")
        print("   2. Run: python3 main.py")
        print("   3. Wait for: 'INFO: Uvicorn running on http://0.0.0.0:5050'")
        print("   4. Keep this terminal open")
        return
    
    if not health_ok:
        print("🔴 CRITICAL: Server is running but not responding!")
        print("\n📋 To fix:")
        print("   1. Stop the server (Ctrl+C)")
        print("   2. Check for errors in the terminal")
        print("   3. Restart: python3 main.py")
        return
    
    if not ngrok_ok:
        print("⚠️  WARNING: ngrok is not running")
        print("\n📋 To start ngrok:")
        print("   1. Open a NEW terminal")
        print("   2. Run: ngrok http 5050")
        print("   3. Copy the https URL")
        print("   4. Update Twilio webhook to: https://YOUR-URL.ngrok-free.dev/incoming-call")
        return
    
    if not db_ok:
        print("⚠️  WARNING: Database connection issue")
        print("\n📋 To fix:")
        print("   1. Check if PostgreSQL is running")
        print("   2. Verify credentials in .env file")
        print("   3. Test connection: psql -U madhavchaturvedi -d voice_automation")
        return
    
    print("✅ All systems operational!")
    print("\n📋 Next steps:")
    print("   1. Make a test call to your Twilio number")
    print("   2. Watch the server terminal for logs")
    print("   3. You should see: '📞 /incoming-call endpoint HIT!'")
    print("   4. Then: '✅ Call created in database'")

async def main():
    """Run all diagnostics."""
    print("\n" + "🔍 SERVER DIAGNOSTICS".center(60))
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run checks
    env_ok = check_env_file()
    port_in_use = check_port()
    db_ok = check_database()
    ngrok_ok = check_ngrok()
    server_ok = check_server_process()
    health_ok = await test_health_endpoint()
    
    # Print summary
    print_section("SUMMARY")
    print(f"Environment Config: {'✅' if env_ok else '❌'}")
    print(f"Port 5050 Status: {'IN USE' if port_in_use else 'AVAILABLE'}")
    print(f"Database: {'✅' if db_ok else '❌' if db_ok is False else '⚠️'}")
    print(f"ngrok: {'✅' if ngrok_ok else '❌' if ngrok_ok is False else '⚠️'}")
    print(f"Server Process: {'✅' if server_ok else '❌' if server_ok is False else '⚠️'}")
    print(f"Health Endpoint: {'✅' if health_ok else '❌' if health_ok is False else '⚠️'}")
    
    # Print recommendations
    print_recommendations((env_ok, port_in_use, db_ok, ngrok_ok, server_ok, health_ok))
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(main())
