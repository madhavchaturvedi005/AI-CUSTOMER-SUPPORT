#!/usr/bin/env python3
"""Test static file accessibility."""

import requests

BASE_URL = "http://localhost:5050"

def test_static_files():
    print("🧪 Testing Static File Access")
    print("=" * 60)
    
    files_to_test = [
        ("/frontend/dashboard.js", "Dashboard JavaScript"),
        ("/frontend/live_events.js", "Live Events JavaScript"),
        ("/login.html", "Login Page"),
        ("/index.html", "Dashboard Page"),
    ]
    
    for path, description in files_to_test:
        print(f"\nTesting: {description}")
        print(f"   URL: {BASE_URL}{path}")
        try:
            response = requests.get(f"{BASE_URL}{path}")
            if response.status_code == 200:
                size = len(response.content)
                print(f"   ✅ Success - {size} bytes")
            else:
                print(f"   ❌ Failed - Status {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")

if __name__ == "__main__":
    print("⚠️  Make sure the server is running: python3 main.py")
    print()
    import time
    time.sleep(1)
    test_static_files()
