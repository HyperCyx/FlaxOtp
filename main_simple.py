#!/usr/bin/env python3
"""
Simplified Telegram SMS Bot for Python 3.10 compatibility
This version uses a simpler initialization process to avoid ExtBot issues.
"""

import logging
import os
import asyncio
from io import BytesIO, StringIO
from datetime import datetime, timedelta
import csv
import time
import re
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from motor.motor_asyncio import AsyncIOMotorClient
import pytz
import pycountry
import aiohttp

# Import all configurations from config.py
from config import *

# === GLOBAL VARIABLES ===
TIMEZONE = pytz.timezone(TIMEZONE_NAME)
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL))

# Session management - initialize from config
CURRENT_SMS_API_COOKIE = SMS_API_COOKIE
logging.info(f"🔑 Initialized SMS API session from config: {CURRENT_SMS_API_COOKIE[:20]}...{CURRENT_SMS_API_COOKIE[-10:]}")

# Bot state variables
uploaded_csv = None
user_states = {}  # Store user states for country input
manual_numbers = {}  # Store manual numbers for each user
current_user_numbers = {}  # Track current number for each user
user_monitoring_sessions = {}  # Track multiple monitoring sessions per user
active_number_monitors = {}  # Store active monitors for each number

# Performance optimization cache
countries_cache = None
countries_cache_time = None

def get_current_sms_cookie():
    """Get the current active SMS API cookie"""
    return CURRENT_SMS_API_COOKIE

def clear_countries_cache():
    """Clear the countries cache to force refresh"""
    global countries_cache, countries_cache_time
    countries_cache = None
    countries_cache_time = None
    logging.info("Countries cache cleared")

# Import the rest of the functions from the main bot file
import importlib.util
spec = importlib.util.spec_from_file_location("bot_functions", "bot.py")
bot_functions = importlib.util.module_from_spec(spec)

# Copy essential functions
async def send_lol_message(update: Update):
    """Send a fun message when users try to use admin commands"""
    await update.message.reply_text("Lol")

def format_number_display(number):
    """Format number for display with proper spacing and plus sign"""
    # Clean the number first
    clean_num = ''.join(filter(str.isdigit, str(number)))
    
    # Ensure number has + prefix
    if not clean_num.startswith("+"):
        return f"+{clean_num}"
    return clean_num

def number_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Get Number", callback_data="request_number")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    try:
        # Check if user is already verified
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
        
        # New user - show channel join requirement
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
        logging.error(f"Error in start command: {e}")
        await update.message.reply_text("❌ An error occurred. Please try again later.")

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
        logging.error(f"Error in request_number: {e}")
        await query.edit_message_text("❌ Error loading countries. Please try again.")

async def countries_keyboard(db):
    """Generate countries keyboard with caching"""
    global countries_cache, countries_cache_time
    
    # Use cache if available and fresh (5 minutes)
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
    for country_info in countries_data[:20]:  # Limit to first 20 for speed
        country_code = country_info.get("country_code")
        if not country_code:
            continue
            
        display_name = country_info.get("display_name", country_code)
        # Simple flag emoji mapping
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
        
        # Get a random number
        pipeline = [
            {"$match": {"country_code": country_code}},
            {"$sample": {"size": 1}}
        ]
        results = await coll.aggregate(pipeline).to_list(length=1)
        result = results[0] if results else None
        
        if result and "number" in result:
            number = result["number"]
            formatted_number = format_number_display(number)
            
            # Track current number for this user
            user_id = query.from_user.id
            current_user_numbers[user_id] = number
            
            message = f"📞 **Number:** `{formatted_number}`\n\n✅ Number assigned successfully!"
            
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
        logging.error(f"Error in send_number: {e}")
        await query.edit_message_text("❌ Error getting number. Please try again.")

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

async def show_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show SMS for a number (simplified)"""
    query = update.callback_query
    await query.answer()
    
    number = query.data.split('_', 1)[1]
    formatted_number = format_number_display(number)
    
    await query.edit_message_text(
        f"📞 **Number:** `{formatted_number}`\n\n"
        f"📩 **SMS Status:** Checking for messages...\n\n"
        f"ℹ️ This is a simplified version. SMS checking will be implemented in the full version.",
        parse_mode=ParseMode.MARKDOWN
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user joined the channel"""
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            # Store user in database
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
        logging.error(f"Error checking channel membership: {e}")
        await query.answer("❌ Error checking membership. Please try again.", show_alert=True)

# Admin commands (simplified)
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin help"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await send_lol_message(update)
        return
    
    await update.message.reply_text(
        "🔧 **ADMIN COMMANDS (Simplified)**\n\n"
        "This is a simplified version for Python 3.10 compatibility.\n"
        "Main features are working. Full admin panel available in bot.py version."
    )

def main():
    """Main function - simplified for Python 3.10"""
    try:
        logging.info("🚀 Starting simplified bot for Python 3.10...")
        
        # Build application
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Set up database connection
        mongo_client = AsyncIOMotorClient(MONGO_URI)
        db = mongo_client[DB_NAME]
        app.bot_data["db"] = db

        # Register essential handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("admin", admin_help))
        app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
        app.add_handler(CallbackQueryHandler(request_number, pattern="request_number"))
        app.add_handler(CallbackQueryHandler(send_number, pattern="^country_"))
        app.add_handler(CallbackQueryHandler(show_sms, pattern="^sms_"))
        app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
        
        logging.info("✅ Bot initialized successfully")
        logging.info("📱 Bot started and polling...")
        
        # Start polling
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logging.error(f"Bot error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()