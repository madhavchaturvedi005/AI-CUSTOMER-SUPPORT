#!/bin/bash

echo "🚀 Deploying Ultra-Optimized System Message"
echo "=========================================="
echo ""

# Check if config_optimized.py exists
if [ ! -f "config_optimized.py" ]; then
    echo "❌ Error: config_optimized.py not found"
    exit 1
fi

# Create backup
BACKUP_FILE="config_backup_$(date +%Y%m%d_%H%M%S).py"
echo "📦 Creating backup: $BACKUP_FILE"
cp config.py "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully"
else
    echo "❌ Failed to create backup"
    exit 1
fi

# Show comparison
echo ""
echo "📊 Token Comparison:"
echo "-------------------"
python3 -c "
from config import get_system_message as old_msg
from config_optimized import get_system_message as new_msg

kb = 'Test KB'
old = old_msg('Test', 'test', kb)
new = new_msg('Test', 'test', kb)

old_tokens = len(old) // 4
new_tokens = len(new) // 4
savings = ((old_tokens - new_tokens) / old_tokens) * 100

print(f'Original: ~{old_tokens} tokens')
print(f'Optimized: ~{new_tokens} tokens')
print(f'Savings: {savings:.1f}%')
"

echo ""
read -p "🤔 Deploy optimized config? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📝 Deploying optimized config..."
    cp config_optimized.py config.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Deployment successful!"
        echo ""
        echo "📝 Next steps:"
        echo "  1. Restart server: python3 main.py"
        echo "  2. Make test call"
        echo "  3. Verify AI behavior"
        echo "  4. Monitor token usage"
        echo ""
        echo "💡 To rollback: cp $BACKUP_FILE config.py"
    else
        echo "❌ Deployment failed"
        exit 1
    fi
else
    echo "❌ Deployment cancelled"
    echo "💡 Backup preserved: $BACKUP_FILE"
    exit 0
fi
