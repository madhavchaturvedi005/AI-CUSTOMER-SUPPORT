#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot ngrok and server connectivity issues.

This script helps identify why Twilio can't reach the /incoming-call endpoint.
"""

import asyncio
import os
import sys
import subprocess
import requests
from datetime import datetime

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_info(text):
    print(f"ℹ️  {text}")

def check_server_running():
    """Check if the FastAPI server is running on port 5050."""
    print_header("1. Checking if FastAPI server is running")
    
    try:
        response = requests.get("http://localhost:5050/health", timeout=5)
        if response.status_code == 200:
            print_success("Server is running on port 5050")
            print_info(f"Response: {response.json()}")
            return True
        else:
            print_error(f"Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Server is NOT running on port 5050")
        print_info("Start the server with: python main.py")
        return False
    except Exception as e:
        print_error(f"Error checking server: {e}")
        return False

def check_incoming_call_endpoint():
    """Check if /incoming-call endpoint is accessible locally."""
    print_header("2. Checking /incoming-call endpoint")
    
    try:
        response = requests.get("http://localhost:5050/incoming-call", timeout=5)
        # We expect a 405 (Method Not Allowed) or 200 for GET
        # The endpoint accepts both GET and POST
        if response.status_code in [200, 405]:
            print_success("/incoming-call endpoint is accessible")
            print_info(f"Status: {response.status_code}")
            return True
        else:
            print_error(f"Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Cannot reach /incoming-call endpoint")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def check_ngrok_running():
    """Check if ngrok is running."""
    print_header("3. Checking if ngrok is running")
    
    try:
        # Try to access ngrok's local API
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            if not tunnels:
                print_warning("ngrok is running but no tunnels found")
                print_info("Start ngrok with: ngrok http 5050")
                return False
            
            print_success("ngrok is running")
            for tunnel in tunnels:
                public_url = tunnel.get('public_url', '')
                config = tunnel.get('config', {})
                addr = config.get('addr', '')
                print_info(f"Tunnel: {public_url} -> {addr}")
            
            return True, tunnels
        else:
            print_error("ngrok API returned unexpected status")
            return False, []
    except requests.exceptions.ConnectionError:
        print_error("ngrok is NOT running")
        print_info("Start ngrok with: ngrok http 5050")
        return False, []
    except Exception as e:
        print_error(f"Error checking ngrok: {e}")
        return False, []

def test_ngrok_url(ngrok_url):
    """Test if the ngrok URL is accessible."""
    print_header("4. Testing ngrok URL accessibility")
    
    # Test health endpoint
    print_info(f"Testing: {ngrok_url}/health")
    try:
        response = requests.get(f"{ngrok_url}/health", timeout=10)
        if response.status_code == 200:
            print_success("ngrok URL is accessible")
            print_info(f"Response: {response.json()}")
        else:
            print_error(f"ngrok URL returned status {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Cannot reach ngrok URL: {e}")
        return False
    
    # Test incoming-call endpoint
    print_info(f"Testing: {ngrok_url}/incoming-call")
    try:
        response = requests.get(f"{ngrok_url}/incoming-call", timeout=10)
        if response.status_code in [200, 405]:
            print_success("/incoming-call endpoint is accessible via ngrok")
            return True
        else:
            print_error(f"Unexpected status: {response.status_code}")
            print_info(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def check_twilio_webhook():
    """Display Twilio webhook configuration instructions."""
    print_header("5. Twilio Webhook Configuration")
    
    print_info("Your Twilio webhook should be configured as:")
    print(f"   {YELLOW}https://YOUR-NGROK-URL/incoming-call{RESET}")
    print()
    print_info("To update Twilio webhook:")
    print("   1. Go to: https://console.twilio.com/")
    print("   2. Navigate to: Phone Numbers > Manage > Active Numbers")
    print("   3. Click on your phone number")
    print("   4. Scroll to 'Voice Configuration'")
    print("   5. Set 'A CALL COMES IN' webhook to your ngrok URL + /incoming-call")
    print("   6. Make sure HTTP method is set to 'POST'")
    print("   7. Click 'Save'")

def main():
    """Run all diagnostic checks."""
    print(f"\n{BLUE}╔{'═'*58}╗{RESET}")
    print(f"{BLUE}║{' '*15}NGROK DIAGNOSTIC TOOL{' '*22}║{RESET}")
    print(f"{BLUE}╚{'═'*58}╝{RESET}")
    print(f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Step 1: Check server
    server_ok = check_server_running()
    
    if not server_ok:
        print_header("DIAGNOSIS")
        print_error("Server is not running!")
        print_info("Fix: Run 'python main.py' in a terminal")
        sys.exit(1)
    
    # Step 2: Check endpoint
    endpoint_ok = check_incoming_call_endpoint()
    
    if not endpoint_ok:
        print_header("DIAGNOSIS")
        print_error("Endpoint is not accessible!")
        print_info("This is unusual if the server is running. Check for errors in server logs.")
        sys.exit(1)
    
    # Step 3: Check ngrok
    ngrok_result = check_ngrok_running()
    
    if isinstance(ngrok_result, tuple):
        ngrok_ok, tunnels = ngrok_result
    else:
        ngrok_ok = ngrok_result
        tunnels = []
    
    if not ngrok_ok:
        print_header("DIAGNOSIS")
        print_error("ngrok is not running!")
        print_info("Fix: Run 'ngrok http 5050' in a separate terminal")
        sys.exit(1)
    
    # Step 4: Test ngrok URL
    if tunnels:
        # Find HTTPS tunnel
        https_tunnel = None
        for tunnel in tunnels:
            if tunnel.get('public_url', '').startswith('https://'):
                https_tunnel = tunnel
                break
        
        if https_tunnel:
            ngrok_url = https_tunnel['public_url']
            url_ok = test_ngrok_url(ngrok_url)
            
            if not url_ok:
                print_header("DIAGNOSIS")
                print_error("ngrok URL is not forwarding correctly!")
                print_info("Possible issues:")
                print("   • ngrok might be forwarding to wrong port")
                print("   • Server might have restarted")
                print("   • Network connectivity issue")
                print()
                print_info("Try restarting ngrok: ngrok http 5050")
                sys.exit(1)
        else:
            print_warning("No HTTPS tunnel found")
    
    # Step 5: Show Twilio configuration
    check_twilio_webhook()
    
    # Final summary
    print_header("SUMMARY")
    print_success("All checks passed!")
    print()
    print_info("Your setup is working correctly:")
    print(f"   • Server: {GREEN}Running{RESET} on http://localhost:5050")
    print(f"   • ngrok: {GREEN}Running{RESET}")
    
    if tunnels:
        for tunnel in tunnels:
            if tunnel.get('public_url', '').startswith('https://'):
                ngrok_url = tunnel['public_url']
                print(f"   • Public URL: {GREEN}{ngrok_url}{RESET}")
                print()
                print_info("Update your Twilio webhook to:")
                print(f"   {YELLOW}{ngrok_url}/incoming-call{RESET}")
    
    print()
    print_success("You're ready to receive calls!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Diagnostic cancelled by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Unexpected error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
