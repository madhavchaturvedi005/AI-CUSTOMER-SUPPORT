# 🚀 AWS EC2 Deployment Guide

Complete guide to deploy your AI Voice Assistant on AWS EC2 Free Tier.

---

## 📋 Prerequisites

- AWS Account (Free Tier eligible)
- Domain name (optional, but recommended for SSL)
- Your `.env` file with all credentials

---

## 🎯 Step 1: Launch EC2 Instance

### 1.1 Go to AWS Console
- Navigate to EC2 Dashboard
- Click "Launch Instance"

### 1.2 Configure Instance

**Name:** `voice-assistant-server`

**AMI:** Ubuntu Server 22.04 LTS (Free tier eligible)

**Instance Type:** `t3.micro` or `t2.micro` (Free tier eligible)
- 1 vCPU
- 1 GB RAM
- Perfect for your use case

**Key Pair:** 
- Create new key pair: `voice-assistant-key`
- Download `.pem` file
- Save it securely!

**Network Settings:**
- ✅ Allow SSH (port 22) from your IP
- ✅ Allow HTTP (port 80) from anywhere
- ✅ Allow HTTPS (port 443) from anywhere

**Storage:** 
- 30 GB gp3 (Free tier includes 30 GB)

### 1.3 Launch Instance
- Click "Launch Instance"
- Wait for instance to be "Running"
- Note the **Public IPv4 address**

---

## 🔐 Step 2: Connect to EC2

### 2.1 Set Key Permissions
```bash
chmod 400 voice-assistant-key.pem
```

### 2.2 Connect via SSH
```bash
ssh -i voice-assistant-key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

Replace `YOUR_EC2_PUBLIC_IP` with your instance's public IP.

---

## 📦 Step 3: Deploy Application

### 3.1 Upload Files to EC2

**Option A: Using SCP (from your local machine)**
```bash
# Upload entire project
scp -i voice-assistant-key.pem -r /path/to/your/project ubuntu@YOUR_EC2_PUBLIC_IP:/home/ubuntu/voice-assistant

# Or upload as zip
zip -r voice-assistant.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"
scp -i voice-assistant-key.pem voice-assistant.zip ubuntu@YOUR_EC2_PUBLIC_IP:/home/ubuntu/
```

**Option B: Using Git (recommended)**
```bash
# On EC2 instance
git clone https://github.com/your-username/your-repo.git /home/ubuntu/voice-assistant
cd /home/ubuntu/voice-assistant
```

### 3.2 Run Deployment Script
```bash
# On EC2 instance
cd /home/ubuntu/voice-assistant
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

### 3.3 Configure Environment Variables
```bash
# Edit .env file
sudo nano /var/www/voice-assistant/.env
```

Paste your actual credentials:
```env
OPENAI_API_KEY=sk-proj-...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
DATABASE_URL=postgresql://...@...aiven.io:...
REDIS_URL=redis://...upstash.io:...
QDRANT_URL=https://...qdrant.io
QDRANT_API_KEY=...
PORT=5050
BUSINESS_NAME=Your Business Name
BUSINESS_TYPE=your business type
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### 3.4 Restart Service
```bash
sudo systemctl restart voice-assistant
```

---

## ✅ Step 4: Verify Deployment

### 4.1 Check Service Status
```bash
sudo systemctl status voice-assistant
```

Should show: `Active: active (running)`

### 4.2 View Logs
```bash
# Real-time logs
sudo journalctl -u voice-assistant -f

# Last 100 lines
sudo journalctl -u voice-assistant -n 100
```

### 4.3 Test Application
```bash
# Check if server is responding
curl http://localhost:5050

# Check from outside
curl http://YOUR_EC2_PUBLIC_IP
```

### 4.4 Access Dashboard
Open browser: `http://YOUR_EC2_PUBLIC_IP`

You should see your dashboard!

---

## 🔒 Step 5: Enable HTTPS (Recommended)

### 5.1 Point Domain to EC2
- Go to your domain registrar
- Add A record: `@` → `YOUR_EC2_PUBLIC_IP`
- Add A record: `www` → `YOUR_EC2_PUBLIC_IP`
- Wait 5-10 minutes for DNS propagation

### 5.2 Update Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/voice-assistant
```

Change `server_name` line:
```nginx
server_name yourdomain.com www.yourdomain.com;
```

### 5.3 Get SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Follow prompts:
- Enter email
- Agree to terms
- Choose: Redirect HTTP to HTTPS (option 2)

### 5.4 Test HTTPS
Open browser: `https://yourdomain.com`

---

## 🔧 Step 6: Configure Twilio Webhook

