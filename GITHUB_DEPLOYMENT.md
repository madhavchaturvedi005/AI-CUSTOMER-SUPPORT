# 🚀 GitHub-Based EC2 Deployment

Deploy your AI Voice Assistant to AWS EC2 using GitHub (cleanest method).

**Repository**: https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT

---

## 📋 Prerequisites

- AWS EC2 instance running Ubuntu 22.04
- GitHub repository (already set up ✅)
- SSH access to EC2

---

## 🎯 Deployment Steps

### Step 1: Connect to EC2

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

### Step 2: Install Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and tools
sudo apt-get install -y python3 python3-venv python3-pip git

# Install system dependencies
sudo apt-get install -y nginx certbot python3-certbot-nginx curl build-essential libpq-dev
```

### Step 3: Clone Repository

```bash
# Clone from GitHub
cd /home/ubuntu
git clone https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT.git voice-assistant

# Move to /var/www
sudo mkdir -p /var/www
sudo mv voice-assistant /var/www/
sudo chown -R ubuntu:ubuntu /var/www/voice-assistant

# Navigate to directory
cd /var/www/voice-assistant
```

### Step 4: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

**Paste your .env contents:**
```env
OPENAI_API_KEY=your_openai_api_key_here

USE_REAL_DB=true
DATABASE_URL=postgres://user:password@host:port/database?sslmode=require
DB_HOST=your_db_host_here
DB_PORT=14641
DB_NAME=defaultdb
DB_USER=your_db_user_here
DB_PASSWORD=your_db_password_here
DB_SSLMODE=require

USE_REAL_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379

PORT=5050
TEMPERATURE=0.8

QDRANT_URL=https://your-qdrant-url.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key_here
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Create Systemd Service

```bash
sudo nano /etc/systemd/system/voice-assistant.service
```

**Paste this:**
```ini
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
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 7: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/voice-assistant
```

**Paste this:**
```nginx
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
```

Save: `Ctrl+X`, then `Y`, then `Enter`

```bash
# Enable site
sudo ln -sf /etc/nginx/sites-available/voice-assistant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 8: Start Application

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable voice-assistant

# Start service
sudo systemctl start voice-assistant

# Check status
sudo systemctl status voice-assistant
```

You should see: `Active: active (running)` in green!

### Step 9: Configure Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

---

## ✅ Verify Deployment

### 1. Check Service Status
```bash
sudo systemctl status voice-assistant
```

### 2. View Logs
```bash
sudo journalctl -u voice-assistant -f
```
Press `Ctrl+C` to stop

### 3. Test Locally
```bash
curl http://localhost:5050
```

### 4. Get Your Public IP
```bash
curl ifconfig.me
```

### 5. Test in Browser
Open: `http://YOUR_EC2_PUBLIC_IP/`

You should see the login page!

Login: `madhav5` / `M@dhav0505@#`

---

## 🔄 Update Application (Future Updates)

When you push changes to GitHub:

```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Navigate to app directory
cd /var/www/voice-assistant

# Pull latest changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Restart service
sudo systemctl restart voice-assistant

# Check status
sudo systemctl status voice-assistant
```

---

## 📞 Configure Twilio Webhook

1. Go to Twilio Console: https://console.twilio.com/
2. Phone Numbers → Manage → Active numbers
3. Click your phone number
4. Voice Configuration:
   - **A CALL COMES IN**: Webhook
   - **URL**: `http://YOUR_EC2_PUBLIC_IP/incoming-call`
   - **HTTP**: POST
5. Save

Test by calling your Twilio number!

---

## 🔒 Enable HTTPS (Optional but Recommended)

### If you have a domain:

1. **Point domain to EC2**
   - Add A record: `@` → `YOUR_EC2_PUBLIC_IP`
   - Add A record: `www` → `YOUR_EC2_PUBLIC_IP`

2. **Update Nginx**
   ```bash
   sudo nano /etc/nginx/sites-available/voice-assistant
   ```
   Change `server_name _;` to `server_name yourdomain.com www.yourdomain.com;`

3. **Get SSL certificate**
   ```bash
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

4. **Update Twilio webhook**
   - Change to: `https://yourdomain.com/incoming-call`

---

## 📊 Monitoring Commands

```bash
# Service status
sudo systemctl status voice-assistant

# Real-time logs
sudo journalctl -u voice-assistant -f

# Last 100 lines
sudo journalctl -u voice-assistant -n 100

# Restart service
sudo systemctl restart voice-assistant

# Stop service
sudo systemctl stop voice-assistant

# Start service
sudo systemctl start voice-assistant

# Check resources
htop
df -h
free -h
```

---

## 🚨 Troubleshooting

### Service won't start
```bash
# Check logs
sudo journalctl -u voice-assistant -n 50

# Test manually
cd /var/www/voice-assistant
source venv/bin/activate
python3 main.py
```

### Can't access from browser
```bash
# Check service
sudo systemctl status voice-assistant

# Check Nginx
sudo systemctl status nginx
sudo nginx -t

# Check firewall
sudo ufw status

# Check AWS Security Group
# Ensure ports 80, 443 are open in EC2 console
```

### Database connection issues
```bash
cd /var/www/voice-assistant
source venv/bin/activate
python3 -c "
import asyncio
from database import initialize_database

async def test():
    db = await initialize_database()
    print('✅ Database connected')
    await db.disconnect()

asyncio.run(test())
"
```

### Git pull fails
```bash
# Stash local changes
git stash

# Pull updates
git pull origin main

# Reapply changes if needed
git stash pop
```

---

## 🎯 Quick Reference

**Repository**: https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT

**Clone command**:
```bash
git clone https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT.git
```

**Update command**:
```bash
cd /var/www/voice-assistant && git pull && sudo systemctl restart voice-assistant
```

**View logs**:
```bash
sudo journalctl -u voice-assistant -f
```

**Dashboard**: `http://YOUR_EC2_PUBLIC_IP/`

**Webhook**: `http://YOUR_EC2_PUBLIC_IP/incoming-call`

---

## ✅ Deployment Checklist

- [ ] EC2 instance running Ubuntu 22.04
- [ ] SSH access working
- [ ] Dependencies installed
- [ ] Repository cloned from GitHub
- [ ] Virtual environment created
- [ ] Python packages installed
- [ ] .env file configured
- [ ] Systemd service created
- [ ] Nginx configured
- [ ] Service running
- [ ] Dashboard accessible
- [ ] Login working
- [ ] Database connected
- [ ] Twilio webhook configured
- [ ] Test call successful

---

## 🎉 Success!

Your AI Voice Assistant is now live on AWS EC2, deployed from GitHub!

**Benefits of GitHub deployment:**
- ✅ Easy updates with `git pull`
- ✅ Version control
- ✅ Clean deployment process
- ✅ No manual file uploads
- ✅ Rollback capability

---

## 💡 Pro Tips

1. **Keep .env secure**: Never commit .env to GitHub
2. **Use branches**: Test changes in a dev branch first
3. **Automate updates**: Set up GitHub Actions for CI/CD
4. **Monitor logs**: Check logs regularly for issues
5. **Backup database**: Regular backups of PostgreSQL

---

**Happy deploying! 🚀**
