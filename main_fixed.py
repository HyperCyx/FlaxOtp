#!/usr/bin/env python3
"""
Telegram SMS Bot - Python 3.10 Compatible Version
Fixed ExtBot initialization issue with manual async setup
"""

import logging
import asyncio
import sys
from datetime import datetime, timedelta
import json
import csv
from io import BytesIO, StringIO
import re
import aiohttp
import pytz
import pycountry

from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from motor.motor_asyncio import AsyncIOMotorClient

# Import configurations
from config import *

# === LOGGING SETUP ===
logging.basicConfig(
    level=getattr(logging, LOGGING_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === GLOBAL VARIABLES ===
TIMEZONE = pytz.timezone(TIMEZONE_NAME)
CURRENT_SMS_API_COOKIE = SMS_API_COOKIE
logger.info(f"🔑 Initialized SMS API session from config: {CURRENT_SMS_API_COOKIE[:20]}...{CURRENT_SMS_API_COOKIE[-10:]}")

# Bot state variables
user_states = {}
manual_numbers = {}
current_user_numbers = {}
user_monitoring_sessions = {}
active_number_monitors = {}
countries_cache = None
countries_cache_time = None
last_api_failure_notification = {}

# Store bot instance globally for background tasks
bot_instance = None

def get_current_sms_cookie():
    """Get the current active SMS API cookie"""
    return CURRENT_SMS_API_COOKIE

def clear_countries_cache():
    """Clear the countries cache to force refresh"""
    global countries_cache, countries_cache_time
    countries_cache = None
    countries_cache_time = None
    logger.info("Countries cache cleared")

def format_number_display(number):
    """Format number for display with proper spacing and plus sign"""
    clean_num = ''.join(filter(str.isdigit, str(number)))
    if not clean_num.startswith("+"):
        return f"+{clean_num}"
    return clean_num

def number_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Get Number", callback_data="request_number")]
    ])

async def send_lol_message(update: Update):
    """Send a fun message when users try to use admin commands"""
    await update.message.reply_text("Lol")

