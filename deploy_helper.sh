#!/bin/bash

# ============================================
# AWS EC2 Deployment Helper
# Run this on your LOCAL machine
# ============================================

echo "🚀 AWS EC2 Deployment Helper"
echo "============================"
echo ""

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found!"
    echo "Please run this script from your project root directory."
    exit 1
fi

echo "📋 Pre-Deployment Checklist"
echo ""

# Check for .env file
if [ -f ".env" ]; then
    echo "✅ .env file found"
else
    echo "❌ .env file not found!"
    echo "Please create .env file with your credentials first."
    exit 1
fi

# Check for requirements.txt
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo ""
echo "🎯 Deployment Options:"
echo ""
echo "1. Create deployment package (zip file)"
echo "2. Upload to existing EC2 instance"
echo "3. Full deployment guide"
echo "4. Exit"
echo ""

read -p "Choose an option (1-4): " choice

case $choice in
    1)
        echo ""
        echo "📦 Creating deployment package..."
        
        # Create deployment package
        zip -r voice-assistant-deploy.zip . \
            -x "*.git*" \
            -x "*__pycache__*" \
            -x "*.pyc" \
            -x "*node_modules*" \
            -x "*.pytest_cache*" \
            -x "*.vscode*" \
            -x "voice-assistant-key.pem" \
            -x "*.zip"
        
        echo "✅ Package created: voice-assistant-deploy.zip"
        echo ""
        echo "📤 Next steps:"
        echo "1. Launch an EC2 instance (see AWS_DEPLOYMENT_START.md)"
        echo "2. Upload this file to EC2:"
        echo "   scp -i your-key.pem voice-assistant-deploy.zip ubuntu@YOUR_EC2_IP:/home/ubuntu/"
        echo "3. SSH to EC2 and unzip:"
        echo "   ssh -i your-key.pem ubuntu@YOUR_EC2_IP"
        echo "   unzip voice-assistant-deploy.zip -d /var/www/voice-assistant"
        ;;
        
    2)
        echo ""
        read -p "Enter path to your EC2 key file (.pem): " KEY_FILE
        
        if [ ! -f "$KEY_FILE" ]; then
            echo "❌ Key file not found: $KEY_FILE"
            exit 1
        fi
        
        read -p "Enter your EC2 Public IP: " EC2_IP
        
        if [ -z "$EC2_IP" ]; then
            echo "❌ EC2 IP is required!"
            exit 1
        fi
        
        echo ""
        echo "📦 Creating deployment package..."
        
        zip -r voice-assistant-deploy.zip . \
            -x "*.git*" \
            -x "*__pycache__*" \
            -x "*.pyc" \
            -x "*node_modules*" \
            -x "*.pytest_cache*" \
            -x "*.vscode*" \
            -x "*.pem" \
            -x "*.zip"
        
        echo "✅ Package created"
        echo ""
        
        # Set key permissions
        chmod 400 "$KEY_FILE"
        
        echo "📤 Uploading to EC2..."
        scp -i "$KEY_FILE" voice-assistant-deploy.zip ubuntu@$EC2_IP:/home/ubuntu/
        
        echo "✅ Upload complete!"
        echo ""
        echo "📋 Next steps:"
        echo "1. SSH to your EC2:"
        echo "   ssh -i $KEY_FILE ubuntu@$EC2_IP"
        echo ""
        echo "2. On EC2, run:"
        echo "   cd /home/ubuntu"
        echo "   sudo mkdir -p /var/www/voice-assistant"
        echo "   sudo chown -R ubuntu:ubuntu /var/www/voice-assistant"
        echo "   unzip -o voice-assistant-deploy.zip -d /var/www/voice-assistant"
        echo "   cd /var/www/voice-assistant"
        echo "   chmod +x deploy_ec2.sh"
        echo "   ./deploy_ec2.sh"
        echo ""
        echo "3. Edit .env file with your credentials:"
        echo "   sudo nano /var/www/voice-assistant/.env"
        echo ""
        echo "4. Restart service:"
        echo "   sudo systemctl restart voice-assistant"
        ;;
        
    3)
        echo ""
        echo "📖 Opening deployment guide..."
        if command -v open &> /dev/null; then
            open AWS_DEPLOYMENT_START.md
        elif command -v xdg-open &> /dev/null; then
            xdg-open AWS_DEPLOYMENT_START.md
        else
            echo "Please open AWS_DEPLOYMENT_START.md manually"
        fi
        ;;
        
    4)
        echo "👋 Goodbye!"
        exit 0
        ;;
        
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
