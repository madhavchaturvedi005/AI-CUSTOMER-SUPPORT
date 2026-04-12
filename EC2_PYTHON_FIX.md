# Python Version Fix for EC2 Deployment

## Issue
Ubuntu 22.04 doesn't have Python 3.11 in default repositories, causing this error:
```
E: Unable to locate package python3.11
```

## Solution
Use Python 3.10 (default on Ubuntu 22.04) instead. It works perfectly with our application.

---

## Fixed Commands

### Instead of:
```bash
sudo apt-get install -y python3.11 python3.11-venv python3-pip
python3.11 -m venv venv
```

### Use:
```bash
sudo apt-get install -y python3 python3-venv python3-pip
python3 -m venv venv
```

---

## Complete Fixed Deployment Steps

Run these commands on your EC2 instance:

```bash
# 1. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python 3.10 (default)
sudo apt-get install -y python3 python3-venv python3-pip

# 3. Install system dependencies
sudo apt-get install -y nginx certbot python3-certbot-nginx git curl build-essential libpq-dev

# 4. Create application directory
sudo mkdir -p /var/www/voice-assistant
sudo chown -R ubuntu:ubuntu /var/www/voice-assistant

# 5. Navigate to directory
cd /var/www/voice-assistant

# 6. Unzip your uploaded code (if you uploaded a zip)
# unzip /home/ubuntu/voice-assistant-deploy.zip -d .

# 7. Create virtual environment with Python 3.10
python3 -m venv venv
source venv/bin/activate

# 8. Verify Python version
python --version
# Should show: Python 3.10.x

# 9. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 10. Create .env file
nano .env
# Paste your .env contents, save with Ctrl+X, Y, Enter

# 11. Continue with deployment script
chmod +x deploy_ec2.sh
./deploy_ec2.sh
```

---

## Why Python 3.10 Works

- Python 3.10 is the default on Ubuntu 22.04
- All our dependencies support Python 3.10+
- FastAPI, asyncpg, OpenAI SDK all work perfectly
- No code changes needed

---

## If You Already Started Deployment

If you already ran the old commands and got errors:

```bash
# Just continue with the fixed commands
sudo apt-get install -y python3 python3-venv python3-pip
cd /var/www/voice-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Then continue with the rest of the deployment
```

---

## Alternative: Install Python 3.11 (Optional)

If you specifically want Python 3.11:

```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update

# Install Python 3.11
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# Use it
python3.11 -m venv venv
source venv/bin/activate
```

But this is NOT necessary - Python 3.10 works great!

---

## Updated Deployment Scripts

The following scripts have been updated to use Python 3.10:
- ✅ `deploy_ec2.sh` - Fixed
- ✅ `AWS_DEPLOYMENT_START.md` - Fixed
- ✅ `EC2_DEPLOYMENT_GUIDE.md` - Already correct

---

## Quick Test

After creating the virtual environment, verify:

```bash
source venv/bin/activate
python --version
# Should show: Python 3.10.x

pip --version
# Should show pip with Python 3.10

# Test imports
python -c "import fastapi; print('FastAPI OK')"
python -c "import asyncpg; print('asyncpg OK')"
python -c "import openai; print('OpenAI OK')"
```

All should work without errors!

---

## Status

✅ Scripts updated to use Python 3.10
✅ Compatible with Ubuntu 22.04 default packages
✅ No additional PPAs needed
✅ All dependencies work correctly

Continue with your deployment using the fixed commands above!