async def notify_admins_api_failure(failure_type):
    """Notify admins about API failures with rate limiting"""
    global last_api_failure_notification
    
    current_time = datetime.now(TIMEZONE)
    if failure_type in last_api_failure_notification:
        time_diff = (current_time - last_api_failure_notification[failure_type]).total_seconds()
        if time_diff < 600:  # 10 minutes
            return
    
    last_api_failure_notification[failure_type] = current_time
    
    failure_messages = {
        "session_expired": "🚨 **SMS API SESSION EXPIRED**\n\nThe SMS API session has expired. Please update the session using `/updatesms` command.",
        "connection_timeout": "⏰ **SMS API CONNECTION TIMEOUT**\n\nThe SMS API is not responding. This might be a temporary network issue.",
        "connection_error": "🔌 **SMS API CONNECTION ERROR**\n\nThere's a connection problem with the SMS API server.",
        "access_blocked": "🚫 **SMS API ACCESS BLOCKED**\n\nDirect script access is not allowed. The session might be invalid.",
    }
    
    message = failure_messages.get(failure_type, f"❌ **SMS API ERROR: {failure_type}**\n\nUnknown API error occurred.")
    message += f"\n\n🕐 **Time:** {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    
    if bot_instance:
        for admin_id in ADMIN_IDS:
            try:
                await bot_instance.send_message(chat_id=admin_id, text=message, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

async def check_sms_for_number(phone_number, date_str):
    """Check SMS for a specific phone number"""
    try:
        url = f"{SMS_API_BASE_URL}{SMS_API_ENDPOINT}"
        headers = {
            'Cookie': f'PHPSESSID={get_current_sms_cookie()}'
        }
        params = {
            'number': phone_number,
            'date': date_str
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    if 'direct script access not allowed' in response_text.lower():
                        asyncio.create_task(notify_admins_api_failure("access_blocked"))
                    else:
                        asyncio.create_task(notify_admins_api_failure(f"HTTP {response.status}"))
                    return None
    except asyncio.TimeoutError:
        asyncio.create_task(notify_admins_api_failure("connection_timeout"))
        return None
    except Exception as e:
        asyncio.create_task(notify_admins_api_failure(f"connection_error: {str(e)}"))
        return None

def extract_otp_from_message(message):
    """Extract OTP from SMS message using configured patterns"""
    if not message:
        return None
    
    for pattern_info in OTP_PATTERNS:
        pattern = pattern_info["pattern"]
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            return matches[0] if isinstance(matches[0], str) else matches[0][0]
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    try:
        db = context.bot_data["db"]
        users_coll = db[USERS_COLLECTION]
        existing_user = await users_coll.find_one({"user_id": user_id})
        
        if existing_user:
            keyboard = number_keyboard()
            await update.message.reply_text(
                "✅ Welcome back! You are already verified.\n\n📞 You can now get phone numbers.",
                reply_markup=keyboard
            )
            return
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Join Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("🔄 Check", callback_data="check_join")]
        ])
        
        welcome_message = f"""
🤖 **Welcome to SMS Number Bot!**

👋 Hello {first_name}!

To use this bot, you need to:
1️⃣ Join our channel 
2️⃣ Click "🔄 Check" to verify

📱 **Features:**
• Get phone numbers from different countries
• Receive SMS and OTP codes instantly
• Real-time monitoring

🔗 Join the channel and click Check to continue!
        """
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user joined the channel"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            db = context.bot_data["db"]
            users_coll = db[USERS_COLLECTION]
            
            user_data = {
                "user_id": user_id,
                "username": query.from_user.username,
                "first_name": query.from_user.first_name,
                "verified_at": datetime.now(TIMEZONE),
                "status": "verified"
            }
            
            await users_coll.insert_one(user_data)
            
            keyboard = number_keyboard()
            await query.edit_message_text(
                "✅ **Verification Successful!**\n\n📞 You can now get phone numbers.",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("❌ Please join the channel first!", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await query.answer("❌ Error checking membership. Please try again.", show_alert=True)

async def request_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle number request"""
    query = update.callback_query
    await query.answer()
    
    try:
        db = context.bot_data["db"]
        keyboard = await countries_keyboard(db)
        
        await query.edit_message_text(
            "🌍 **Select a Country:**\n\nChoose the country for your phone number:",
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Error in request_number: {e}")
        await query.edit_message_text("❌ Error loading countries. Please try again.")

async def countries_keyboard(db):
    """Generate countries keyboard with caching"""
    global countries_cache, countries_cache_time
    
    now = datetime.now()
    if countries_cache and countries_cache_time and (now - countries_cache_time) < timedelta(minutes=5):
        countries_data = countries_cache
    else:
        countries_coll = db[COUNTRIES_COLLECTION]
        countries_data = await countries_coll.find({}).to_list(length=None)
        countries_data.sort(key=lambda x: x.get("display_name", x.get("country_code", "")))
        countries_cache = countries_data
        countries_cache_time = now
    
    buttons = []
    for country_info in countries_data[:20]:  # Limit for performance
        country_code = country_info.get("country_code")
        if not country_code:
            continue
            
        display_name = country_info.get("display_name", country_code)
        flag_map = {
            'pk': '🇵🇰', 'in': '🇮🇳', 'us': '🇺🇸', 'uk': '🇬🇧', 'ca': '🇨🇦',
            'au': '🇦🇺', 'de': '🇩🇪', 'fr': '🇫🇷', 'it': '🇮🇹', 'es': '🇪🇸'
        }
        flag = flag_map.get(country_code.lower(), '🏳️')
        
        buttons.append([InlineKeyboardButton(f"{flag} {display_name}", callback_data=f"country_{country_code}")])
    
    return InlineKeyboardMarkup(buttons)

async def send_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a random number from selected country"""
    query = update.callback_query
    await query.answer()
    country_code = query.data.split('_', 1)[1]
    
    try:
        db = context.bot_data["db"]
        coll = db[COLLECTION_NAME]
        
        # Fast path: Simple random selection
        simple_pipeline = [{"$match": {"country_code": country_code}}, {"$sample": {"size": 1}}]
        results = await coll.aggregate(simple_pipeline).to_list(length=1)
        result = results[0] if results else None
        
        if result and "number" in result:
            number = result["number"]
            formatted_number = format_number_display(number)
            
            user_id = query.from_user.id
            current_user_numbers[user_id] = number
            
            message = f"📞 **Number:** `{formatted_number}`\n\n✅ Number assigned successfully!\n\n⏳ Checking for SMS messages..."
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Check SMS", callback_data=f"sms_{number}")],
                [InlineKeyboardButton("📋 Menu", callback_data="menu")]
            ])
            
            await query.edit_message_text(
                message,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.edit_message_text("❌ No numbers available for this country. Please try another.")
            
    except Exception as e:
        logger.error(f"Error in send_number: {e}")
        await query.edit_message_text("❌ Error getting number. Please try again.")

async def show_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show SMS for a number"""
    query = update.callback_query
    await query.answer()
    
    number = query.data.split('_', 1)[1]
    formatted_number = format_number_display(number)
    
    try:
        # Check for SMS
        date_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        sms_data = await check_sms_for_number(number, date_str)
        
        if sms_data and sms_data.get('aaData'):
            messages = []
            for row in sms_data['aaData'][:5]:  # Show last 5 messages
                if len(row) >= 3:
                    sender = row[1] if len(row) > 1 else "Unknown"
                    message_text = row[2] if len(row) > 2 else ""
                    time_str = row[0] if len(row) > 0 else ""
                    
                    otp = extract_otp_from_message(message_text)
                    if otp:
                        messages.append(f"🔐 **{sender}**: {otp}")
                    else:
                        messages.append(f"📱 **{sender}**: {message_text[:50]}...")
            
            if messages:
                sms_text = "\n\n".join(messages)
                response = f"📞 **Number:** `{formatted_number}`\n\n📩 **Recent SMS:**\n\n{sms_text}"
            else:
                response = f"📞 **Number:** `{formatted_number}`\n\n📩 **SMS Status:** No messages found yet."
        else:
            response = f"📞 **Number:** `{formatted_number}`\n\n📩 **SMS Status:** No messages found yet."
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"sms_{number}")],
            [InlineKeyboardButton("📋 Menu", callback_data="menu")]
        ])
        
        await query.edit_message_text(
            response,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in show_sms: {e}")
        await query.edit_message_text(f"📞 **Number:** `{formatted_number}`\n\n❌ Error checking SMS. Please try again.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu"""
    query = update.callback_query
    await query.answer()
    
    keyboard = number_keyboard()
    await query.edit_message_text(
        "📱 **Main Menu**\n\nSelect an option:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )

# Admin commands
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin help"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await send_lol_message(update)
        return
    
    help_text = """
🔧 **ADMIN COMMANDS**

📊 **Statistics:**
• `/stats` - Show bot statistics
• `/list` - List all numbers
• `/monitoring` - Check monitoring status

🔧 **Management:**
• `/add` - Add numbers/countries
• `/delete` - Delete country
• `/cleanup` - Clean used numbers
• `/checkapi` - Check SMS API status

🛠️ **Maintenance:**
• `/updatesms` - Update SMS session
• `/reloadsession` - Reload session from config
• `/clearcache` - Clear countries cache

ℹ️ **Other:**
• `/admin` - Show this help
    """
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def check_api_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check SMS API connection status"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await send_lol_message(update)
        return
    
    try:
        test_number = "1234567890"
        date_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
        
        start_time = datetime.now()
        result = await check_sms_for_number(test_number, date_str)
        end_time = datetime.now()
        
        response_time = (end_time - start_time).total_seconds()
        
        if result is not None:
            status = "✅ **Connected**"
            details = f"Response time: {response_time:.2f}s"
        else:
            status = "❌ **Connection Failed**"
            details = "Check session cookie"
        
        message = f"""
🔌 **SMS API Status Check**

**Status:** {status}
**Cookie:** `{get_current_sms_cookie()[:20]}...`
**Endpoint:** `{SMS_API_BASE_URL}{SMS_API_ENDPOINT}`
**Details:** {details}

**Time:** {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')}
        """
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ **API Check Failed**\n\nError: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )

async def background_otp_cleanup_task():
    """Background task to cleanup OTPs (simplified version)"""
    logger.info("🔄 Background OTP cleanup task started - checking every minute")
    
    while True:
        try:
            await asyncio.sleep(60)  # Wait 1 minute
            logger.debug("Background cleanup task running...")
            # Simplified cleanup - full implementation would go here
            
        except Exception as e:
            logger.error(f"Background cleanup task error: {e}")
            await asyncio.sleep(60)

async def main_async():
    """Main async function with proper initialization"""
    global bot_instance
    
    try:
        logger.info("🚀 Starting Telegram Bot...")
        
        # Create bot instance manually
        bot_instance = Bot(token=TOKEN)
        await bot_instance.initialize()
        
        # Create application with the initialized bot
        app = Application.builder().bot(bot_instance).build()
        
        # Set up database connection
        mongo_client = AsyncIOMotorClient(MONGO_URI)
        db = mongo_client[DB_NAME]
        app.bot_data["db"] = db
        
        # Register handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("admin", admin_help))
        app.add_handler(CommandHandler("checkapi", check_api_connection))
        app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
        app.add_handler(CallbackQueryHandler(request_number, pattern="request_number"))
        app.add_handler(CallbackQueryHandler(send_number, pattern="^country_"))
        app.add_handler(CallbackQueryHandler(show_sms, pattern="^sms_"))
        app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
        
        logger.info("✅ Bot initialized successfully")
        
        # Start background tasks
        background_task = asyncio.create_task(background_otp_cleanup_task())
        
        # Initialize and start the application
        await app.initialize()
        await app.start()
        
        logger.info("📱 Bot started and polling...")
        
        # Start polling
        await app.updater.start_polling(drop_pending_updates=True)
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'app' in locals():
            await app.stop()
            await app.shutdown()
        if bot_instance:
            await bot_instance.shutdown()

def main():
    """Main entry point"""
    try:
        if sys.version_info >= (3, 7):
            asyncio.run(main_async())
        else:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main_async())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()