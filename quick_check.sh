#!/bin/bash
# Quick check script for OpenAI response fix

echo "=================================="
echo "QUICK CHECK - OpenAI Response Fix"
echo "=================================="
echo ""

echo "1. Checking Python imports..."
python3 -c "import main; print('✅ main.py imports OK')" || { echo "❌ main.py has errors"; exit 1; }

echo "2. Checking tool configuration..."
python3 test_openai_response.py || { echo "❌ Tool config has errors"; exit 1; }

echo "3. Running diagnostics..."
python3 diagnose_call_issue.py

echo ""
echo "=================================="
echo "READY TO TEST"
echo "=================================="
echo ""
echo "Start your server:"
echo "  python3 main.py"
echo ""
echo "Then make a test call and say:"
echo "  'I want to book an appointment'"
echo ""
echo "You should see tool calls in the logs!"
