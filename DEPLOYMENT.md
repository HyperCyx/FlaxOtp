# Telegram Bot Deployment Guide for Koyeb

This guide will help you deploy your Telegram bot to Koyeb using Docker.

## Prerequisites

- A Koyeb account (sign up at https://app.koyeb.com)
- Your code pushed to a GitHub repository
- Docker installed locally (for testing)

## Quick Deployment

### Option 1: Using the Deployment Script

1. Make sure all files are committed to your repository
2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

### Option 2: Manual Deployment

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Add Docker deployment files"
   git push origin main
   ```

2. **Deploy to Koyeb**
   - Go to https://app.koyeb.com
   - Click "Create App"
   - Choose "GitHub" as your source
   - Select your repository
   - Choose "Docker" as the deployment method
   - Koyeb will automatically detect the Dockerfile
   - Click "Deploy"

## Configuration

### Environment Variables (Optional)

If you need to override configuration values, you can set these environment variables in Koyeb:

- `TOKEN`: Your Telegram bot token
- `MONGO_URI`: MongoDB connection string
- `SMS_API_COOKIE`: SMS API session cookie
- `ADMIN_IDS`: Comma-separated list of admin user IDs

### Setting Environment Variables in Koyeb

1. Go to your app in the Koyeb dashboard
2. Click on "Settings" → "Environment variables"
3. Add your variables as needed

## Monitoring

### Health Checks

The Dockerfile includes a health check that runs every 30 seconds. Koyeb will automatically restart your app if it becomes unhealthy.

### Logs

View your bot logs in the Koyeb dashboard:
1. Go to your app
2. Click on "Logs" tab
3. Monitor for any errors or issues

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if the bot token is correct
   - Verify MongoDB connection
   - Check logs for errors

2. **Build failures**
   - Ensure all dependencies are in `requirements.txt`
   - Check that the Dockerfile is in the root directory
   - Verify Python version compatibility

3. **Memory issues**
   - The bot is configured with 512MB RAM
   - Increase memory allocation if needed in Koyeb settings

### Debugging

1. **Local testing**
   ```bash
   docker build -t telegram-bot .
   docker run -it telegram-bot
   ```

2. **Check logs**
   ```bash
   # If using Koyeb CLI
   koyeb app logs <app-name>
   ```

## Security Notes

- The Dockerfile runs the bot as a non-root user for security
- Sensitive data should be stored as environment variables
- Never commit API keys or tokens to your repository

## Performance Optimization

- The bot is configured to run a single instance (min: 1, max: 1)
- For high traffic, consider increasing the max instances
- Monitor resource usage in the Koyeb dashboard

## Support

If you encounter issues:
1. Check the Koyeb documentation: https://docs.koyeb.com
2. Review the bot logs for error messages
3. Ensure all dependencies are properly installed