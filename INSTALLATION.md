# 🤖 Telegram SMS Bot Installation Guide

## 📋 System Requirements

### **Operating System:**
- Ubuntu 20.04+ (Recommended)
- Debian 11+
- CentOS 8+
- macOS 12+
- Windows 10+ (with WSL2)

### **Software Requirements:**
- **Python:** 3.8 or higher (3.11+ recommended)
- **MongoDB:** 4.4 or higher (5.0+ recommended)
- **Git:** For cloning the repository
- **pip3:** Python package manager

---

## 🚀 Quick Installation

### **1. Clone Repository**
```bash
git clone <your-repository-url>
cd telegram-sms-bot
```

### **2. Install Python Dependencies**
```bash
# Install required packages
pip3 install -r requirements.txt

# Or using virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **3. Configure Environment**
```bash
# Create user cache directory
mkdir -p user_cache

# Copy and edit configuration
cp config.py.example config.py  # If you have an example file
# OR edit config.py directly with your settings
```

### **4. Configure MongoDB**
- Install MongoDB on your system
- Create database: `TelegramBotDB`
- Update `MONGO_URI` in `config.py`

### **5. Start the Bot**
```bash
python3 bot.py
```

---

## 🔧 Detailed Installation

### **Step 1: System Dependencies**

#### **Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-dev python3-venv
sudo apt install -y mongodb-server git curl
```

#### **CentOS/RHEL:**
```bash
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel git
# Install MongoDB following official documentation
```

#### **macOS:**
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 mongodb-community git
```

### **Step 2: Python Virtual Environment (Recommended)**
```bash
# Create virtual environment
python3 -m venv telegram-bot-env

# Activate virtual environment
source telegram-bot-env/bin/activate  # Linux/macOS
# OR
telegram-bot-env\Scripts\activate  # Windows

# Upgrade pip
pip install --upgrade pip
```

### **Step 3: Install Python Dependencies**
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Verify installation
python -c "import telegram, motor, aiohttp, pytz, pycountry; print('✅ All dependencies installed')"
```

### **Step 4: MongoDB Setup**

#### **Local MongoDB Installation:**
```bash
# Ubuntu/Debian
sudo systemctl start mongodb
sudo systemctl enable mongodb

# Create database and user (optional)
mongo
> use TelegramBotDB
> db.createUser({user: "botuser", pwd: "secure_password", roles: ["readWrite"]})
> exit
```

#### **MongoDB Atlas (Cloud):**
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create cluster and database
3. Get connection string
4. Update `MONGO_URI` in config.py

### **Step 5: Bot Configuration**

#### **Create Telegram Bot:**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command
3. Get your bot token
4. Update `TOKEN` in `config.py`

#### **Setup Telegram Channel:**
1. Create a Telegram channel
2. Add your bot as admin
3. Get channel ID (use @userinfobot)
4. Update `CHANNEL_ID` and `CHANNEL_LINK` in `config.py`

#### **Configure SMS API:**
1. Update `SMS_API_BASE_URL` with your SMS panel URL
2. Login to SMS panel and get session cookie
3. Update `SMS_API_COOKIE` in `config.py`

---

## ⚙️ Configuration File

### **config.py Structure:**
```python
# === TELEGRAM BOT CONFIGURATION ===
TOKEN = "your_bot_token_here"
CHANNEL_ID = -1001234567890
CHANNEL_LINK = "https://t.me/your_channel"

# === DATABASE CONFIGURATION ===
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "TelegramBotDB"
COLLECTION_NAME = "numbers"
COUNTRIES_COLLECTION = "countries"
USERS_COLLECTION = "verified_users"

# === ADMIN CONFIGURATION ===
ADMIN_IDS = {your_user_id}

# === SMS API CONFIGURATION ===
SMS_API_BASE_URL = "http://your-sms-panel.com"
SMS_API_ENDPOINT = "/api/endpoint"
SMS_API_COOKIE = "PHPSESSID=your_session_here"

# === OTHER CONFIGURATIONS ===
TIMEZONE_NAME = 'Asia/Riyadh'
LOGGING_LEVEL = "INFO"
USER_CACHE_DIR = "user_cache"
```

