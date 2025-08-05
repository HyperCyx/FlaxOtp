# Telegram Bot - Koyeb Deployment Guide

## 🚀 Quick Deploy to Koyeb

This Telegram bot is now ready for production deployment on Koyeb.com with:
- ✅ Health check endpoint on port 8080
- ✅ Proper signal handling
- ✅ Production-optimized configuration
- ✅ Automatic restarts on failure

## 📋 Pre-Deployment Checklist

### Required Services
Ensure you have accounts and credentials for:
- [x] Telegram Bot (BotFather token) ✅ CONFIGURED
- [x] MongoDB Atlas (or compatible MongoDB service) ✅ CONFIGURED  
- [x] SMS API service ✅ CONFIGURED
- [ ] Koyeb.com account

### Environment Variables for Koyeb
Configure these exact values in your Koyeb service environment variables:

```bash
# === TELEGRAM CONFIGURATION ===
TOKEN=8018522823:AAEF9LBO6W6OlsL__grsUURLgX2PIClws2Q
CHANNEL_ID=-1002598958220
CHANNEL_LINK=https://t.me/+CgIjCeBinD5hMDI1

# === DATABASE CONFIGURATION ===
MONGO_URI=mongodb+srv://nooblofi0:YO57TmRbkXiGYBCo@noob.gyu06tt.mongodb.net/?retryWrites=true&w=majority
DB_NAME=TellaBot
COLLECTION_NAME=numbers
COUNTRIES_COLLECTION=countries
USERS_COLLECTION=verified_users

# === SMS API CONFIGURATION ===
SMS_API_BASE_URL=http://51.83.103.80
SMS_API_ENDPOINT=/ints/agent/res/data_smscdr.php
SMS_API_COOKIE=PHPSESSID=o38eibu9l81kk5iek0l3sq65ke

# === ADMIN CONFIGURATION ===
ADMIN_IDS=1211362365

# === OTP MONITORING CONFIGURATION ===
OTP_CHECK_INTERVAL=5
OTP_TIMEOUT=300
MORNING_CALL_TIMEOUT=120

# === APPLICATION CONFIGURATION ===
TIMEZONE_NAME=Asia/Riyadh
LOGGING_LEVEL=INFO
PORT=8080

# === ALTERNATIVE SMS API CONFIGURATIONS ===
ALT_SMS_API_BASE_URL_1=http://51.83.103.80
ALT_SMS_API_COOKIE_1=PHPSESSID=o38eibu9l81kk5iek0l3sq65ke
ALT_SMS_API_BASE_URL_2=http://51.83.103.80
ALT_SMS_API_COOKIE_2=PHPSESSID=o38eibu9l81kk5iek0l3sq65ke
```

## 🔧 Koyeb Deployment Steps

### Step 1: Create New Service
1. Log into your Koyeb dashboard at https://app.koyeb.com
2. Click "Create Service" 
3. Choose "GitHub" as source
4. Connect your repository containing the Dockerfile

### Step 2: Configure Build Settings
- **Builder**: Docker
- **Dockerfile path**: `./Dockerfile` 
- **Build command**: (leave empty - handled by Dockerfile)
- **Build context**: Repository root

### Step 3: Configure Service Settings
- **Port**: 8080 (REQUIRED)
- **Health check path**: `/health`
- **Health check protocol**: HTTP
- **Instance type**: Small (512MB RAM recommended)

### Step 4: Environment Variables (CRITICAL)
In the Koyeb environment variables section, add ALL variables listed above.

**Quick Setup Method:**
1. Click "Bulk Edit" in environment variables
2. Copy-paste the entire environment block above
3. Verify all values are correct

### Step 5: Health Check Configuration
```yaml
Health Check Settings:
- Protocol: HTTP
- Path: /health
- Port: 8080
- Grace period: 90 seconds (bot needs time to connect to MongoDB/Telegram)
- Interval: 30 seconds
- Timeout: 10 seconds
- Restart limit: 3
```

