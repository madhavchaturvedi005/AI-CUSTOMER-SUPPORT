#!/usr/bin/env python3
"""Quick test to verify login routes are working."""

import requests
import time

BASE_URL = "http://localhost:5050"

def test_routes():
    """Test the login and dashboard routes."""
    print("🧪 Testing Login Routes")
    print("=" * 60)
    
    # Test 1: Root redirect
    print("\n1. Testing root redirect (/) -> /login.html")
    try:
        response = requests.get(f"{BASE_URL}/", allow_redirects=False)
        if response.status_code == 307 and 'login.html' in response.headers.get('location', ''):
            print("   ✅ Root redirects to login.html")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Login page
    print("\n2. Testing /login.html")
    try:
        response = requests.get(f"{BASE_URL}/login.html")
        if response.status_code == 200 and 'AI Voice Automation' in response.text:
            print("   ✅ Login page loads successfully")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Dashboard page (should load but redirect via JS)
    print("\n3. Testing /index.html")
    try:
        response = requests.get(f"{BASE_URL}/index.html")
        if response.status_code == 200:
            print("   ✅ Dashboard page loads successfully")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Login API
    print("\n4. Testing /api/login")
    try:
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "madhav5", "password": "M@dhav0505@#"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('token'):
                print("   ✅ Login API works - token received")
                token = data['token']
                
                # Test 5: Verify session
                print("\n5. Testing /api/verify-session")
                verify_response = requests.get(f"{BASE_URL}/api/verify-session?token={token}")
                if verify_response.status_code == 200 and verify_response.json().get('valid'):
                    print("   ✅ Session verification works")
                else:
                    print("   ❌ Session verification failed")
            else:
                print(f"   ❌ Login failed: {data}")
        else:
            print(f"   ❌ Login API error: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")

if __name__ == "__main__":
    print("⚠️  Make sure the server is running on http://localhost:5050")
    print("   Run: python3 main.py")
    print()
    time.sleep(1)
    test_routes()
