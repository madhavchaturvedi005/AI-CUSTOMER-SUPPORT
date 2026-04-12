# AWS EC2 Deployment - Getting Started

## 🎯 Deployment Overview

You have two options for deploying to AWS EC2:

### Option A: Manual Deployment (Recommended for first time)
- Full control over each step
- Better understanding of the setup
- Easier to troubleshoot

### Option B: Automated Deployment
- Faster deployment
- Uses provided scripts
- Good for subsequent deployments

---

## 📋 Pre-Deployment Checklist

Before starting, ensure you have:

- [ ] AWS Account (sign up at aws.amazon.com)
- [ ] Credit card for AWS (required even for free tier)
- [ ] Your `.env` file with all credentials ready
- [ ] Twilio account and phone number
- [ ] OpenAI API key
- [ ] Aiven PostgreSQL database (already configured)
- [ ] Domain name (optional, but recommended for HTTPS)

---

## 🚀 Quick Start - Step by Step

### Step 1: Launch EC2 Instance

1. **Go to AWS Console**
   - Visit: https://console.aws.amazon.com/ec2/
   - Sign in to your AWS account

2. **Launch Instance**
   - Click "Launch Instance" button
   - Follow the configuration below

3. **Instance Configuration**

   **Name and tags:**
   ```
   Name: voice-assistant-server
   ```

   **Application and OS Images (AMI):**
   ```
   Ubuntu Server 22.04 LTS (HVM), SSD Volume Type
   Architecture: 64-bit (x86)
   ✅ Free tier eligible
   ```

   **Instance type:**
   ```
   t2.micro (Free tier eligible)
   - 1 vCPU
   - 1 GiB Memory
   ```

   **Key pair (login):**
   ```
   Click "Create new key pair"
   Key pair name: voice-assistant-key
   Key pair type: RSA
   Private key file format: .pem
   
   ⚠️ IMPORTANT: Download and save the .pem file!
   You'll need this to connect to your server.
   ```

   **Network settings:**
   ```
   Click "Edit" and configure:
   
   ✅ Allow SSH traffic from: My IP (or Anywhere for testing)
   ✅ Allow HTTP traffic from the internet
   ✅ Allow HTTPS traffic from the internet
   ```

   **Configure storage:**
   ```
   30 GiB gp3 (Free tier eligible)
   ```

4. **Launch Instance**
   - Review your settings
   - Click "Launch instance"
   - Wait for instance state to be "Running" (takes 1-2 minutes)

5. **Get Your Instance Details**
   - Click on your instance ID
   - Note down the **Public IPv4 address** (e.g., 54.123.45.67)
   - This is your server's address

---

### Step 2: Connect to Your EC2 Instance

**On macOS/Linux:**

1. **Set key permissions**
   ```bash
   chmod 400 ~/Downloads/voice-assistant-key.pem
   ```

2. **Connect via SSH**
   ```bash
   ssh -i ~/Downloads/voice-assistant-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
   ```
   
   Replace `YOUR_EC2_PUBLIC_IP` with your actual IP address.

3. **First time connection**
   - You'll see a message: "Are you sure you want to continue connecting?"
   - Type `yes` and press Enter

4. **You're in!**
   - You should see: `ubuntu@ip-xxx-xxx-xxx-xxx:~$`
   - You're now connected to your EC2 server

---

### Step 3: Deploy Your Application

**Option A: Manual Deployment (Recommended)**

Run these commands on your EC2 instance:

```bash
# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python 3.10 (default on Ubuntu 22.04)
sudo apt-get install -y python3 python3-venv python3-pip

# 3. Install system dependencies
sudo apt-get install -y nginx certbot python3-certbot-nginx git curl build-essential libpq-dev

# 4. Create application directory
sudo mkdir -p /var/www/voice-assistant
sudo chown -R ubuntu:ubuntu /var/www/voice-assistant

# 5. Upload your code (see below)
```

**Upload Your Code to EC2:**

From your LOCAL machine (new terminal):

```bash
# Navigate to your project directory
cd /path/to/your/speech-assistant-openai-realtime-api-python

# Create a deployment package
zip -r voice-assistant.zip . \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*node_modules*" \
    -x "voice-assistant-key.pem"

# Upload to EC2
scp -i ~/Downloads/voice-assistant-key.pem voice-assistant.zip ubuntu@YOUR_EC2_PUBLIC_IP:/home/ubuntu/

# Connect back to EC2
ssh -i ~/Downloads/voice-assistant-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# Unzip on EC2
cd /home/ubuntu
unzip voice-assistant.zip -d /var/www/voice-assistant
cd /var/www/voice-assistant
```

**Continue on EC2:**

```bash
# 6. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 7. Install Python packages
pip install --upgrade pip
pip install -r requirements.txt

# 8. Create .env file
nano .env
```

