# Debugging Steps

## 1. Check your server logs
Look at the terminal running `python3 main.py` - you should see error messages when the call disconnects.

## 2. Common errors and fixes:

### "Missing the OpenAI API key"
- Update `.env` file with real API key from https://platform.openai.com/api-keys

### "401 Unauthorized" or authentication error
- Your API key is invalid or expired
- Get a new key from OpenAI dashboard

### "Connection refused" or WebSocket error
- Check if you have OpenAI Realtime API access
- Verify your OpenAI account has credits/billing set up

## 3. Test your OpenAI key
Run: `python3 test_openai.py`

## 4. Check ngrok
Make sure ngrok is still running and the URL hasn't changed
