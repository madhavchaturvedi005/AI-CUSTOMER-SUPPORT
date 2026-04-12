#!/usr/bin/env python3
"""Test API endpoints to verify database connectivity."""

import requests
import json

BASE_URL = "http://localhost:5050"

def test_api():
    print("🧪 Testing API Endpoints with Database")
    print("=" * 60)
    
    # Test 1: Login
    print("\n1. Testing Login")
    try:
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "madhav5", "password": "M@dhav0505@#"}
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            print(f"   ✅ Login successful - Token: {token[:20]}...")
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    # Test 2: Get Calls
    print("\n2. Testing GET /api/calls")
    try:
        response = requests.get(f"{BASE_URL}/api/calls")
        if response.status_code == 200:
            data = response.json()
            calls = data.get('calls', [])
            print(f"   ✅ Found {len(calls)} calls")
            if calls:
                print(f"   📞 Sample call: {calls[0].get('caller_phone')} - {calls[0].get('status')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get Leads
    print("\n3. Testing GET /api/leads")
    try:
        response = requests.get(f"{BASE_URL}/api/leads")
        if response.status_code == 200:
            data = response.json()
            leads = data.get('leads', [])
            print(f"   ✅ Found {len(leads)} leads")
            if leads:
                print(f"   👤 Sample lead: {leads[0].get('name')} - Score: {leads[0].get('lead_score')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get Appointments
    print("\n4. Testing GET /api/appointments")
    try:
        response = requests.get(f"{BASE_URL}/api/appointments")
        if response.status_code == 200:
            data = response.json()
            appointments = data.get('appointments', [])
            print(f"   ✅ Found {len(appointments)} appointments")
            if appointments:
                print(f"   📅 Sample: {appointments[0].get('customer_name')} - {appointments[0].get('service_type')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Get Stats
    print("\n5. Testing GET /api/stats")
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Stats retrieved:")
            print(f"      Total Calls: {data.get('total_calls')}")
            print(f"      New Leads: {data.get('new_leads')}")
            print(f"      Appointments: {data.get('appointments_scheduled')}")
        else:
            print(f"   ❌ Failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")

if __name__ == "__main__":
    print("⚠️  Make sure the server is running: python3 main.py")
    print()
    import time
    time.sleep(1)
    test_api()
