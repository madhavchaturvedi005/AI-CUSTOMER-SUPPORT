#!/bin/bash

# ============================================
# GitHub-Based EC2 Deployment Script
# Run this ON YOUR EC2 INSTANCE
# ============================================

set -e

REPO_URL="https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT.git"
APP_DIR="/var/www/voice-assistant"

echo "🚀 Starting GitHub-based deployment..."
echo "Repository: $REPO_URL"
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
echo "🐍 Installing Python 3.10 and dependencies..."
sudo apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    curl \
    build-essential \
    libpq-dev

# Clone repository
echo "📥 Cloning repository from GitHub..."
if [ -d "$APP_DIR" ]; then
    echo "⚠️  Directory $APP_DIR already exists"
    read -p "Do you want to remove it and re-clone? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo rm -rf $APP_DIR
    else
        echo "❌ Deployment cancelled"
        exit 1
    fi
fi

cd /home/ubuntu
git clone $REPO_URL voice-assistant

# Move to /var/www
sudo mkdir -p /var/www
sudo mv voice-assistant $APP_DIR
sudo chown -R ubuntu:ubuntu $APP_DIR

cd $APP_DIR

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file template
echo "⚙️  Creating .env file template..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# IMPORTANT: Replace these with your actual credentials!

OPENAI_API_KEY=your_openai_key_here

USE_REAL_DB=true
DATABASE_URL=your_database_url_here
DB_HOST=your_db_host
DB_PORT=14641
DB_NAME=defaultdb
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_SSLMODE=require

USE_REAL_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379

PORT=5050
TEMPERATURE=0.8

QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
EOF
    echo "⚠️  IMPORTANT: Edit $APP_DIR/.env with your actual credentials!"
    echo "   Run: sudo nano $APP_DIR/.env"
else
    echo "✅ .env file already exists"
fi

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/voice-assistant.service > /dev/null << EOF
[Unit]
Description=AI Voice Assistant Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/voice-assistant > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_connect_timeout 86400;
        proxy_send_timeout 86400;
    }
}
EOF

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/voice-assistant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Enable and start service
echo "🚀 Starting application service..."
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant

# Check if .env has been configured
if grep -q "your_openai_key_here" .env 2>/dev/null; then
    echo ""
    echo "⚠️  WARNING: .env file needs to be configured!"
    echo "   Please edit: sudo nano $APP_DIR/.env"
    echo "   Then start the service: sudo systemctl start voice-assistant"
else
    sudo systemctl start voice-assistant
    echo ""
    echo "✅ Service started!"
fi

echo ""
echo "============================================================"
echo "✅ Deployment complete!"
echo "============================================================"
echo ""
echo "📋 Next steps:"
echo ""
if grep -q "your_openai_key_here" .env 2>/dev/null; then
    echo "1. Edit .env file with your credentials:"
    echo "   sudo nano $APP_DIR/.env"
    echo ""
    echo "2. Start the service:"
    echo "   sudo systemctl start voice-assistant"
    echo ""
    echo "3. Check status:"
else
    echo "1. Check service status:"
fi
echo "   sudo systemctl status voice-assistant"
echo ""
echo "2. View logs:"
echo "   sudo journalctl -u voice-assistant -f"
echo ""
echo "3. Access dashboard:"
PUBLIC_IP=$(curl -s ifconfig.me)
echo "   http://$PUBLIC_IP/"
echo ""
echo "4. Configure Twilio webhook:"
echo "   http://$PUBLIC_IP/incoming-call"
echo ""
echo "============================================================"
echo ""

