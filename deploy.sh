#!/bin/bash

# Telegram Bot Deployment Script for Koyeb
# This script helps build and deploy the bot to Koyeb

set -e

echo "🚀 Starting Telegram Bot deployment to Koyeb..."

# Check if required files exist
if [ ! -f "bot.py" ]; then
    echo "❌ Error: bot.py not found!"
    exit 1
fi

if [ ! -f "config.py" ]; then
    echo "❌ Error: config.py not found!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found!"
    exit 1
fi

echo "✅ All required files found"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t telegram-bot .

echo "✅ Docker image built successfully"

# Check if Koyeb CLI is installed
if ! command -v koyeb &> /dev/null; then
    echo "⚠️  Koyeb CLI not found. Please install it first:"
    echo "   curl -fsSL https://cli.koyeb.com/install.sh | bash"
    echo ""
    echo "📋 Manual deployment steps:"
    echo "1. Push your code to GitHub"
    echo "2. Go to https://app.koyeb.com"
    echo "3. Create a new app"
    echo "4. Connect your GitHub repository"
    echo "5. Use the Dockerfile for deployment"
    echo "6. Set environment variables if needed"
    exit 0
fi

# Deploy to Koyeb
echo "🚀 Deploying to Koyeb..."
koyeb app init telegram-bot --docker ./Dockerfile --ports 8000:http

echo "✅ Deployment completed!"
echo "🌐 Your bot should be running on Koyeb now"
echo "📊 Check the status at: https://app.koyeb.com"