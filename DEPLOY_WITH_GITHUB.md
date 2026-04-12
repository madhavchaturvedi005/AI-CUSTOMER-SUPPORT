# 🚀 Deploy with GitHub - Quick Guide

The cleanest way to deploy your AI Voice Assistant to AWS EC2.

---

## 🎯 One-Command Deployment

### On your EC2 instance, run:

```bash
curl -sSL https://raw.githubusercontent.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT/main/deploy_from_github.sh | bash
```

Or manually:

```bash
# Download script
wget https://raw.githubusercontent.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT/main/deploy_from_github.sh

# Make executable
chmod +x deploy_from_github.sh

# Run
./deploy_from_github.sh
```

---

## 📋 What This Does

1. ✅ Updates system packages
2. ✅ Installs Python 3.10 and dependencies
3. ✅ Clones your GitHub repository
4. ✅ Sets up virtual environment
5. ✅ Installs Python packages
6. ✅ Creates systemd service
7. ✅ Configures Nginx
8. ✅ Sets up firewall
9. ✅ Starts your application

---

## ⚙️ After Deployment

### 1. Configure .env file

```bash
sudo nano /var/www/voice-assistant/.env
```

Paste your actual credentials (replace the placeholders).

### 2. Start the service

```bash
sudo systemctl start voice-assistant
```

### 3. Check status

```bash
sudo systemctl status voice-assistant
```

### 4. View logs

```bash
sudo journalctl -u voice-assistant -f
```

---

## 🌐 Access Your Application

### Dashboard
```
http://YOUR_EC2_PUBLIC_IP/
```

Login: `madhav5` / `M@dhav0505@#`

### Twilio Webhook
```
http://YOUR_EC2_PUBLIC_IP/incoming-call
```

---

## 🔄 Update Application

When you push changes to GitHub:

```bash
cd /var/www/voice-assistant
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart voice-assistant
```

---

## 📚 Full Documentation

- `GITHUB_DEPLOYMENT.md` - Complete step-by-step guide
- `deploy_from_github.sh` - Automated deployment script
- `EC2_PYTHON_FIX.md` - Python version troubleshooting

---

## ✅ Benefits

- ✅ No manual file uploads
- ✅ Easy updates with `git pull`
- ✅ Version control
- ✅ Clean deployment
- ✅ Rollback capability

---

**Repository**: https://github.com/madhavchaturvedi005/AI-CUSTOMER-SUPPORT

**Ready to deploy? SSH to your EC2 and run the command above!** 🚀
