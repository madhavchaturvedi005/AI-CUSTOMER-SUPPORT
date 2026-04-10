import os
from dotenv import load_dotenv
import requests

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY or OPENAI_API_KEY == 'your_api_key':
    print("❌ Error: OPENAI_API_KEY is not set or is still the placeholder value")
    print("Please update your .env file with your actual OpenAI API key")
    exit(1)

print(f"✓ API Key found (starts with: {OPENAI_API_KEY[:10]}...)")
print("Testing OpenAI API connection...")

# Test the API key with a simple request
headers = {
    "Authorization": f"Bearer {OPENAI_API_KEY}"
}

try:
    response = requests.get("https://api.openai.com/v1/models", headers=headers)
    
    if response.status_code == 200:
        print("✓ OpenAI API key is valid and working!")
        models = response.json()
        print(f"✓ Successfully connected to OpenAI API")
    elif response.status_code == 401:
        print("❌ Error: Invalid API key")
        print("Please check your OpenAI API key in the .env file")
    else:
        print(f"❌ Error: API returned status code {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error connecting to OpenAI API: {e}")
