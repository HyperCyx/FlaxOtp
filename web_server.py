import os
import asyncio
import logging
from aiohttp import web
import threading
import time

# Import the bot's main function
from bot import main as bot_main

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable to store the bot task
bot_task = None

async def health_check(request):
    """Health check endpoint for Koyeb"""
    return web.json_response({
        "status": "healthy",
        "bot_running": bot_task is not None and not bot_task.done(),
        "timestamp": time.time()
    })

async def root_handler(request):
    """Root endpoint"""
    return web.json_response({
        "message": "Telegram Bot is running",
        "status": "active",
        "endpoints": {
            "health": "/health",
            "status": "/status"
        }
    })

async def status_handler(request):
    """Status endpoint"""
    bot_status = "running" if bot_task and not bot_task.done() else "stopped"
    return web.json_response({
        "bot_status": bot_status,
        "uptime": time.time() - start_time if 'start_time' in globals() else 0
    })

async def start_bot():
    """Start the Telegram bot in a separate task"""
    global bot_task
    try:
        logger.info("Starting Telegram bot...")
        bot_task = asyncio.create_task(bot_main())
        await bot_task
    except Exception as e:
        logger.error(f"Bot error: {e}")
        bot_task = None

async def init_app():
    """Initialize the web application"""
    app = web.Application()
    
    # Add routes
    app.router.add_get('/', root_handler)
    app.router.add_get('/health', health_check)
    app.router.add_get('/status', status_handler)
    
    # Start the bot when the app starts
    app.on_startup.append(start_bot_background)
    
    return app

def start_bot_background(app):
    """Start the bot in a background thread"""
    def run_bot():
        try:
            asyncio.run(bot_main())
        except Exception as e:
            logger.error(f"Bot background error: {e}")
    
    # Start bot in a separate thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("Bot started in background thread")

async def main():
    """Main function to start the web server"""
    global start_time
    start_time = time.time()
    
    # Get port from environment variable (Koyeb sets PORT)
    port = int(os.environ.get('PORT', 8000))
    
    app = await init_app()
    
    logger.info(f"Starting web server on port {port}")
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Web server started on http://0.0.0.0:{port}")
    
    # Keep the server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down web server...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())