### Step 6: Final Deployment Settings
- **Scaling**: 1 instance (Telegram bots don't need horizontal scaling)
- **Region**: Choose closest to your users (fra, was, or sin recommended)
- **Auto-deploy**: Enable for automatic updates from Git

## 🏥 Health Check Endpoint

Your bot includes a built-in health check server on port 8080:

**Health Check URL:** `https://your-app-name.koyeb.app/health`

**Response:**
```json
{
  "status": "healthy",
  "message": "Bot Active",
  "timestamp": "2024-12-19T10:30:00Z",
  "service": "telegram-bot"
}
```

## 🔍 Monitoring & Verification

### Post-Deployment Checks
1. **Health endpoint**: Visit `https://your-app.koyeb.app/health`
2. **Bot commands**: Test in Telegram with `/status`
3. **API connectivity**: Use `/checkapi` command
4. **Database**: Verify with `/stats` command

### Key Log Messages to Monitor
```bash
✅ "Health check server started on port 8080" - Server ready
✅ "Bot started and polling..." - Telegram connection active
✅ "🔑 Initialized SMS API session" - SMS API connected
✅ Database connection established
❌ "Bot error:" - Application issues
❌ "SMS API error:" - External API problems
```

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

#### 1. Health Check Failing
**Symptoms:** Service shows "Unhealthy" status
**Solutions:**
- Increase grace period to 120 seconds
- Check logs for startup errors
- Verify port 8080 is exposed
- Test health endpoint directly

#### 2. Bot Not Responding to Commands
**Symptoms:** No response in Telegram
**Check:**
- Telegram token validity
- Bot permissions in target channel
- Admin ID configuration
- Network connectivity

#### 3. Database Connection Issues  
**Symptoms:** "Database connection failed" in logs
**Solutions:**
- Verify MongoDB URI format
- Check MongoDB Atlas IP whitelist (add 0.0.0.0/0 for Koyeb)
- Ensure database user has read/write permissions
- Test connection string locally

#### 4. SMS API Problems
**Symptoms:** OTP detection not working
**Check:**
- SMS API server accessibility
- Cookie validity and format
- API endpoint availability
- Use `/checkapi` command for diagnostics

### Emergency Commands
- `/checkapi` - Verify SMS API connection
- `/status` - Get current bot status  
- `/stats` - View system statistics
- `/monitoring` - Check monitoring sessions

## 🔐 Security Considerations

### Production Security Checklist
- [x] Sensitive tokens in environment variables (not code)
- [ ] MongoDB Atlas IP whitelist configured
- [ ] SMS API access properly secured
- [ ] Telegram webhook URL secured (if switching from polling)
- [ ] Regular credential rotation scheduled

### Network Security
- MongoDB: Configure IP whitelist in Atlas console
- SMS API: Monitor for unauthorized access
- Telegram: Verify bot token scope and permissions

## 📊 Performance Optimization

### Resource Monitoring
Monitor these metrics in Koyeb dashboard:
- **CPU Usage**: Should stay below 50% normally
- **Memory Usage**: ~200-400MB typical usage
- **Response Time**: Health checks < 1s
- **Uptime**: Target 99.9% availability

### Scaling Recommendations
- **Current Setup**: Single instance sufficient
- **High Load**: Vertical scaling (larger instance)
- **Never**: Horizontal scaling (bots maintain state)

## 🔄 Deployment Verification

### Step-by-Step Verification
1. **Service Status**: Green in Koyeb dashboard
2. **Health Check**: `curl https://your-app.koyeb.app/health`
3. **Telegram Test**: Send `/start` to bot
4. **API Test**: Use `/checkapi` command
5. **Database Test**: Use `/stats` command
6. **OTP Test**: Request a number and verify OTP detection

### Success Indicators
- ✅ Health endpoint returns "Bot Active" 
- ✅ Telegram commands respond immediately
- ✅ SMS API status shows "Connected"
- ✅ MongoDB operations successful
- ✅ No error logs for 5+ minutes

## 🚀 Go Live Checklist

### Pre-Production
- [ ] All environment variables configured
- [ ] Health check responding correctly
- [ ] Database connectivity verified
- [ ] SMS API integration working
- [ ] Admin commands functional
- [ ] Telegram channel access confirmed

### Production Ready
- [ ] External monitoring configured (optional)
- [ ] Backup procedures documented
- [ ] Incident response plan ready
- [ ] Performance baselines established

## 📞 Support & Maintenance

### Bot Management Commands
- `/admin` - View all admin commands
- `/stats` - System statistics and health
- `/checkapi` - SMS API diagnostics
- `/monitoring` - Active monitoring sessions
- `/help` - User command reference

### Koyeb Resources  
- [Koyeb Dashboard](https://app.koyeb.com)
- [Health Checks Documentation](https://www.koyeb.com/docs/run-and-scale/health-checks)
- [Deployment Troubleshooting](https://www.koyeb.com/docs/build-and-deploy/troubleshooting-tips)

### Update Procedures
1. **Code Changes**: Push to GitHub → Auto-deploy (if enabled)
2. **Environment Variables**: Update in Koyeb dashboard → Redeploy
3. **Dependencies**: Update requirements.txt → Push to trigger rebuild
4. **Configuration**: Modify config values via environment variables

---

## 🎯 **DEPLOYMENT STATUS**

**Configuration**: ✅ **COMPLETE** - All values configured  
**Health Check**: ✅ **READY** - Port 8080 with `/health` endpoint  
**Message**: 🤖 **"Bot Active"** - Displays on successful health check  
**Environment**: ✅ **PRODUCTION READY** - Optimized for Koyeb deployment

**Next Step**: Create your Koyeb service and deploy! 🚀