# 🤖 Telegram SMS Bot

An advanced Telegram bot for managing phone numbers and monitoring SMS/OTP messages with real-time notifications.

## 🌟 Features

### **📱 User Features:**
- **Number Requesting**: Get phone numbers from different countries
- **Real-time OTP Monitoring**: Automatic SMS monitoring with 2-minute timeout
- **OTP Detection**: Advanced pattern matching for various OTP formats
- **User Verification**: Channel membership requirement with caching
- **Interactive Interface**: Inline keyboards for easy navigation

### **🔧 Admin Features:**
- **Number Management**: Add, delete, and organize phone numbers
- **CSV Upload**: Bulk import numbers from CSV files
- **Database Statistics**: Real-time stats and monitoring
- **SMS API Management**: Session handling with auto-recovery
- **Background Cleanup**: Automatic number cleanup when OTPs received
- **Admin Notifications**: Real-time alerts for API issues

### **🛡️ Advanced Features:**
- **Session Management**: Automatic SMS API session reload
- **Background Tasks**: Continuous OTP monitoring and cleanup
- **Error Handling**: Comprehensive error detection and recovery
- **Rate Limiting**: Smart notification throttling
- **Multi-admin Support**: Multiple administrator management
- **Cache Management**: User verification caching system

---

## 📋 Quick Start

### **1. Install Dependencies**
```bash
pip3 install -r requirements.txt
```

### **2. Run Installation Test**
```bash
python3 test_installation.py
```

### **3. Configure Bot**
Edit `config.py` with your settings:
- Telegram bot token
- MongoDB connection
- SMS API credentials
- Admin user IDs

### **4. Start Bot**
```bash
python3 bot.py
```

---

## 📖 Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[Requirements](requirements.txt)** - Python dependencies
- **[Configuration](config.py)** - Bot configuration file

---

## 🎯 Commands

### **👤 User Commands:**
- `/start` - Start bot and verify channel membership

### **👨‍💼 Admin Commands:**

#### **Number Management:**
- `/add` - Add numbers manually or upload CSV
- `/list [country]` - List available numbers
- `/delete <country>` - Delete numbers by country
- `/deleteall` - Delete all numbers (with confirmation)
- `/countrynumbers` - Check numbers per country

#### **Monitoring & Control:**
- `/stats` - Show database statistics
- `/monitoring` - Check active OTP monitoring sessions
- `/cleanup` - Manually clean numbers with OTPs
- `/forceotp <number>` - Force OTP check for specific number

#### **API & Session Management:**
- `/checkapi` - Test SMS API connection
- `/updatesms <session>` - Update SMS API session
- `/reloadsession` - Reload session from config file

#### **User Management:**
- `/resetnumber` - Reset user's current number
- `/morningcalls` - Show user's active calls

#### **System:**
- `/admin` - Show admin help and command list
- `/test` - Developer testing commands

---

## 🔧 Technical Specifications

### **Dependencies:**
- **Python**: 3.8+ (3.11+ recommended)
- **Database**: MongoDB 4.4+
- **Libraries**: See [requirements.txt](requirements.txt)

### **Architecture:**
- **Async/Await**: Full asynchronous operation
- **Background Tasks**: Continuous monitoring and cleanup
- **Session Management**: Automatic API session handling
- **Error Recovery**: Comprehensive error handling and recovery

### **Security:**
- **Admin Protection**: Command-level access control
- **Channel Verification**: Required membership verification
- **Session Security**: Secure API session management
- **Rate Limiting**: Prevents spam and abuse

---

## 📊 Database Structure

### **Collections:**
- **`numbers`** - Available phone numbers
- **`countries`** - Country information and counters
- **`verified_users`** - Verified user cache

### **Indexes:**
- Number lookup optimization
- Country-based filtering
- User verification queries

---

## 🚀 Deployment

### **Development:**
```bash
python3 bot.py
```

### **Production (with systemd):**
```bash
sudo cp telegram-bot.service /etc/systemd/system/
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### **Docker:**
```bash
docker build -t telegram-sms-bot .
docker run -d --name sms-bot telegram-sms-bot
```

---

## 🔍 Monitoring

### **Health Checks:**
```bash
# Check bot status
ps aux | grep "python3 bot.py"

# View logs
tail -f bot.log

# Test installation
python3 test_installation.py
```

### **API Monitoring:**
- Real-time SMS API health monitoring
- Automatic session refresh on expiry
- Admin notifications for failures
- Connection timeout handling

---

## 🛠️ Configuration

### **Required Settings:**
```python
# Telegram Configuration
TOKEN = "your_bot_token"
CHANNEL_ID = -1001234567890
ADMIN_IDS = {your_user_id}

# Database Configuration
MONGO_URI = "mongodb://localhost:27017"

# SMS API Configuration
SMS_API_BASE_URL = "http://your-sms-panel.com"
SMS_API_COOKIE = "PHPSESSID=your_session"
```

### **Optional Settings:**
- Timezone configuration
- Logging levels
- Cache directories
- Monitoring intervals

---

## 📈 Performance

### **Optimizations:**
- **Connection Pooling**: Efficient database connections
- **Async Operations**: Non-blocking I/O operations
- **Background Processing**: Separate cleanup tasks
- **Memory Management**: Efficient user state handling

### **Scalability:**
- **Multi-user Support**: Concurrent user handling
- **Database Indexing**: Optimized queries
- **Session Caching**: Reduced API calls
- **Error Recovery**: Automatic failure handling

---

## 🆘 Troubleshooting

### **Common Issues:**

#### **Bot Not Starting:**
1. Check Python version (3.8+)
2. Verify dependencies installed
3. Validate config.py settings
4. Check bot token format

#### **Database Connection:**
1. Ensure MongoDB is running
2. Verify connection string
3. Check network connectivity
4. Validate credentials

#### **SMS API Issues:**
1. Test connection with `/checkapi`
2. Update session with `/updatesms`
3. Check API endpoint URL
4. Verify session cookie format

#### **OTP Not Detected:**
1. Check SMS API connectivity
2. Verify OTP patterns in config
3. Test with `/forceotp` command
4. Check background cleanup task

---

## 📝 Changelog

### **Latest Version:**
- ✅ Advanced session management with auto-recovery
- ✅ Background OTP cleanup every minute
- ✅ Admin notification system for API failures
- ✅ Comprehensive error handling and logging
- ✅ Change button temporarily suspended
- ✅ Enhanced user verification system
- ✅ Rate-limited admin notifications

### **Previous Features:**
- Real-time OTP monitoring
- Multi-country support
- CSV bulk import
- User verification system
- Database statistics
- Session management

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

### **Getting Help:**
1. Check [Installation Guide](INSTALLATION.md)
2. Run `python3 test_installation.py`
3. Review logs with `tail -f bot.log`
4. Test configuration with `/checkapi`

### **Reporting Issues:**
- Provide bot logs
- Include configuration (sanitized)
- Describe expected vs actual behavior
- Include system information

---

**🎉 Ready to manage your SMS operations with style!** 

*Built with ❤️ for efficient SMS and OTP management*