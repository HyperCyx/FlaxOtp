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
- [ ] Telegram Bot (BotFather token)
- [ ] MongoDB Atlas (or compatible MongoDB service)
- [ ] SMS API service
- [ ] Koyeb.com account

### Environment Variables
You'll need to configure these in Koyeb:

```bash
# Telegram Configuration
TOKEN=your_telegram_bot_token
CHANNEL_ID=your_channel_id
CHANNEL_LINK=your_channel_link

# Database Configuration
MONGO_URI=your_mongodb_connection_string
DB_NAME=TellaBot
COLLECTION_NAME=numbers
COUNTRIES_COLLECTION=countries
USERS_COLLECTION=verified_users

# SMS API Configuration
SMS_API_BASE_URL=your_sms_api_url
SMS_API_ENDPOINT=/ints/agent/res/data_smscdr.php
SMS_API_COOKIE=your_api_cookie

# Admin Configuration
ADMIN_IDS=1211362365  # Comma-separated if multiple

# Application Configuration
LOGGING_LEVEL=INFO
TIMEZONE_NAME=Asia/Riyadh
PORT=8080
```

## 🔧 Koyeb Deployment Steps

### Step 1: Create New Service
1. Log into your Koyeb dashboard
2. Click "Create Service"
3. Choose "GitHub" as source
4. Connect your repository

### Step 2: Configure Build Settings
- **Builder**: Docker
- **Dockerfile path**: `./Dockerfile`
- **Build command**: (leave empty - handled by Dockerfile)

### Step 3: Configure Service Settings
- **Port**: 8080
- **Health check path**: `/health`
- **Health check protocol**: HTTP

### Step 4: Environment Variables
Add all the environment variables listed above in the Koyeb environment variables section.

### Step 5: Health Check Configuration
```yaml
Health Check Settings:
- Protocol: HTTP
- Path: /health
- Port: 8080
- Grace period: 60 seconds
- Interval: 30 seconds
- Timeout: 10 seconds
- Restart limit: 3
```

### Step 6: Resource Configuration
Recommended settings:
- **Instance type**: Small (512MB RAM, 0.5 vCPU)
- **Scaling**: 1 instance (bots don't typically need horizontal scaling)
- **Region**: Choose closest to your users

## 🏥 Health Check Endpoint

The deployment includes a built-in health check server that responds on port 8080:

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "message": "Bot Active",
  "timestamp": "2024-01-15T10:30:00Z",
  "service": "telegram-bot"
}
```

## 🔍 Monitoring & Logs

### View Logs
```bash
# In Koyeb dashboard, go to your service -> Logs tab
# Or use Koyeb CLI:
koyeb logs <service-name>
```

### Health Status
- Monitor via Koyeb dashboard
- Check `/health` endpoint directly
- Use external monitoring services (UptimeRobot, etc.)

## 🚨 Troubleshooting

### Common Issues

#### Health Check Failing
- Check if port 8080 is exposed
- Verify health endpoint responds: `curl https://your-app.koyeb.app/health`
- Check application logs for startup errors

#### Bot Not Responding
- Verify Telegram token is correct
- Check MongoDB connection
- Ensure admin IDs are set correctly

#### Database Connection Issues
- Verify MongoDB URI format
- Check network connectivity
- Ensure database user has proper permissions

### Log Analysis
Monitor these log patterns:
```
✅ "Health check server started on port 8080" - Health server ready
✅ "Bot started and polling..." - Telegram bot ready
❌ "Bot error:" - Application errors
❌ "SMS API error:" - External API issues
```

## 🔐 Security Best Practices

### Environment Variables
- Never commit sensitive data to Git
- Use Koyeb's secret management
- Rotate API keys regularly

### Network Security
- MongoDB should have IP whitelist
- Use strong passwords
- Enable 2FA on all accounts

## 📊 Performance Optimization

### Resource Monitoring
- Monitor CPU/Memory usage in Koyeb dashboard
- Scale up if consistently above 80% usage
- Bot typically uses minimal resources

### Database Optimization
- Index frequently queried fields
- Clean up old data periodically
- Monitor MongoDB Atlas metrics

## 🚀 Production Deployment

### Final Checklist
- [ ] All environment variables configured
- [ ] Health check endpoint responding
- [ ] Bot responding to Telegram commands
- [ ] Database connectivity verified
- [ ] SMS API integration working
- [ ] Monitoring/alerting configured

### Post-Deployment
1. Test all bot commands
2. Verify monitoring data flows
3. Set up external monitoring
4. Configure backup procedures
5. Document operational procedures

## 📞 Support

### Bot Commands for Health Check
- `/checkapi` - Check SMS API status
- `/status` - Get bot status
- `/stats` - View usage statistics

### Koyeb Resources
- [Koyeb Documentation](https://www.koyeb.com/docs)
- [Health Checks Guide](https://www.koyeb.com/docs/run-and-scale/health-checks)
- [Deployment Troubleshooting](https://www.koyeb.com/docs/build-and-deploy/troubleshooting-tips)

## 🔄 Updates & Maintenance

### Updating the Bot
1. Push changes to GitHub
2. Koyeb will auto-deploy (if configured)
3. Monitor health checks during deployment
4. Verify functionality post-update

### Backup Strategy
- MongoDB: Use Atlas automated backups
- Configuration: Store in version control
- Logs: Use Koyeb log exporter if needed

---

**Status**: ✅ Ready for Production Deployment
**Health Check**: ✅ Port 8080 - `/health` endpoint
**Message**: 🤖 Bot Active