import os
import asyncio
import logging
import threading
import time
from flask import Flask, jsonify

# Import the bot's main function
from bot import main as bot_main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Global variable to store the bot task
bot_task = None
start_time = None

@app.route('/')
def home():
    return jsonify({
        "message": "Telegram Bot is running", 
        "status": "active",
        "endpoints": {
            "health": "/health",
            "status": "/status"
        }
    })

@app.route('/health')
def health_check():
    """Health check endpoint for Koyeb"""
    bot_running = bot_task is not None and not bot_task.done() if bot_task else False
    return jsonify({
        "status": "healthy",
        "bot_running": bot_running,
        "timestamp": time.time()
    })

@app.route('/status')
def status_handler():
    """Status endpoint"""
    bot_status = "running" if bot_task and not bot_task.done() else "stopped"
    uptime = time.time() - start_time if start_time else 0
    return jsonify({
        "bot_status": bot_status,
        "uptime": uptime
    })

def run_bot():
    """Run the Telegram bot in a separate thread"""
    global bot_task
    try:
        logger.info("Starting Telegram bot...")
        # Run the bot in a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_task = loop.run_until_complete(bot_main())
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_task = None

def start_bot_background():
    """Start the bot in a background thread"""
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot started in background thread")

def run_flask():
    """Run the Flask web server"""
    global start_time
    start_time = time.time()
    
    # Start the bot in background
    start_bot_background()
    
    # Get port from environment variable (Koyeb sets PORT)
    port = int(os.environ.get('PORT', 8080))
    
    logger.info(f"Starting Flask web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    run_flask()