---

## 🚀 Running the Bot

### **Development Mode:**
```bash
# Run directly
python3 bot.py

# Run with verbose logging
python3 bot.py --log-level DEBUG
```

### **Production Mode:**
```bash
# Using nohup
nohup python3 bot.py > bot.log 2>&1 &

# Using systemd (recommended)
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### **Using Docker (Advanced):**
```bash
# Build image
docker build -t telegram-sms-bot .

# Run container
docker run -d --name sms-bot \
  -v $(pwd)/config.py:/app/config.py \
  -v $(pwd)/user_cache:/app/user_cache \
  telegram-sms-bot
```

---

## 🔍 Verification

### **Test Installation:**
```bash
# Check bot startup
python3 -c "from bot import *; print('✅ Bot imports successful')"

# Test database connection
python3 -c "from motor.motor_asyncio import AsyncIOMotorClient; import asyncio; print('✅ MongoDB connection available')"

# Verify all modules
python3 -c "
import telegram
import motor
import aiohttp
import pytz
import pycountry
print('✅ All required modules available')
print(f'📱 python-telegram-bot: {telegram.__version__}')
print(f'🗄️ motor: {motor.version}')
print(f'🌐 aiohttp: {aiohttp.__version__}')
"
```

### **Bot Health Check:**
```bash
# Check if bot is responding
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe"

# Check logs
tail -f bot.log
```

---

## 🛠️ Troubleshooting

### **Common Issues:**

#### **Import Errors:**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

#### **Database Connection:**
```bash
# Test MongoDB connection
mongo --eval "db.adminCommand('ping')"

# Check MongoDB status
sudo systemctl status mongodb
```

#### **Bot Token Issues:**
```bash
# Verify token format
python3 -c "
token = 'YOUR_TOKEN_HERE'
if ':' in token and len(token.split(':')[0]) == 10:
    print('✅ Token format valid')
else:
    print('❌ Invalid token format')
"
```

#### **Permission Issues:**
```bash
# Fix file permissions
chmod +x bot.py
chown $USER:$USER -R .
```

### **Log Analysis:**
```bash
# View recent logs
tail -100 bot.log

# Search for errors
grep -i error bot.log

# Monitor real-time
tail -f bot.log | grep -E "(ERROR|WARNING|INFO)"
```

---

## 📦 Package Versions

The bot has been tested with these specific versions:

| Package | Version | Purpose |
|---------|---------|---------|
| python-telegram-bot | 22.3 | Telegram API |
| motor | 3.7.1 | Async MongoDB |
| aiohttp | 3.12.15 | HTTP client |
| pytz | 2025.2 | Timezone handling |
| pycountry | 24.6.1 | Country codes |
| pymongo | 4.10.1 | MongoDB driver |

---

## 🔄 Updates

### **Updating Dependencies:**
```bash
# Update all packages
pip install --upgrade -r requirements.txt

# Update specific package
pip install --upgrade python-telegram-bot
```

### **Bot Updates:**
```bash
# Pull latest code
git pull origin main

# Restart bot
sudo systemctl restart telegram-bot
# OR
pkill -f "python3 bot.py" && python3 bot.py &
```

---

## 🆘 Support

### **Getting Help:**
1. Check logs: `tail -f bot.log`
2. Verify configuration: Review `config.py`
3. Test dependencies: Run verification commands
4. Check MongoDB: Ensure database is accessible
5. Validate bot token: Test with Telegram API

### **Useful Commands:**
```bash
# Bot status
ps aux | grep "python3 bot.py"

# Resource usage
top -p $(pgrep -f "python3 bot.py")

# Network connections
netstat -tulpn | grep python3

# System resources
df -h  # Disk space
free -m  # Memory usage
```

**✅ Your Telegram SMS Bot should now be ready to run!** 🎉