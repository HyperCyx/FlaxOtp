# 🔧 Python 3.10 + Ubuntu 22.04 Fix Guide

## 🚨 **Problem:**
```
RuntimeError: ExtBot is not properly initialized. Call `ExtBot.initialize` before accessing this property.
```

## ✅ **Solutions:**

### **Option 1: Use Compatible Telegram Library Version**

```bash
# Uninstall current version
pip uninstall python-telegram-bot telegram

# Install compatible version for Python 3.10
pip install python-telegram-bot==20.8

# Restart your bot
python3 main.py
```

### **Option 2: Use the Simplified Version**

```bash
# Use the simplified bot that avoids ExtBot issues
python3 main_simple.py
```

### **Option 3: Upgrade to Python 3.11+**

```bash
# Install Python 3.11
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create new virtual environment
python3.11 -m venv venv_311
source venv_311/bin/activate

# Install requirements
pip install -r requirements.txt

# Run bot
python3 main.py
```

---

## 🛠️ **Quick Fix for Your Current Setup:**

### **Step 1: Update Requirements**
```bash
cd ~/Flex
pip uninstall python-telegram-bot
pip install python-telegram-bot==20.8
```

### **Step 2: Use Fixed main.py**
Your current `main.py` has been updated with compatibility fixes.

### **Step 3: Test the Bot**
```bash
python3 main.py
```

---

## 📋 **What Was Fixed:**

### **1. Initialization Method:**
- **Old:** `app.run_polling()` with post_init
- **New:** Direct initialization without complex async setup

### **2. Background Tasks:**
- **Old:** Immediate background task creation
- **New:** Delayed start using job queue

### **3. Error Handling:**
- **Old:** Complex exception handling
- **New:** Simple try-catch with better error messages

### **4. Library Compatibility:**
- **Old:** Latest telegram library (22.3)
- **New:** Compatible version (20.8) for Python 3.10

---

## 🎯 **Expected Output After Fix:**

```
INFO:root:🔑 Initialized SMS API session from config: PHPSESSID=jfi9fn51cr...
INFO:root:Bot started and polling...
INFO:telegram.ext.Application:Application started
INFO:httpx:HTTP Request: POST https://api.telegram.org/bot.../getMe "HTTP/1.1 200 OK"
```

**No more ExtBot initialization errors!**

---

## 🚀 **Alternative: Docker Solution**

If you continue having issues, use Docker:

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python3", "main.py"]
EOF

# Build and run
docker build -t telegram-bot .
docker run -d --name sms-bot telegram-bot
```

---

## ✅ **Verification:**

### **Test Commands:**
```bash
# 1. Check Python version
python3 --version

# 2. Check telegram library
python3 -c "import telegram; print(telegram.__version__)"

# 3. Test bot startup
timeout 10 python3 main.py

# 4. Check for errors
echo "If no ExtBot errors appear, you're good to go!"
```

---

## 🆘 **If Still Having Issues:**

### **Complete Reset:**
```bash
# 1. Remove virtual environment
rm -rf venv

# 2. Create fresh environment
python3 -m venv venv
source venv/bin/activate

# 3. Install exact versions
pip install python-telegram-bot==20.8 motor==3.7.1 aiohttp==3.12.15 pytz==2025.2 pycountry==24.6.1

# 4. Run bot
python3 main.py
```

### **Environment Check:**
```bash
# Check your exact setup
python3 --version
pip list | grep telegram
uname -a
```

**✅ This should resolve the ExtBot initialization issue on Python 3.10!**