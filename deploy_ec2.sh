#!/bin/bash

# ============================================
# EC2 Deployment Script for AI Voice Assistant
# ============================================

set -e

echo "🚀 Starting EC2 deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.10 (default on Ubuntu 22.04)
echo "🐍 Installing Python 3.10..."
sudo apt-get install -y python3 python3-venv python3-pip

# Install system dependencies
echo "📚 Installing system dependencies..."
sudo apt-get install -y \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    build-essential \
    libpq-dev

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p /var/www/voice-assistant
sudo chown -R $USER:$USER /var/www/voice-assistant
cd /var/www/voice-assistant

# Clone or copy your application
echo "📥 Setting up application..."
# If using git:
# git clone <your-repo-url> .
# Or copy files manually

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
echo "⚙️  Creating environment file..."
cat > .env << 'EOF'
# Copy your .env contents here
OPENAI_API_KEY=your_key_here
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
DATABASE_URL=your_aiven_postgres_url
REDIS_URL=your_upstash_redis_url
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
PORT=5050
EOF

echo "⚠️  IMPORTANT: Edit /var/www/voice-assistant/.env with your actual credentials!"

# Create systemd service
echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/voice-assistant.service > /dev/null << 'EOF'
[Unit]
Description=AI Voice Assistant Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/voice-assistant
Environment="PATH=/var/www/voice-assistant/venv/bin"
ExecStart=/var/www/voice-assistant/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 1
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
    server_name your-domain.com;  # Replace with your domain or EC2 public IP

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

# Enable and start service
echo "🚀 Starting application service..."
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant

# Configure firewall
echo "🔒 Configuring firewall..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit /var/www/voice-assistant/.env with your credentials"
echo "2. Run: sudo systemctl restart voice-assistant"
echo "3. Check status: sudo systemctl status voice-assistant"
echo "4. View logs: sudo journalctl -u voice-assistant -f"
echo ""
echo "🌐 Your app should be running at: http://$(curl -s ifconfig.me)"
echo ""
echo "🔒 To enable HTTPS (recommended):"
echo "   sudo certbot --nginx -d your-domain.com"
echo ""