### 6.1 Update Twilio Console
- Go to Twilio Console
- Phone Numbers → Your Number
- Voice Configuration:
  - **A CALL COMES IN:** Webhook
  - **URL:** `https://yourdomain.com/incoming-call` (or `http://YOUR_EC2_PUBLIC_IP/incoming-call`)
  - **HTTP:** POST

### 6.2 Test Call
Call your Twilio number and verify it works!

---

## 📊 Monitoring & Maintenance

### Check Service Status
```bash
sudo systemctl status voice-assistant
```

### View Logs
```bash
# Real-time
sudo journalctl -u voice-assistant -f

# Last 100 lines
sudo journalctl -u voice-assistant -n 100

# Errors only
sudo journalctl -u voice-assistant -p err
```

### Restart Service
```bash
sudo systemctl restart voice-assistant
```

### Update Application
```bash
cd /var/www/voice-assistant
git pull  # If using git
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart voice-assistant
```

### Check Disk Space
```bash
df -h
```

### Check Memory Usage
```bash
free -h
```

### Check CPU Usage
```bash
top
```

---

## 🔄 Auto-Restart on Failure

The systemd service is configured to auto-restart:
```ini
Restart=always
RestartSec=10
```

This means if your app crashes, it will automatically restart after 10 seconds.

---

## 💰 Cost Breakdown

### Free Tier (First 12 months)
- ✅ EC2 t3.micro: **FREE** (750 hours/month)
- ✅ 30 GB Storage: **FREE**
- ✅ Elastic IP: **FREE** (when attached)
- ✅ Data Transfer: **15 GB/month FREE**

### After Free Tier
- EC2 t3.micro: **~$8-10/month**
- 30 GB Storage: **~$3/month**
- Data Transfer: **$0.09/GB** (after 15 GB)

**Total: ~$11-13/month** after free tier

### External Services (Always Paid)
- Twilio: **~$0.0085/min** for calls
- OpenAI: **~$0.06/min** for realtime API
- Aiven PostgreSQL: **FREE** (1 GB)
- Upstash Redis: **FREE** (10K commands/day)
- Qdrant: **FREE** (1 GB)

---

## 🚨 Troubleshooting

### Service Won't Start
```bash
# Check logs
sudo journalctl -u voice-assistant -n 50

# Check if port is in use
sudo lsof -i :5050

# Test manually
cd /var/www/voice-assistant
source venv/bin/activate
python3 main.py
```

### Can't Connect from Outside
```bash
# Check firewall
sudo ufw status

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check security group in AWS Console
# Ensure ports 80, 443 are open
```

### Database Connection Issues
```bash
# Test database connection
cd /var/www/voice-assistant
source venv/bin/activate
python3 -c "from database import test_connection; import asyncio; asyncio.run(test_connection())"
```

### High Memory Usage
```bash
# Check memory
free -h

# Restart service
sudo systemctl restart voice-assistant

# Consider upgrading to t3.small if needed
```

---

## 🎯 Performance Optimization

### 1. Enable Swap (for 1GB RAM)
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 2. Optimize Uvicorn Workers
In `/etc/systemd/system/voice-assistant.service`:
```ini
# For t3.micro (1 GB RAM), use 1 worker
ExecStart=/var/www/voice-assistant/venv/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 5050 --workers 1
```

### 3. Enable Nginx Caching
```bash
sudo nano /etc/nginx/sites-available/voice-assistant
```

Add inside `server` block:
```nginx
location /static {
    alias /var/www/voice-assistant/frontend;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 📈 Scaling Up (When Needed)

### Upgrade Instance Type
1. Stop instance
2. Actions → Instance Settings → Change Instance Type
3. Select `t3.small` (2 GB RAM) or `t3.medium` (4 GB RAM)
4. Start instance

### Add Load Balancer (for high traffic)
1. Create Application Load Balancer
2. Add EC2 instance as target
3. Update Twilio webhook to ALB URL

---

## ✅ Success Checklist

- [ ] EC2 instance running
- [ ] Application deployed
- [ ] Service active and running
- [ ] Dashboard accessible via browser
- [ ] HTTPS enabled (if using domain)
- [ ] Twilio webhook configured
- [ ] Test call successful
- [ ] Logs showing no errors
- [ ] Auto-restart configured

---

## 🎉 You're Live!

Your AI Voice Assistant is now running 24/7 on AWS EC2!

**Dashboard:** `https://yourdomain.com` or `http://YOUR_EC2_PUBLIC_IP`

**Twilio Webhook:** `https://yourdomain.com/incoming-call`

---

## 📞 Support

If you encounter issues:
1. Check logs: `sudo journalctl -u voice-assistant -f`
2. Verify .env file has correct credentials
3. Test database connection
4. Check AWS security group settings
5. Verify Twilio webhook URL

---

**Happy Calling! 🎤📞**
