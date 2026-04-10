"""Check Twilio webhook configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

print("Checking Twilio Configuration...")
print("="*60)

# Check if Twilio credentials are set
twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
twilio_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_phone = os.getenv("TWILIO_PHONE_NUMBER")

if twilio_sid:
    print(f"✅ TWILIO_ACCOUNT_SID: {twilio_sid[:10]}...")
else:
    print(f"❌ TWILIO_ACCOUNT_SID: Not set")

if twilio_token:
    print(f"✅ TWILIO_AUTH_TOKEN: {twilio_token[:10]}...")
else:
    print(f"❌ TWILIO_AUTH_TOKEN: Not set")

if twilio_phone:
    print(f"✅ TWILIO_PHONE_NUMBER: {twilio_phone}")
else:
    print(f"❌ TWILIO_PHONE_NUMBER: Not set")

print("\n" + "="*60)
print("IMPORTANT: Check your Twilio Console")
print("="*60)
print("1. Go to: https://console.twilio.com/")
print("2. Navigate to: Phone Numbers > Manage > Active Numbers")
print(f"3. Click on your number: {twilio_phone if twilio_phone else '[YOUR NUMBER]'}")
print("4. Scroll to 'Voice Configuration'")
print("5. Check 'A CALL COMES IN' webhook URL")
print("\nIt should be:")
print("  https://[YOUR-NGROK-URL]/incoming-call")
print("\nIf it's different, update it in Twilio Console!")