**Paste your .env contents** (from your local .env file):
```env
OPENAI_API_KEY=sk-proj-...
USE_REAL_DB=true
DATABASE_URL=postgres://avnadmin:...@pg-1c535dfd-madhavchaturvedimac-9806.j.aivencloud.com:14641/defaultdb?sslmode=require
DB_HOST=pg-1c535dfd-madhavchaturvedimac-9806.j.aivencloud.com
DB_PORT=14641
DB_NAME=defaultdb
DB_USER=avnadmin
DB_PASSWORD=AVNS_35aiv44hUxwJ9Kq_eE5
DB_SSLMODE=require
USE_REAL_REDIS=true
REDIS_HOST=localhost
REDIS_PORT=6379
PORT=5050
TEMPERATURE=0.8
QDRANT_URL=https://8b745f0a-0926-468e-8989-e40430834d4f.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Save: `Ctrl+X`, then `Y`, then `Enter`

```bash
# 9. Create systemd service
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

```bash
# 10. Configure Nginx
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
# 11. Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/voice-assistant /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# 12. Start your application
sudo systemctl daemon-reload
sudo systemctl enable voice-assistant
sudo systemctl start voice-assistant

# 13. Check status
sudo systemctl status voice-assistant
```

You should see: `Active: active (running)` in green!

---

### Step 4: Test Your Deployment

1. **Check the service**
   ```bash
   sudo systemctl status voice-assistant
   ```

2. **View logs**
   ```bash
   sudo journalctl -u voice-assistant -f
   ```
   Press `Ctrl+C` to stop viewing logs

3. **Test locally on EC2**
   ```bash
   curl http://localhost:5050
   ```

4. **Test from your browser**
   - Open: `http://YOUR_EC2_PUBLIC_IP/`
   - You should see the login page!
   - Login: `madhav5` / `M@dhav0505@#`

---

### Step 5: Configure Twilio Webhook

1. **Go to Twilio Console**
   - Visit: https://console.twilio.com/
   - Go to Phone Numbers → Manage → Active numbers
   - Click on your phone number

2. **Configure Voice & Fax**
   - Under "Voice Configuration"
   - A CALL COMES IN: **Webhook**
   - URL: `http://YOUR_EC2_PUBLIC_IP/incoming-call`
   - HTTP: **POST**
   - Click "Save"

3. **Test a call**
   - Call your Twilio number
   - The AI should answer!

---

## 🎉 Success!

Your AI Voice Assistant is now live on AWS EC2!

**Dashboard:** `http://YOUR_EC2_PUBLIC_IP/`
**Webhook:** `http://YOUR_EC2_PUBLIC_IP/incoming-call`

---

## 📊 Monitoring Commands

```bash
# Check service status
sudo systemctl status voice-assistant

# View real-time logs
sudo journalctl -u voice-assistant -f

# View last 100 log lines
sudo journalctl -u voice-assistant -n 100

# Restart service
sudo systemctl restart voice-assistant

# Stop service
sudo systemctl stop voice-assistant

# Start service
sudo systemctl start voice-assistant
```

---

## 🔒 Next Steps (Optional but Recommended)

### 1. Enable HTTPS with Domain

If you have a domain name:

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

### 2. Set Up Monitoring

```bash
# Install monitoring tools
sudo apt-get install -y htop

# Monitor resources
htop
```

### 3. Enable Swap (for 1GB RAM)

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
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
# Check if service is running
sudo systemctl status voice-assistant

# Check if Nginx is running
sudo systemctl status nginx

# Check AWS Security Group
# Go to EC2 Console → Security Groups
# Ensure ports 80, 443 are open
```

### Database connection issues
```bash
# Test database
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

---

## 💰 Cost Estimate

**Free Tier (First 12 months):**
- EC2 t2.micro: FREE (750 hours/month)
- 30 GB Storage: FREE
- Data Transfer: 15 GB/month FREE

**After Free Tier:**
- ~$10-12/month for EC2 + storage

**Per-use costs:**
- Twilio: ~$0.0085/minute
- OpenAI Realtime API: ~$0.06/minute

---

## ✅ Deployment Checklist

- [ ] EC2 instance launched and running
- [ ] SSH connection working
- [ ] Application code uploaded
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Systemd service created and running
- [ ] Nginx configured and running
- [ ] Dashboard accessible via browser
- [ ] Login working
- [ ] Database connected (real data showing)
- [ ] Twilio webhook configured
- [ ] Test call successful

---

## 📞 Need Help?

Check these files for more details:
- `EC2_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `deploy_ec2.sh` - Automated deployment script
- `COMPLETE_FIX_SUMMARY.md` - Recent fixes and updates

---

**You're ready to deploy! 🚀**
