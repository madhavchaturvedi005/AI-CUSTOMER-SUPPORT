import os
import asyncio
import websockets
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

print("=" * 60)
print("DIAGNOSTIC CHECK")
print("=" * 60)

# Check 1: API Key
print("\n1. Checking OpenAI API Key...")
if not OPENAI_API_KEY:
    print("   ❌ OPENAI_API_KEY not found in .env file")
    exit(1)
elif OPENAI_API_KEY == 'your_api_key':
    print("   ❌ OPENAI_API_KEY is still the placeholder value")
    print("   Please update .env with your real OpenAI API key")
    exit(1)
else:
    print(f"   ✓ API Key found (starts with: {OPENAI_API_KEY[:10]}...)")

# Check 2: Test WebSocket connection to OpenAI
print("\n2. Testing WebSocket connection to OpenAI Realtime API...")
async def test_openai_connection():
    try:
        uri = "wss://api.openai.com/v1/realtime?model=gpt-realtime&temperature=0.8"
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
        
        print("   Connecting to OpenAI WebSocket...")
        async with websockets.connect(uri, additional_headers=headers) as ws:
            print("   ✓ Successfully connected to OpenAI WebSocket!")
            
            # Send session update
            session_update = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": "Test connection"
                }
            }
            
            import json
            await ws.send(json.dumps(session_update))
            print("   ✓ Sent session update")
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            print("   ✓ Received response from OpenAI")
            print(f"   Response: {response[:100]}...")
            
            return True
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"   ❌ Connection failed with status code: {e.status_code}")
        if e.status_code == 401:
            print("   → Invalid API key or unauthorized")
        elif e.status_code == 403:
            print("   → Access forbidden - check if you have Realtime API access")
        elif e.status_code == 404:
            print("   → Endpoint not found - check the URL")
        return False
    except asyncio.TimeoutError:
        print("   ❌ Connection timeout - no response from OpenAI")
        return False
    except Exception as e:
        print(f"   ❌ Connection error: {type(e).__name__}: {e}")
        return False

# Run the test
try:
    result = asyncio.run(test_openai_connection())
    
    if result:
        print("\n" + "=" * 60)
        print("✓ ALL CHECKS PASSED!")
        print("=" * 60)
        print("\nYour setup should work. If calls still disconnect:")
        print("1. Check server logs for specific errors")
        print("2. Verify ngrok is running and URL is correct in Twilio")
        print("3. Make sure your phone number is verified in Twilio")
    else:
        print("\n" + "=" * 60)
        print("❌ CONNECTION TEST FAILED")
        print("=" * 60)
        print("\nPossible issues:")
        print("1. Invalid or expired OpenAI API key")
        print("2. No access to OpenAI Realtime API")
        print("3. Network/firewall blocking WebSocket connections")
        print("4. OpenAI service issues")
        
except KeyboardInterrupt:
    print("\n\nTest interrupted")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
