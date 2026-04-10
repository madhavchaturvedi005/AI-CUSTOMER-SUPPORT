#!/usr/bin/env python3
"""Quick test to verify ngrok connection and server status."""

import requests
import sys

def test_connection():
    """Test local server and ngrok URL."""
    
    print("\n" + "="*60)
    print("QUICK CONNECTION TEST")
    print("="*60 + "\n")
    
    # Test 1: Local server
    print("1. Testing local server (http://localhost:5050/health)...")
    try:
        response = requests.get("http://localhost:5050/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Local server is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Cannot connect to local server: {e}")
        print("   → Start server with: python main.py")
        return False
    
    # Test 2: ngrok
    print("\n2. Checking ngrok status...")
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            if not tunnels:
                print("   ❌ ngrok is running but no tunnels found")
                print("   → Start ngrok with: ngrok http 5050")
                return False
            
            print("   ✅ ngrok is running")
            
            # Find HTTPS tunnel
            https_url = None
            for tunnel in tunnels:
                url = tunnel.get('public_url', '')
                if url.startswith('https://'):
                    https_url = url
                    print(f"   Public URL: {url}")
            
            if not https_url:
                print("   ❌ No HTTPS tunnel found")
                return False
            
            # Test 3: ngrok URL
            print(f"\n3. Testing ngrok URL ({https_url}/health)...")
            try:
                response = requests.get(f"{https_url}/health", timeout=10)
                if response.status_code == 200:
                    print("   ✅ ngrok URL is accessible")
                    print(f"   Response: {response.json()}")
                else:
                    print(f"   ❌ ngrok URL returned status {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    return False
            except Exception as e:
                print(f"   ❌ Cannot reach ngrok URL: {e}")
                return False
            
            # Test 4: /incoming-call endpoint
            print(f"\n4. Testing /incoming-call endpoint ({https_url}/incoming-call)...")
            try:
                response = requests.get(f"{https_url}/incoming-call", timeout=10)
                # GET request should return 200 or 405 (Method Not Allowed)
                if response.status_code in [200, 405]:
                    print("   ✅ /incoming-call endpoint is accessible")
                else:
                    print(f"   ❌ Unexpected status: {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    return False
            except Exception as e:
                print(f"   ❌ Error: {e}")
                return False
            
            # Success!
            print("\n" + "="*60)
            print("✅ ALL TESTS PASSED!")
            print("="*60)
            print(f"\nYour Twilio webhook should be set to:")
            print(f"   {https_url}/incoming-call")
            print("\nTo update Twilio webhook:")
            print("   1. Go to: https://console.twilio.com/")
            print("   2. Phone Numbers > Manage > Active Numbers")
            print("   3. Click your number")
            print("   4. Set 'A CALL COMES IN' to the URL above")
            print("   5. Save")
            return True
            
    except Exception as e:
        print(f"   ❌ ngrok is not running: {e}")
        print("   → Start ngrok with: ngrok http 5050")
        return False

if __name__ == "__main__":
    try:
        success = test_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest cancelled")
        sys.exit(0)
