#!/bin/bash

# ============================================
# EC2 Quick Start - Run this on your LOCAL machine
# ============================================

echo "🚀 EC2 Quick Deployment Helper"
echo "================================"
echo ""

# Check if key file exists
if [ ! -f "voice-assistant-key.pem" ]; then
    echo "⚠️  Key file not found!"
    echo "Please download your EC2 key pair and save it as 'voice-assistant-key.pem'"
    exit 1
fi

# Get EC2 IP
read -p "Enter your EC2 Public IP: " EC2_IP

if [ -z "$EC2_IP" ]; then
    echo "❌ EC2 IP is required!"
    exit 1
fi

echo ""
echo "📦 Preparing deployment package..."

# Create deployment package
zip -r voice-assistant-deploy.zip . \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*node_modules*" \
    -x "*.env" \
    -x "voice-assistant-key.pem" \
    -x "voice-assistant-deploy.zip"

echo "✅ Package created"
echo ""

# Set key permissions
chmod 400 voice-assistant-key.pem

echo "📤 Uploading to EC2..."
scp -i voice-assistant-key.pem voice-assistant-deploy.zip ubuntu@$EC2_IP:/home/ubuntu/

echo "✅ Upload complete"
echo ""

echo "🔧 Connecting to EC2 and deploying..."
ssh -i voice-assistant-key.pem ubuntu@$EC2_IP << 'ENDSSH'
    # Unzip
    cd /home/ubuntu
    unzip -o voice-assistant-deploy.zip -d voice-assistant
    cd voice-assistant
    
    # Make deploy script executable
    chmod +x deploy_ec2.sh
    
    # Run deployment
    ./deploy_ec2.sh
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. SSH into your EC2: ssh -i voice-assistant-key.pem ubuntu@$EC2_IP"
echo "2. Edit .env file: sudo nano /var/www/voice-assistant/.env"
echo "3. Restart service: sudo systemctl restart voice-assistant"
echo "4. Check status: sudo systemctl status voice-assistant"
echo ""
echo "🌐 Your app will be at: http://$EC2_IP"
echo ""
