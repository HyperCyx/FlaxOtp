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

# Bot state variables
uploaded_csv = None
user_states = {}  # Store user states for country input
manual_numbers = {}  # Store manual numbers for each user
current_user_numbers = {}  # Track current number for each user
user_monitoring_sessions = {}  # Track multiple monitoring sessions per user
active_number_monitors = {}  # Store active monitors for each number

# === UTILITY FUNCTIONS ===
def extract_otp_from_message(message):
    """Extract OTP from SMS message using patterns from config"""
    if not message:
        return None
    
    message_lower = message.lower()
    logging.info(f"Extracting OTP from message: {message}")
    
    for pattern in OTP_PATTERNS:
        match = re.search(pattern, message_lower)
        if match:
            otp = match.group(1)
            # Validate that it's actually an OTP (not just any number)
            if len(otp) >= 4 and len(otp) <= 6 and otp.isdigit():
                logging.info(f"Found OTP: {otp} using pattern: {pattern}")
                return otp
    
    logging.info(f"No OTP found in message: {message}")
    return None

def get_country_flag(country_code):
    """Get country flag emoji from country code"""
    try:
        country_code = country_code.upper()
        if country_code == 'XK':
            return '🇽🇰'
        # Handle custom country codes (like "india_ws", "india_tg")
        if "_" in country_code or len(country_code) > 2:
            # Try to extract a valid country code from the custom name
            if country_code.startswith("INDIA"):
                return '🇮🇳'
            elif country_code.startswith("SAUDI") or country_code.startswith("SA"):
                return '🇸🇦'
            elif country_code.startswith("USA") or country_code.startswith("US"):
                return '🇺🇸'
            elif country_code.startswith("UK") or country_code.startswith("GB"):
                return '🇬🇧'
            elif country_code.startswith("SRI") or country_code.startswith("LK"):
                return '🇱🇰'
            else:
                return '🌐'
        if len(country_code) != 2 or not country_code.isalpha():
            return '🌐'
        offset = ord('🇦') - ord('A')
        return chr(ord(country_code[0]) + offset) + chr(ord(country_code[1]) + offset)
    except:
        return '🌐'

def clean_number(number):
    """Convert numbers to proper string format"""
    if isinstance(number, float) and number.is_integer():
        return str(int(number))
    return str(number).replace(" ", "").replace("-", "").replace(".", "")

def extract_country_from_range(range_str):
    """Extract country name from range string using intelligent parsing"""
    if not range_str:
        return None
    
    range_str = str(range_str).lower()
    
    # Remove common non-country words and patterns
    patterns_to_remove = [
        r'\(.*?\)', r'\[.*?\]', r'\d+', r'[-–_/\\|]',
        r'\bwhatsapp\b', r'\bws\b', r'\bbmet\b', r'\bsms\b'
    ]
    
    for pattern in patterns_to_remove:
        range_str = re.sub(pattern, ' ', range_str)
    
    # Try to find country match with pycountry
    try:
        matches = pycountry.countries.search_fuzzy(range_str.strip())
        if matches:
            return matches[0].alpha_2.lower()
    except:
        pass
    
    return None

def detect_country_code(number, range_str=None):
    """Detect country code from number and range string using config prefixes"""
    # First try to detect from range string
    if range_str:
        country_code = extract_country_from_range(range_str)
        if country_code:
            return country_code
    
    # Then try to detect from number prefix
    number = clean_number(str(number))
    
    # Check if number starts with known prefix from config
    for prefix, code in COUNTRY_PREFIXES.items():
        if number.startswith(prefix):
            return code
    
    return None

# === KEYBOARDS ===
def join_channel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Check Join", callback_data="check_join")]
    ])

def number_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Get Number", callback_data="request_number")]
    ])

async def countries_keyboard(db):
    countries_coll = db[COUNTRIES_COLLECTION]
    countries = await countries_coll.distinct("country_code")
    
    buttons = []
    for country_code in countries:
        country_info = await countries_coll.find_one({"country_code": country_code})
        if country_info and "display_name" in country_info:
            display_name = country_info["display_name"]
            # Use detected country for flag if available
            detected_country = country_info.get("detected_country", country_code)
            flag = get_country_flag(detected_country)
        else:
            try:
                country = pycountry.countries.get(alpha_2=country_code.upper())
                display_name = country.name if country else country_code
            except:
                display_name = country_code
            flag = get_country_flag(country_code)
        
        buttons.append([InlineKeyboardButton(f"{flag} {display_name}", callback_data=f"country_{country_code}")])
    
    return InlineKeyboardMarkup(buttons)

def number_options_keyboard(number, country_code):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Change", callback_data=f"change_{country_code}")],
        [InlineKeyboardButton("📩 Show SMS", callback_data=f"sms_{number}")],
        [InlineKeyboardButton("📋 Menu", callback_data="menu")]
    ])

# === COMMAND HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    last_name = update.effective_user.last_name
    
    try:
        # Check if user is already verified
        is_verified = await is_user_verified(user_id, context)
        
        if is_verified:
            # User already verified, proceed directly
            await update.message.reply_text(
                "✅ Welcome back! You are already verified.\n\n"
                "📞 You can now get phone numbers.",
                reply_markup=number_keyboard()
            )
            return
        
        # Check channel membership for new user
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        
        if chat_member.status in ("member", "administrator", "creator"):
            # Store user data in database
            db = context.bot_data["db"]
            users_coll = db[USERS_COLLECTION]
            
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "verified_at": datetime.now(TIMEZONE),
                "last_activity": datetime.now(TIMEZONE),
                "status": "verified"
            }
            
            await users_coll.insert_one(user_data)
            
            # Create cache file for user
            await create_user_cache(user_id, user_data)
            
            logging.info(f"New user verified and stored via /start: {user_id} ({username})")
            
            await update.message.reply_text(
                "✅ You have successfully joined the channel!\n\n"
                "📱 Your account has been verified and cached.\n"
                "📞 You can now get phone numbers.",
                reply_markup=number_keyboard()
            )
        else:
            await update.message.reply_text("🚫 You haven't joined the channel yet!")
            await update.message.reply_text(
                "Please join the channel and check again.",
                reply_markup=join_channel_keyboard()
            )
    except Exception as e:
        logging.error(f"Error in start command: {e}")
        await update.message.reply_text("🚫 You haven't joined the channel yet!")
        await update.message.reply_text(
            "Please join the channel and check again.",
            reply_markup=join_channel_keyboard()
        )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    try:
        user_id = query.from_user.id
        username = query.from_user.username
        first_name = query.from_user.first_name
        last_name = query.from_user.last_name
        
        # Check if user is already verified in database
        db = context.bot_data["db"]
        users_coll = db[USERS_COLLECTION]
        
        existing_user = await users_coll.find_one({"user_id": user_id})
        
        if existing_user:
            # User already verified, proceed directly
            keyboard = number_keyboard()
            await query.edit_message_text(
                "✅ Welcome back! You are already verified.\n\n"
                "📞 You can now get phone numbers.",
                reply_markup=keyboard
            )
            return
        
        # Check channel membership for new user
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            # Store user data in database
            user_data = {
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "verified_at": datetime.now(TIMEZONE),
                "last_activity": datetime.now(TIMEZONE),
                "status": "verified"
            }
            
            await users_coll.insert_one(user_data)
            
            # Create cache file for user
            await create_user_cache(user_id, user_data)
            
            logging.info(f"New user verified and stored: {user_id} ({username})")
            
            keyboard = number_keyboard()
            await query.edit_message_text(
                "✅ You have successfully joined the channel!\n\n"
                "📱 Your account has been verified and cached.\n"
                "📞 You can now get phone numbers.",
                reply_markup=keyboard
            )
        else:
            await query.answer("❌ You need to join the channel first!", show_alert=True)
    except Exception as e:
        logging.error(f"Error checking channel membership: {e}")
        await query.answer("❌ Error checking channel membership. Please try again.", show_alert=True)

async def create_user_cache(user_id, user_data):
    """Create a cache file for verified user using config directory"""
    try:
        cache_dir = USER_CACHE_DIR
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        cache_file = os.path.join(cache_dir, f"user_{user_id}.json")
        
        cache_data = {
            "user_id": user_id,
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "verified_at": user_data.get("verified_at").isoformat() if user_data.get("verified_at") else None,
            "status": "verified"
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        logging.info(f"Cache file created for user {user_id}")
    except Exception as e:
        logging.error(f"Error creating cache file for user {user_id}: {e}")

async def is_user_verified(user_id, context):
    """Check if user is verified (database or cache)"""
    try:
        # First check database
        db = context.bot_data.get("db")
        if db is not None:
            users_coll = db[USERS_COLLECTION]
            user = await users_coll.find_one({"user_id": user_id})
            if user:
                return True
        
        # Then check cache file
        cache_file = os.path.join(USER_CACHE_DIR, f"user_{user_id}.json")
        if os.path.exists(cache_file):
            return True
        
        return False
    except Exception as e:
        logging.error(f"Error checking user verification: {e}")
        return False

async def request_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = context.bot_data["db"]
    keyboard = await countries_keyboard(db)
    await query.edit_message_text(
        "🌍 Select Country:",
        reply_markup=keyboard
    )

async def send_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country_code = query.data.split('_', 1)[1]
    
    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    country_info = await countries_coll.find_one({"country_code": country_code})
    country_name = country_info["display_name"] if country_info else country_code

    # Get a random number from the available numbers for this country (number stays in database for reuse)
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
        logging.info(f"Updated current number for user {user_id}: {number}")
        
        # Use detected country for flag if available
        detected_country = result.get("detected_country", country_code)
        flag = get_country_flag(detected_country)
        
        # Check for latest SMS and OTP
        sms_info = await get_latest_sms_for_number(number)
        
        message = (
            f"{flag} Country: {country_name}\n"
            f"📞 Number: [{formatted_number}](https://t.me/share/url?text={formatted_number})"
        )
        
        # Add OTP if found
        if sms_info and sms_info['otp']:
            if sms_info['sms']['sender']:
                message += f"\n🔐 {sms_info['sms']['sender']} : {sms_info['otp']}"
            else:
                message += f"\n🔐 OTP : {sms_info['otp']}"
        
        message += "\n\nSelect an option:"
        
        sent_message = await query.edit_message_text(
            message,
            reply_markup=number_options_keyboard(number, country_code),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Start OTP monitoring for this number
        await start_otp_monitoring(
            number, 
            sent_message.message_id, 
            query.message.chat_id, 
            country_code, 
            country_name, 
            context,
            query.from_user.id
        )
    else:
        keyboard = await countries_keyboard(db)
        await query.edit_message_text(
            f"⚠️ No numbers available for {country_name} right now. Please try another country.",
            reply_markup=keyboard
        )

async def change_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    country_code = query.data.split('_', 1)[1]
    
    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    country_info = await countries_coll.find_one({"country_code": country_code})
    country_name = country_info["display_name"] if country_info else country_code

    # Don't stop existing monitoring - let multiple morning calls run simultaneously
    logging.info("Keeping existing morning calls active while getting new number")
    
    # Get current number for this user to exclude it
    user_id = query.from_user.id
    current_number = current_user_numbers.get(user_id)
    logging.info(f"Current number for user {user_id}: {current_number}")
    
    # Show user that existing morning calls are still active
    if user_id in user_monitoring_sessions and user_monitoring_sessions[user_id]:
        active_sessions = len(user_monitoring_sessions[user_id])
        logging.info(f"User {user_id} has {active_sessions} active morning call sessions")
        await query.answer(f"📞 You have {active_sessions} active morning call(s) running", show_alert=False)
    
    # First, let's see all available numbers for this country
    all_numbers_pipeline = [
        {"$match": {"country_code": country_code}},
        {"$project": {"number": 1, "_id": 0}}
    ]
    all_numbers = await coll.aggregate(all_numbers_pipeline).to_list(length=None)
    all_number_list = [doc["number"] for doc in all_numbers]
    logging.info(f"All available numbers for {country_code}: {all_number_list}")
    
    # Get a different random number from the available numbers for this country
    if current_number and current_number in all_number_list and len(all_number_list) > 1:
        # Exclude current number and get a different one
        pipeline = [
            {"$match": {"country_code": country_code, "number": {"$ne": current_number}}},
            {"$sample": {"size": 1}}
        ]
        logging.info(f"Trying to get different number, excluding: {current_number}")
    else:
        # No current number or only one number available, get any random number
        pipeline = [
            {"$match": {"country_code": country_code}},
            {"$sample": {"size": 1}}
        ]
        if current_number:
            logging.info(f"Only one number available or current number not found, getting any number")
        else:
            logging.info("No current number to exclude, getting any random number")
    
    results = await coll.aggregate(pipeline).to_list(length=1)
    result = results[0] if results else None
    
    # Debug logging
    logging.info(f"Change number requested for country: {country_code}")
    logging.info(f"Found {len(results)} numbers for this country")
    if result:
        logging.info(f"Selected number: {result.get('number', 'N/A')}")
    else:
        logging.info("No numbers found for this country")
    
    if result and "number" in result:
        number = result["number"]
        formatted_number = format_number_display(number)
        
        # Check if this is actually a different number
        if current_number and number == current_number:
            logging.warning(f"Got same number again: {number}")
            if len(all_number_list) > 1:
                await query.answer(f"⚠️ Error: Got same number. Available: {len(all_number_list)} numbers. Try again.", show_alert=True)
                return
            else:
                await query.answer(f"⚠️ Only one number available for {country_name}. Try another country.", show_alert=True)
                return
        
        # Track current number for this user
        user_id = query.from_user.id
        current_user_numbers[user_id] = number
        logging.info(f"Updated current number for user {user_id}: {number}")
        
        # Use detected country for flag if available
        detected_country = result.get("detected_country", country_code)
        flag = get_country_flag(detected_country)
        
        # Check for latest SMS and OTP
        sms_info = await get_latest_sms_for_number(number)
        
        message = (
            f"{flag} Country: {country_name}\n"
            f"📞 Number: [{formatted_number}](https://t.me/share/url?text={formatted_number})"
        )
        
        # Add OTP if found
        if sms_info and sms_info['otp']:
            if sms_info['sms']['sender']:
                message += f"\n🔐 {sms_info['sms']['sender']} : {sms_info['otp']}"
            else:
                message += f"\n🔐 OTP : {sms_info['otp']}"
        
        message += "\n\nSelect an option:"
        
        sent_message = await query.edit_message_text(
            message,
            reply_markup=number_options_keyboard(number, country_code),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Start OTP monitoring for this number
        await start_otp_monitoring(
            number, 
            sent_message.message_id, 
            query.message.chat_id, 
            country_code, 
            country_name, 
            context,
            user_id
        )
    else:
        # No different numbers available for this country
        if current_number:
            # Check if we got the same number
            if len(all_number_list) == 1:
                logging.info(f"Only one number available for {country_code}: {all_number_list[0]}")
                await query.answer(f"⚠️ Only one number available for {country_name}. Try another country.", show_alert=True)
            else:
                logging.info(f"No different number available, keeping current: {current_number}")
                await query.answer(f"⚠️ No different number available for {country_name}. Available: {len(all_number_list)} numbers. Try another country.", show_alert=True)
        else:
            # No numbers available at all
            keyboard = await countries_keyboard(db)
            await query.edit_message_text(
                f"⚠️ No numbers available for {country_name}.\n"
                f"📱 All numbers for this country have been used (received OTPs).\n\n"
                f"🌍 Please select another country:",
                reply_markup=keyboard
            )

async def get_latest_sms_for_number(phone_number, date_str=None):
    """Get the latest SMS for a phone number and extract OTP"""
    logging.info(f"Getting latest SMS for {phone_number}")
    sms_data = await check_sms_for_number(phone_number, date_str)
    
    if sms_data and 'aaData' in sms_data and sms_data['aaData']:
        logging.info(f"SMS data found for {phone_number}, processing {len(sms_data['aaData'])} rows")
        # Filter out summary rows and get actual SMS messages
        sms_messages = []
        for row in sms_data['aaData']:
            if isinstance(row, list) and len(row) >= 6:
                # Check if this is a real SMS message (not a summary row)
                first_item = str(row[0])
                if not first_item.startswith('0.') and not ',' in first_item and len(first_item) > 10:
                    sms_messages.append({
                        'datetime': row[0],
                        'range': row[1],
                        'number': row[2],
                        'sender': row[3] if len(row) > 3 else 'Unknown',
                        'message': row[5] if len(row) > 5 else 'No message content'
                    })
        
        logging.info(f"Found {len(sms_messages)} valid SMS messages for {phone_number}")
        
        if sms_messages:
            # Get the latest SMS (first in the list since it's sorted by desc)
            latest_sms = sms_messages[0]
            logging.info(f"Latest SMS for {phone_number}: {latest_sms}")
            
            # Enhanced OTP extraction with more detailed logging
            otp = extract_otp_from_message(latest_sms['message'])
            if otp:
                logging.info(f"🎯 OTP DETECTED for {phone_number}: {otp}")
            else:
                logging.info(f"❌ No OTP found in message: {latest_sms['message'][:100]}...")
            
            result = {
                'sms': latest_sms,
                'otp': otp,
                'total_messages': len(sms_messages)
            }
            logging.info(f"Returning SMS info for {phone_number}: {result}")
            return result
    else:
        logging.info(f"No SMS data found for {phone_number}")
    
    return None

async def start_otp_monitoring(phone_number, message_id, chat_id, country_code, country_name, context, user_id=None):
    """Start monitoring a phone number for new OTPs (morning call system)"""
    if user_id is None:
        user_id = context.effective_user.id if context.effective_user else None
    
    if user_id is None:
        logging.error(f"Cannot start monitoring for {phone_number}: user_id is None")
        return
    
    # Create unique session ID for this monitoring session
    session_id = f"{phone_number}_{int(time.time())}"
    
    # Initialize user monitoring sessions if not exists
    if user_id not in user_monitoring_sessions:
        user_monitoring_sessions[user_id] = {}
    
    # Add this session to user's monitoring sessions
    user_monitoring_sessions[user_id][session_id] = {
        'phone_number': phone_number,
        'message_id': message_id,
        'chat_id': chat_id,
        'country_code': country_code,
        'country_name': country_name,
        'start_time': datetime.now(TIMEZONE),
        'stop': False,
        'last_otp': None,
        'last_check': None
    }
    
    # Start new monitor (multiple monitors can run simultaneously)
    active_number_monitors[session_id] = {
        'stop': False,
        'last_otp': None,
        'last_check': None,
        'start_time': datetime.now(TIMEZONE),
        'user_id': user_id,
        'phone_number': phone_number
    }
    
    logging.info(f"Started morning call monitoring session {session_id} for user {user_id} on number {phone_number}")
    logging.info(f"Active monitors count: {len(active_number_monitors)}")
    logging.info(f"User monitoring sessions for user {user_id}: {len(user_monitoring_sessions.get(user_id, {}))}")
    
    async def monitor_otp():
        """Morning call monitoring - runs for 2 minutes then auto-cancels"""
        logging.info(f"Starting morning call monitoring for {phone_number} - checking every 5 seconds for 2 minutes")
        
        # Morning call timeout: 2 minutes (120 seconds)
        MORNING_CALL_TIMEOUT = 120
        check_count = 0
        
        # Immediate check for existing OTP
        logging.info(f"🔍 Immediate OTP check for {phone_number}")
        immediate_sms_info = await get_latest_sms_for_number(phone_number)
        if immediate_sms_info and immediate_sms_info['otp']:
            logging.info(f"🎯 IMMEDIATE OTP FOUND for {phone_number}: {immediate_sms_info['otp']}")
            # Process this OTP immediately
            current_otp = immediate_sms_info['otp']
            active_number_monitors[session_id]['last_otp'] = current_otp
            
            # Update the message with new OTP
            formatted_number = format_number_display(phone_number)
            flag = get_country_flag(country_code)
            
            message = (
                f"{flag} Country: {country_name}\n"
                f"📞 Number: [{formatted_number}](https://t.me/share/url?text={formatted_number})\n"
                f"🔐 {immediate_sms_info['sms']['sender']} : {current_otp}\n\n"
                f"Select an option:"
            )
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=message,
                    reply_markup=number_options_keyboard(phone_number, country_code),
                    parse_mode=ParseMode.MARKDOWN
                )
                logging.info(f"✅ Immediate OTP update successful for {phone_number}: {current_otp}")
                
                # Delete the number permanently
                db = context.bot_data["db"]
                coll = db[COLLECTION_NAME]
                countries_coll = db[COUNTRIES_COLLECTION]
                
                delete_result = await coll.delete_one({"number": phone_number})
                if delete_result.deleted_count > 0:
                    logging.info(f"🗑️ Number {phone_number} permanently deleted after immediate OTP")
                    
                    # Update country count
                    await countries_coll.update_one(
                        {"country_code": country_code},
                        {"$inc": {"number_count": -1}}
                    )
                    
                    # Stop this monitoring session
                    await stop_otp_monitoring_session(session_id)
                    
                    # Send clean OTP notification to user's private chat
                    monitoring_user_id = active_number_monitors[session_id].get('user_id')
                    if monitoring_user_id:
                        await context.bot.send_message(
                            chat_id=monitoring_user_id,  # Send to user's private chat
                            text=f"📞 Number: {formatted_number}\n🔐 {immediate_sms_info['sms']['sender']} : {current_otp}"
                        )
                    return  # Exit monitoring since OTP was found
                    
            except Exception as e:
                logging.error(f"Failed to update message for {phone_number} (immediate): {e}")
        else:
            logging.info(f"❌ No immediate OTP found for {phone_number}, starting monitoring loop")
        
        while not active_number_monitors[session_id]['stop']:
            try:
                check_count += 1
                logging.info(f"🔍 Morning call check #{check_count} for {phone_number}")
                
                # Get latest SMS and OTP
                sms_info = await get_latest_sms_for_number(phone_number)
                
                if sms_info and sms_info['otp']:
                    current_otp = sms_info['otp']
                    last_otp = active_number_monitors[session_id]['last_otp']
                    
                    logging.info(f"🔍 OTP Check for {phone_number}: Last OTP = {last_otp}, Current OTP = {current_otp}")
                    
                    # Check if this is a new OTP (including first OTP detection)
                    if last_otp != current_otp or last_otp is None:
                        logging.info(f"🎯 NEW OTP DETECTED for {phone_number}: {current_otp}")
                        active_number_monitors[session_id]['last_otp'] = current_otp
                        
                        # Update the message with new OTP
                        formatted_number = format_number_display(phone_number)
                        flag = get_country_flag(country_code)
                        
                        message = (
                            f"{flag} Country: {country_name}\n"
                            f"📞 Number: [{formatted_number}](https://t.me/share/url?text={formatted_number})\n"
                            f"🔐 {sms_info['sms']['sender']} : {current_otp}\n\n"
                            f"Select an option:"
                        )
                        
                        try:
                            await context.bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=message_id,
                                text=message,
                                reply_markup=number_options_keyboard(phone_number, country_code),
                                parse_mode=ParseMode.MARKDOWN
                            )
                            logging.info(f"✅ OTP detected and message updated for {phone_number}: {current_otp}")
                            
                            # Delete the number permanently (never give to others)
                            db = context.bot_data["db"]
                            coll = db[COLLECTION_NAME]
                            countries_coll = db[COUNTRIES_COLLECTION]
                            
                            delete_result = await coll.delete_one({"number": phone_number})
                            if delete_result.deleted_count > 0:
                                logging.info(f"🗑️ Number {phone_number} permanently deleted after OTP")
                                
                                # Update country count
                                await countries_coll.update_one(
                                    {"country_code": country_code},
                                    {"$inc": {"number_count": -1}}
                                )
                                
                                # Stop this monitoring session
                                await stop_otp_monitoring_session(session_id)
                                
                                # Send clean OTP notification to user's private chat
                                monitoring_user_id = active_number_monitors[session_id].get('user_id')
                                if monitoring_user_id:
                                    await context.bot.send_message(
                                        chat_id=monitoring_user_id,  # Send to user's private chat
                                        text=f"📞 Number: {formatted_number}\n🔐 {sms_info['sms']['sender']} : {current_otp}"
                                    )
                                
                        except Exception as e:
                            logging.error(f"Failed to update message for {phone_number}: {e}")
                
                # Check for morning call timeout (2 minutes)
                current_time = datetime.now(TIMEZONE)
                start_time = active_number_monitors[session_id]['start_time']
                time_elapsed = (current_time - start_time).total_seconds()
                
                if time_elapsed > MORNING_CALL_TIMEOUT:
                    logging.info(f"⏰ Morning call timeout reached for {phone_number} (2 minutes), auto-canceling")
                    
                    # Stop this monitoring session (number stays in database for reuse)
                    await stop_otp_monitoring_session(session_id)
                    
                    # Notify user about morning call ending (send to user's private chat only)
                    try:
                        # Get the user ID from the monitoring session to ensure private message
                        monitoring_user_id = active_number_monitors[session_id].get('user_id')
                        if monitoring_user_id:
                            await context.bot.send_message(
                                chat_id=monitoring_user_id,  # Send to user's private chat, not group/channel
                                text=f"⏰ Morning call ended for {format_number_display(phone_number)} (2 minutes timeout)\n\n"
                                     f"🔄 This number can be given to other users again.\n"
                                     f"📞 You can get a new number anytime!"
                            )
                    except Exception as e:
                        logging.error(f"Failed to send morning call timeout message for {phone_number}: {e}")
                    
                    break
                
                # Wait 5 seconds before next check
                await asyncio.sleep(OTP_CHECK_INTERVAL)
                
            except Exception as e:
                logging.error(f"Error in morning call monitoring for {phone_number}: {e}")
                await asyncio.sleep(OTP_CHECK_INTERVAL)
    
    # Start the monitoring task
    asyncio.create_task(monitor_otp())

async def stop_otp_monitoring_session(session_id):
    """Stop a specific monitoring session"""
    if session_id in active_number_monitors:
        logging.info(f"Stopping monitoring session {session_id}")
        active_number_monitors[session_id]['stop'] = True
        del active_number_monitors[session_id]
        
        # Also remove from user monitoring sessions
        user_id = active_number_monitors[session_id].get('user_id') if session_id in active_number_monitors else None
        if user_id and user_id in user_monitoring_sessions:
            if session_id in user_monitoring_sessions[user_id]:
                del user_monitoring_sessions[user_id][session_id]
                logging.info(f"Removed session {session_id} from user {user_id} monitoring sessions")
        
        logging.info(f"Monitoring session {session_id} stopped")
    else:
        logging.info(f"No active monitoring session found for {session_id}")

async def stop_otp_monitoring(phone_number):
    """Stop monitoring a phone number for OTPs (legacy function)"""
    # Find all sessions for this phone number and stop them
    sessions_to_stop = []
    for session_id, monitor_data in active_number_monitors.items():
        if monitor_data.get('phone_number') == phone_number:
            sessions_to_stop.append(session_id)
    
    for session_id in sessions_to_stop:
        await stop_otp_monitoring_session(session_id)
    
    if sessions_to_stop:
        logging.info(f"Stopped {len(sessions_to_stop)} monitoring sessions for {phone_number}")
    else:
        logging.info(f"No active monitoring found for {phone_number}")

async def check_sms_for_number(phone_number, date_str=None):
    """Check SMS for a specific phone number using the API"""
    if not date_str:
        # For live monitoring, check last 24 hours to catch recent messages
        now = datetime.now(TIMEZONE)
        yesterday = now - timedelta(hours=24)
        date_str = yesterday.strftime("%Y-%m-%d")
    
    logging.info(f"Checking SMS for number: {phone_number} on date: {date_str}")
    
    # Build the API URL with parameters - optimized for live monitoring
    params = {
        'fdate1': f"{date_str} 00:00:00",
        'fdate2': f"{datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}",  # Current time
        'frange': '',
        'fclient': '',
        'fnum': phone_number,  # Filter by phone number
        'fcli': '',
        'fgdate': '',
        'fgmonth': '',
        'fgrange': '',
        'fgclient': '',
        'fgnumber': '',
        'fgcli': '',
        'fg': '0',
        'sEcho': '1',
        'iColumns': '9',
        'sColumns': ',,,,,,,,',
        'iDisplayStart': '0',
        'iDisplayLength': '50',  # Get more messages for better coverage
        'mDataProp_0': '0',
        'sSearch_0': '',
        'bRegex_0': 'false',
        'bSearchable_0': 'true',
        'bSortable_0': 'true',
        'mDataProp_1': '1',
        'sSearch_1': '',
        'bRegex_1': 'false',
        'bSearchable_1': 'true',
        'bSortable_1': 'true',
        'mDataProp_2': '2',
        'sSearch_2': '',
        'bRegex_2': 'false',
        'bSearchable_2': 'true',
        'bSortable_2': 'true',
        'mDataProp_3': '3',
        'sSearch_3': '',
        'bRegex_3': 'false',
        'bSearchable_3': 'true',
        'bSortable_3': 'true',
        'mDataProp_4': '4',
        'sSearch_4': '',
        'bRegex_4': 'false',
        'bSearchable_4': 'true',
        'bSortable_4': 'true',
        'mDataProp_5': '5',
        'sSearch_5': '',
        'bRegex_5': 'false',
        'bSearchable_5': 'true',
        'bSortable_5': 'true',
        'mDataProp_6': '6',
        'sSearch_6': '',
        'bRegex_6': 'false',
        'bSearchable_6': 'true',
        'bSortable_6': 'true',
        'mDataProp_7': '7',
        'sSearch_7': '',
        'bRegex_7': 'false',
        'bSearchable_7': 'true',
        'bSortable_7': 'true',
        'mDataProp_8': '8',
        'sSearch_8': '',
        'bRegex_8': 'false',
        'bSearchable_8': 'true',
        'bSortable_8': 'false',
        'sSearch': '',
        'bRegex': 'false',
        'iSortCol_0': '0',
        'sSortDir_0': 'desc',
        'iSortingCols': '1',
        '_': str(int(datetime.now().timestamp() * 1000))
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{SMS_API_BASE_URL}/ints/agent/SMSCDRReports',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-US,en;q=0.9,ks-IN;q=0.8,ks;q=0.7',
        'Cookie': SMS_API_COOKIE
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{SMS_API_BASE_URL}{SMS_API_ENDPOINT}"
            logging.info(f"Making API request to: {url}")
            logging.info(f"With params: {params}")
            
            async with session.get(url, params=params, headers=headers) as response:
                logging.info(f"API response status: {response.status}")
                
                if response.status == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    logging.info(f"Content-Type: {content_type}")
                    
                    # Get response text first to check for login redirect
                    response_text = await response.text()
                    
                    # Check if we got redirected to login page
                    if 'login' in response_text.lower() or 'msi sms | login' in response_text.lower():
                        logging.error(f"❌ SMS API session expired - redirected to login page")
                        logging.error(f"🔑 Need to update SMS_API_COOKIE with fresh session")
                        return None
                    
                    # Always try to parse as JSON regardless of content type
                    try:
                        data = await response.json()
                        logging.info(f"API response data: {data}")
                        return data
                    except Exception as json_error:
                        logging.error(f"JSON parsing failed: {json_error}")
                        logging.info(f"Response text: {response_text[:500]}...")  # Log first 500 chars
                        
                        # Try to extract JSON from HTML response
                        if 'aaData' in response_text:
                            try:
                                # Find JSON part in the response
                                start = response_text.find('{')
                                end = response_text.rfind('}') + 1
                                if start != -1 and end != 0:
                                    json_part = response_text[start:end]
                                    data = json.loads(json_part)
                                    logging.info(f"Extracted JSON data: {data}")
                                    return data
                            except Exception as extract_error:
                                logging.error(f"Failed to extract JSON: {extract_error}")
                        
                        return None
                else:
                    response_text = await response.text()
                    logging.error(f"SMS API error: {response.status}, Response: {response_text}")
                    return None
    except Exception as e:
        logging.error(f"Error checking SMS: {e}")
        return None

async def show_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    number = query.data.split('_', 1)[1]
    
    # Show loading message
    await query.answer("🔍 Checking for SMS messages...", show_alert=True)
    
    try:
        # Get latest SMS and OTP
        sms_info = await get_latest_sms_for_number(number)
        
        if sms_info and sms_info['otp']:
            # Display compact OTP format
            formatted_number = format_number_display(number)
            message = f"📞 Number: {formatted_number}\n"
            message += f"🔐 {sms_info['sms']['sender']} : {sms_info['otp']}"
            
            # Send as a new message
            await context.bot.send_message(
                chat_id=query.from_user.id,
                text=message,
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await query.answer("📭 No OTP found for this number today.", show_alert=True)
            
    except Exception as e:
        logging.error(f"Error in show_sms: {e}")
        await query.answer("❌ SMS API not available. Please try again later.", show_alert=True)




async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # Stop any active OTP monitoring
    for phone_number in list(active_number_monitors.keys()):
        await stop_otp_monitoring(phone_number)
    
    db = context.bot_data["db"]
    keyboard = await countries_keyboard(db)
    await query.edit_message_text(
        "🌍 Select Country:",
        reply_markup=keyboard
    )

async def delete_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logging.info(f"Delete country command called by user {user_id}")
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to delete numbers.")
        return

    args = context.args
    logging.info(f"Delete country args: {args}")
    
    if not args:
        # Show available countries to delete
        db = context.bot_data["db"]
        countries_coll = db[COUNTRIES_COLLECTION]
        countries = await countries_coll.find({}).to_list(length=50)
        
        if not countries:
            await update.message.reply_text("📭 No countries found in database.")
            return
        
        message_lines = ["🗑️ Available countries to delete:"]
        for country in countries:
            flag = get_country_flag(country.get("detected_country", country["country_code"]))
            display_name = country.get("display_name", country["country_code"])
            count = country.get("number_count", 0)
            message_lines.append(f"{flag} {display_name} ({country['country_code']}) - {count} numbers")
        
        message_lines.append("\nUsage: /delete <country_code>")
        message_lines.append("Example: /delete india_ws")
        
        await update.message.reply_text("\n".join(message_lines))
        return

    country_code = args[0].lower()
    
    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    # Check if country exists
    country_info = await countries_coll.find_one({"country_code": country_code})
    if not country_info:
        await update.message.reply_text(f"❌ Country code '{country_code}' not found in database.")
        return

    # Get country display name
    display_name = country_info.get("display_name", country_code)
    
    # Delete numbers
    result = await coll.delete_many({"country_code": country_code})
    
    # Delete country from countries collection
    await countries_coll.delete_one({"country_code": country_code})
    
    flag = get_country_flag(country_info.get("detected_country", country_code))
    
    await update.message.reply_text(
        f"✅ Deleted {result.deleted_count} numbers for {flag} {display_name} (`{country_code}`)."
    )

async def check_api_connection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check SMS API connection status"""
    user_id = update.effective_user.id
    logging.info(f"Check API connection command called by user {user_id}")
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to check API connection.")
        return

    await update.message.reply_text("🔍 Checking SMS API connection...")

    try:
        # Test the SMS API connection
        url = f"{SMS_API_BASE_URL}{SMS_API_ENDPOINT}"
        
        # Use minimal params for connection test
        from datetime import datetime, timedelta
        import pytz
        timezone = pytz.timezone(TIMEZONE_NAME)
        now = datetime.now(timezone)
        yesterday = now - timedelta(hours=24)
        date_str = yesterday.strftime("%Y-%m-%d")
        
        params = {
            'fdate1': f"{date_str} 00:00:00",
            'fdate2': f"{now.strftime('%Y-%m-%d %H:%M:%S')}",
            'fnum': '000000000',  # Dummy number for connection test
            'iDisplayLength': '1',  # Minimal data
            'sSortDir_0': 'desc',
            '_': str(int(datetime.now().timestamp() * 1000))
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'{SMS_API_BASE_URL}/ints/agent/SMSCDRReports',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9,ks-IN;q=0.8,ks;q=0.7',
            'Cookie': SMS_API_COOKIE
        }
        
        import time
        start_time = time.time()
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url, params=params, headers=headers) as response:
                response_time = round((time.time() - start_time) * 1000, 2)
                
                status_emoji = "✅" if response.status == 200 else "❌"
                status_text = "Connected" if response.status == 200 else f"Error {response.status}"
                
                # Check response content
                response_text = await response.text()
                content_type = response.headers.get('content-type', 'unknown')
                
                # Detect common issues
                issues = []
                warnings = []
                
                if 'login' in response_text.lower():
                    issues.append("❌ Session expired - redirected to login")
                elif 'direct script access not allowed' in response_text.lower():
                    issues.append("❌ Direct script access blocked")
                elif response.status != 200:
                    issues.append(f"❌ HTTP Error: {response.status}")
                elif not response_text.strip().startswith('{'):
                    issues.append("❌ Non-JSON response received")
                
                # Check for warnings (non-critical issues)
                if 'application/json' not in content_type and response_text.strip().startswith('{'):
                    warnings.append("⚠️ JSON response with HTML content-type (common, not critical)")
                
                # Try to parse JSON
                json_valid = False
                try:
                    import json
                    data = json.loads(response_text)
                    json_valid = True
                    record_count = data.get('iTotalRecords', 'unknown')
                except:
                    record_count = 'invalid'
                
                # Build status message
                message_lines = [
                    f"🌐 **SMS API Connection Status**",
                    f"",
                    f"{status_emoji} **Status**: {status_text}",
                    f"⏱️ **Response Time**: {response_time}ms",
                    f"📡 **Endpoint**: {SMS_API_BASE_URL}",
                    f"🔧 **Content-Type**: {content_type}",
                    f"📊 **JSON Valid**: {'✅ Yes' if json_valid else '❌ No'}",
                    f"📈 **Test Query Records**: {record_count}",
                    f"🍪 **Cookie**: {SMS_API_COOKIE[:20]}...{SMS_API_COOKIE[-10:]}",
                ]
                
                # Add issues section
                if issues:
                    message_lines.extend([
                        f"",
                        f"🚨 **Critical Issues Detected**:"
                    ])
                    message_lines.extend(issues)
                
                # Add warnings section
                if warnings:
                    message_lines.extend([
                        f"",
                        f"⚠️ **Warnings** (non-critical):"
                    ])
                    message_lines.extend(warnings)
                
                # Add final status
                if not issues:
                    message_lines.extend([
                        f"",
                        f"✅ **API Connection Healthy!**",
                        f"🎯 **Ready for OTP detection**"
                    ])
                else:
                    message_lines.extend([
                        f"",
                        f"❌ **API has critical issues**",
                        f"🔧 **Action required to fix OTP detection**"
                    ])
                
                message_lines.extend([
                    f"",
                    f"_Test performed at {now.strftime('%Y-%m-%d %H:%M:%S')}_"
                ])
                
                await update.message.reply_text(
                    "\n".join(message_lines),
                    parse_mode=ParseMode.MARKDOWN
                )
                
    except asyncio.TimeoutError:
        await update.message.reply_text(
            "❌ **SMS API Connection Failed**\n\n"
            "⏱️ **Error**: Connection timeout (>10 seconds)\n"
            "🔧 **Suggestion**: Check SMS API server status\n\n"
            f"📡 **Endpoint**: {SMS_API_BASE_URL}",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ **SMS API Connection Failed**\n\n"
            f"🚫 **Error**: {str(e)}\n"
            f"🔧 **Suggestion**: Check network connection and API settings\n\n"
            f"📡 **Endpoint**: {SMS_API_BASE_URL}",
            parse_mode=ParseMode.MARKDOWN
        )

async def delete_all_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete all numbers from database"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to delete numbers.")
        return

    # Ask for confirmation
    if not context.args or context.args[0] != "confirm":
        await update.message.reply_text(
            "⚠️ This will delete ALL numbers from the database!\n"
            "To confirm, use: /deleteall confirm"
        )
        return

    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    # Get count before deletion
    total_numbers = await coll.count_documents({})
    
    # Delete all numbers
    result = await coll.delete_many({})
    
    # Delete all countries
    await countries_coll.delete_many({})
    
    await update.message.reply_text(
        f"🗑️ Deleted all {result.deleted_count} numbers from database."
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show database statistics"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to view stats.")
        return

    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    # Get total numbers
    total_numbers = await coll.count_documents({})
    
    # Get countries with counts
    countries = await countries_coll.find({}).to_list(length=50)
    
    message_lines = [
        "📊 Database Statistics:",
        f"📱 Total Numbers: {total_numbers}",
        f"🌍 Total Countries: {len(countries)}",
        "",
        "📋 Countries:"
    ]
    
    for country in countries:
        flag = get_country_flag(country.get("detected_country", country["country_code"]))
        display_name = country.get("display_name", country["country_code"])
        count = country.get("number_count", 0)
        message_lines.append(f"{flag} {display_name}: {count} numbers")
    
    await update.message.reply_text("\n".join(message_lines))

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add command to enter numbers manually and upload CSV"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to use this command.")
        return

    # Initialize user state
    user_states[user_id] = "waiting_for_manual_numbers"
    manual_numbers[user_id] = []
    
    await update.message.reply_text(
        "📱 **Add Numbers Command**\n\n"
        "Please enter the phone numbers one by one (one number per line):\n"
        "Example:\n"
        "94741854027\n"
        "94775995195\n"
        "94743123866\n\n"
        "💡 **Options:**\n"
        "• Send 'done' when finished entering numbers manually\n"
        "• Upload a CSV file (will skip to country name step)\n"
        "• Send 'cancel' to cancel the operation",
        parse_mode=ParseMode.MARKDOWN
    )

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test command for debugging"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    args = context.args
    if args and args[0].isdigit():
        # Test specific phone number
        phone_number = args[0]
        await update.message.reply_text(f"🔍 Testing OTP for number: {phone_number}")
        
        # Check SMS for this number
        sms_info = await get_latest_sms_for_number(phone_number)
        
        if sms_info:
            await update.message.reply_text(
                f"📱 SMS Info for {phone_number}:\n"
                f"Sender: {sms_info['sms']['sender']}\n"
                f"Message: {sms_info['sms']['message']}\n"
                f"OTP: {sms_info['otp']}\n"
                f"Total Messages: {sms_info['total_messages']}"
            )
        else:
            await update.message.reply_text(f"❌ No SMS found for {phone_number}")
    else:
        # Test OTP extraction
        test_message = "# Snapchat 157737 is your one time passcode for phone enrollment"
        otp = extract_otp_from_message(test_message)
        
        await update.message.reply_text(
            f"🧪 Test Results:\n"
            f"Test Message: {test_message}\n"
            f"Extracted OTP: {otp}\n"
            f"Active Monitors: {list(active_number_monitors.keys())}"
        )

async def cleanup_used_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clean up numbers that have received OTPs"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    await update.message.reply_text("🧹 Starting cleanup of numbers with OTPs...")
    
    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]
    
    # Get all numbers from database
    all_numbers = await coll.find({}).to_list(length=None)
    deleted_count = 0
    kept_count = 0
    
    for num_data in all_numbers:
        phone_number = num_data["number"]
        country_code = num_data["country_code"]
        
        # Check if this number has received any OTPs
        sms_info = await get_latest_sms_for_number(phone_number)
        
        if sms_info and sms_info['otp']:
            # This number has received an OTP, delete it
            await coll.delete_one({"number": phone_number})
            
            # Update country count
            await countries_coll.update_one(
                {"country_code": country_code},
                {"$inc": {"number_count": -1}}
            )
            
            deleted_count += 1
            logging.info(f"Cleaned up number {phone_number} with OTP: {sms_info['otp']}")
        else:
            kept_count += 1
    
    await update.message.reply_text(
        f"✅ Cleanup completed!\n\n"
        f"🗑️ Deleted {deleted_count} numbers with OTPs\n"
        f"✅ Kept {kept_count} numbers without OTPs\n"
        f"📊 Total processed: {deleted_count + kept_count}"
    )

async def force_otp_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force OTP check for a specific number"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /forceotp <phone_number>")
        return
    
    phone_number = args[0]
    await update.message.reply_text(f"🔍 Force checking OTP for {phone_number}")
    
    # Get latest SMS and OTP
    sms_info = await get_latest_sms_for_number(phone_number)
    
    if sms_info and sms_info['otp']:
        await update.message.reply_text(
            f"✅ OTP Found!\n"
            f"Number: {phone_number}\n"
            f"OTP: {sms_info['otp']}\n"
            f"Sender: {sms_info['sms']['sender']}\n"
            f"Time: {sms_info['sms']['datetime']}"
        )
    else:
        await update.message.reply_text(f"❌ No OTP found for {phone_number}")

async def check_monitoring_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check current OTP monitoring status"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    if active_number_monitors:
        status_text = "📊 Active OTP Monitoring:\n\n"
        for phone_number, monitor_data in active_number_monitors.items():
            status_text += f"📞 {phone_number}\n"
            status_text += f"   Status: {'Running' if not monitor_data['stop'] else 'Stopping'}\n"
            status_text += f"   Last OTP: {monitor_data['last_otp'] or 'None'}\n"
            status_text += f"   Start Time: {monitor_data['start_time']}\n\n"
    else:
        status_text = "📊 No active OTP monitoring"
    
    await update.message.reply_text(status_text)

async def check_country_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check how many numbers are available for each country"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]
    
    # Get all countries
    countries = await countries_coll.find({}).to_list(length=None)
    
    status_text = "📊 Numbers Available by Country:\n\n"
    
    for country in countries:
        country_code = country["country_code"]
        country_name = country["display_name"]
        
        # Count numbers for this country
        count = await coll.count_documents({"country_code": country_code})
        
        status_text += f"🌍 {country_name} ({country_code})\n"
        status_text += f"   📱 Available: {count} numbers\n\n"
    
    await update.message.reply_text(status_text)

async def show_my_morning_calls(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active morning calls for the user"""
    user_id = update.effective_user.id
    
    if user_id not in user_monitoring_sessions or not user_monitoring_sessions[user_id]:
        await update.message.reply_text("📞 You have no active morning calls.")
        return
    
    status_text = "📞 Your Active Morning Calls:\n\n"
    
    for session_id, session_data in user_monitoring_sessions[user_id].items():
        phone_number = session_data['phone_number']
        country_name = session_data['country_name']
        start_time = session_data['start_time']
        
        # Calculate remaining time (2 minutes = 120 seconds)
        current_time = datetime.now(TIMEZONE)
        elapsed = (current_time - start_time).total_seconds()
        remaining = max(0, 120 - elapsed)
        
        status_text += f"📱 {format_number_display(phone_number)}\n"
        status_text += f"   🌍 {country_name}\n"
        status_text += f"   ⏰ Remaining: {int(remaining)} seconds\n"
        status_text += f"   🕐 Started: {start_time.strftime('%H:%M:%S')}\n\n"
    
    await update.message.reply_text(status_text)

async def update_sms_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update SMS API session cookie"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "🔑 SMS API Session Update\n\n"
            "Usage: /updatesms <new_session_cookie>\n\n"
            "Example: /updatesms PHPSESSID=abc123def456\n\n"
            "⚠️ Current session appears to be expired.\n"
            "🔍 Get fresh session from your SMS panel."
        )
        return
    
    new_cookie = args[0]
    if not new_cookie.startswith("PHPSESSID="):
        await update.message.reply_text("❌ Invalid session cookie format. Must start with 'PHPSESSID='")
        return
    
    # Update the global variable
    global SMS_API_COOKIE
    SMS_API_COOKIE = new_cookie
    
    await update.message.reply_text(
        f"✅ SMS API session updated!\n\n"
        f"🔑 New cookie: {new_cookie}\n\n"
        f"🔄 Restart the bot to apply changes."
    )

async def reset_current_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset current number tracking for debugging"""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    
    if user_id in current_user_numbers:
        old_number = current_user_numbers[user_id]
        del current_user_numbers[user_id]
        await update.message.reply_text(f"✅ Reset current number tracking for user {user_id}\nOld number: {old_number}")
    else:
        await update.message.reply_text(f"ℹ️ No current number tracking found for user {user_id}")

async def list_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all numbers in database"""
    user_id = update.effective_user.id
    logging.info(f"List numbers command called by user {user_id}")
    
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to view numbers.")
        return

    args = context.args
    country_filter = None
    if args:
        country_filter = args[0].lower()

    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]

    # Build query
    query = {}
    if country_filter:
        query["country_code"] = country_filter

    # Get numbers
    numbers = await coll.find(query).limit(20).to_list(length=20)
    
    if not numbers:
        if country_filter:
            await update.message.reply_text(f"📭 No numbers found for country '{country_filter}'.")
        else:
            await update.message.reply_text("📭 No numbers found in database.")
        return

    message_lines = [f"📱 Numbers in database{f' for {country_filter}' if country_filter else ''}:"]
    
    for num_data in numbers:
        flag = get_country_flag(num_data.get("detected_country", num_data["country_code"]))
        formatted_num = format_number_display(num_data["number"])
        country_code = num_data["country_code"]
        message_lines.append(f"{flag} {formatted_num} ({country_code})")
    
    if len(numbers) == 20:
        message_lines.append("\n... (showing first 20 numbers)")
    
    message_lines.append(f"\nTotal: {len(numbers)} numbers shown")
    
    await update.message.reply_text("\n".join(message_lines))

def format_number_display(number):
    """Format number for display with proper spacing and plus sign"""
    number = clean_number(number)
    
    # Ensure number has + prefix
    if not number.startswith("+"):
        # Add + prefix to all numbers
        return f"+{number}"
    
    return number

# === CSV PROCESSING ===
async def process_csv_file(file_bytes):
    """Process the uploaded CSV file and return extracted numbers"""
    try:
        # Convert bytes to string and create CSV reader
        file_text = file_bytes.getvalue().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(file_text))
        
        # Verify required columns exist
        if 'Number' not in csv_reader.fieldnames:
            return None, "CSV file must contain a 'Number' column"
        
        # Process all rows
        numbers = []
        for row in csv_reader:
            try:
                number = row.get('Number', '')
                range_val = row.get('Range', '')
                
                if not number:
                    continue
                
                cleaned_number = clean_number(number)
                country_code = detect_country_code(cleaned_number, range_val)
                
                if country_code:
                    numbers.append({
                        'number': cleaned_number,
                        'original_number': number,
                        'country_code': country_code,
                        'range': range_val
                    })
            except Exception as e:
                logging.error(f"Error processing row: {e}")
                continue
        
        return numbers, f"Processed {len(numbers)} numbers"
    except Exception as e:
        return None, f"Error processing CSV file: {str(e)}"

async def upload_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global uploaded_csv
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to upload files.")
        return

    if not update.message.document:
        await update.message.reply_text("❌ Please upload a CSV file.")
        return

    file = update.message.document
    if not file.file_name.lower().endswith('.csv'):
        await update.message.reply_text("❌ Only CSV files are supported.")
        return

    await update.message.reply_text("📥 CSV file received!")

    file_obj = await file.get_file()
    file_bytes = BytesIO()
    await file_obj.download_to_memory(out=file_bytes)
    file_bytes.seek(0)
    uploaded_csv = file_bytes

    # Check if user is in add command flow (either waiting for manual numbers or CSV)
    if user_id in user_states and user_states[user_id] in ["waiting_for_csv", "waiting_for_manual_numbers"]:
        # User is in /add command flow, ask for name immediately (skip "done" step)
        user_states[user_id] = "waiting_for_name"
        await update.message.reply_text(
            "🌍 Please enter the name for all the numbers (manual + CSV):\n"
            "Examples: Sri Lanka Ws, Sri Lanka Tg, etc.\n"
            "This name will be used for all numbers (manual and CSV)."
        )
    else:
        # Regular CSV upload flow
        user_states[user_id] = "waiting_for_country"
        await update.message.reply_text(
            "🌍 Please enter the country name for the numbers in this CSV file:\n"
            "Examples: India Ws, India Tg, Saudi Arabia, USA, etc.\n"
            "You can use custom names like 'India Ws' for WhatsApp numbers or 'India Tg' for Telegram numbers."
        )

async def addlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process CSV file by asking for country name directly"""
    global uploaded_csv
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to perform this command.")
        return

    if not uploaded_csv:
        await update.message.reply_text("❌ No CSV file found. Please upload the file first.")
        return

    # Set user state to ask for country name directly
    user_states[user_id] = "waiting_for_country"
    await update.message.reply_text(
        "🌍 Please enter the country name for the numbers in the CSV file:\n"
        "Examples: Sri Lanka Ws, Sri Lanka Tg, India, Saudi Arabia, USA, etc.\n"
        "You can use custom names like 'India Ws' for WhatsApp numbers or 'India Tg' for Telegram numbers."
    )

async def process_all_numbers_with_country(update: Update, context: ContextTypes.DEFAULT_TYPE, country_name):
    """Process both manual numbers and CSV file with the provided country name"""
    global uploaded_csv
    user_id = update.effective_user.id
    
    await update.message.reply_text("🔍 Analyzing and processing all numbers...")

    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    # Get manual numbers
    manual_nums = manual_numbers.get(user_id, [])
    
    # Process CSV file if available
    csv_numbers = []
    if uploaded_csv:
        csv_numbers, process_msg = await process_csv_file(uploaded_csv)
        if not csv_numbers:
            csv_numbers = []

    # Combine all numbers
    all_numbers = []
    
    # Add manual numbers
    for number in manual_nums:
        all_numbers.append({
            'number': number,
            'original_number': number,
            'country_code': None,
            'range': '',
            'source': 'manual'
        })
    
    # Add CSV numbers
    for num_data in csv_numbers:
        all_numbers.append({
            'number': num_data['number'],
            'original_number': num_data['original_number'],
            'country_code': None,
            'range': num_data.get('range', ''),
            'source': 'csv'
        })

    if not all_numbers:
        await update.message.reply_text("❌ No numbers found to process.")
        return

    # Detect the most common country from all numbers
    detected_countries = {}
    for num_data in all_numbers:
        detected_country = detect_country_code(num_data['number'], num_data.get('range', ''))
        if detected_country:
            detected_countries[detected_country] = detected_countries.get(detected_country, 0) + 1
    
    # Get the most common detected country
    most_common_country = None
    if detected_countries:
        most_common_country = max(detected_countries, key=detected_countries.get)
    
    # Use the provided country name as the country code (custom naming)
    country_code = country_name.lower().replace(" ", "_")
    country_display_name = country_name
    
    # Store the detected country for flag purposes
    detected_country_code = most_common_country if most_common_country else "unknown"

    # Set country code for all numbers
    for num_data in all_numbers:
        num_data['country_code'] = country_code

    # Upload to database
    inserted_count = 0
    number_details = []
    manual_count = 0
    csv_count = 0

    for num_data in all_numbers:
        try:
            # Insert number with both custom country code and detected country
            await coll.insert_one({
                "country_code": num_data['country_code'],
                "number": num_data['number'],
                "original_number": num_data['original_number'],
                "range": num_data['range'],
                "detected_country": detected_country_code,
                "added_at": datetime.now(TIMEZONE)
            })
            
            inserted_count += 1
            if num_data['source'] == 'manual':
                manual_count += 1
            else:
                csv_count += 1
            
            # Get country flag from detected country, but display custom name
            flag = get_country_flag(detected_country_code)
            number_details.append(f"{flag} {num_data['number']} - {country_display_name}")
        except Exception as e:
            logging.error(f"Error inserting number: {e}")
            continue

    # Update countries collection
    await countries_coll.update_one(
        {"country_code": country_code},
        {"$set": {
            "country_code": country_code,
            "display_name": country_display_name,
            "detected_country": detected_country_code,
            "last_updated": datetime.now(TIMEZONE),
            "number_count": inserted_count
        }},
        upsert=True
    )

    # Clear all user data
    uploaded_csv = None
    if user_id in user_states:
        del user_states[user_id]
    if user_id in manual_numbers:
        del manual_numbers[user_id]

    # Prepare report
    report_lines = [
        "📊 Combined Upload Report:",
        f"✅ Successfully uploaded {inserted_count} numbers",
        f"📱 Manual numbers: {manual_count}",
        f"📄 CSV numbers: {csv_count}",
        f"🌍 Custom Name: {country_display_name}",
    ]
    
    if most_common_country:
        detected_country_name = "Unknown"
        try:
            country = pycountry.countries.get(alpha_2=most_common_country.upper())
            if country:
                detected_country_name = country.name
        except:
            pass
        report_lines.append(f"🏳️ Detected Country: {detected_country_name} ({most_common_country.upper()})")
    
    report_lines.extend([
        "",
        "📋 Sample numbers:",
        *number_details[:10]
    ])

    if len(number_details) > 10:
        report_lines.append(f"\n... and {len(number_details) - 10} more numbers")

    # Send report
    await update.message.reply_text("\n".join(report_lines))

    # Send complete list as file if many numbers
    if len(number_details) > 10:
        report_file = BytesIO()
        report_file.write("\n".join([
            "Number,Custom Country,Detected Country,Source",
            *[f"{num.split(' - ')[0]},{country_display_name},{detected_country_code.upper()},{'manual' if i < manual_count else 'csv'}" 
              for i, num in enumerate(number_details)]
        ]).encode('utf-8'))
        report_file.seek(0)
        await update.message.reply_document(
            document=report_file,
            filename="combined_number_upload_report.csv",
            caption="📄 Complete combined number upload report"
        )

async def process_csv_with_country(update: Update, context: ContextTypes.DEFAULT_TYPE, country_name):
    """Process CSV file with the provided country name"""
    global uploaded_csv
    user_id = update.effective_user.id
    
    if not uploaded_csv:
        await update.message.reply_text("❌ No CSV file found. Please upload the file first.")
        return

    await update.message.reply_text("🔍 Analyzing and processing numbers...")

    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    # Process CSV file first to detect country from numbers
    numbers, process_msg = await process_csv_file(uploaded_csv)
    if not numbers:
        await update.message.reply_text(f"❌ {process_msg}")
        return

    # Detect the most common country from the numbers
    detected_countries = {}
    for num_data in numbers:
        detected_country = detect_country_code(num_data['number'], num_data.get('range', ''))
        if detected_country:
            detected_countries[detected_country] = detected_countries.get(detected_country, 0) + 1
    
    # Get the most common detected country
    most_common_country = None
    if detected_countries:
        most_common_country = max(detected_countries, key=detected_countries.get)
    
    # Use the provided country name as the country code (custom naming)
    country_code = country_name.lower().replace(" ", "_")
    country_display_name = country_name
    
    # Store the detected country for flag purposes
    detected_country_code = most_common_country if most_common_country else "unknown"

    # Override country codes with the provided country
    for num_data in numbers:
        num_data['country_code'] = country_code

    # Upload to database
    inserted_count = 0
    number_details = []

    for num_data in numbers:
        try:
            # Insert number with both custom country code and detected country
            await coll.insert_one({
                "country_code": num_data['country_code'],
                "number": num_data['number'],
                "original_number": num_data['original_number'],
                "range": num_data['range'],
                "detected_country": detected_country_code,  # Store detected country for flag
                "added_at": datetime.now(TIMEZONE)
            })
            
            inserted_count += 1
            
            # Get country flag from detected country, but display custom name
            flag = get_country_flag(detected_country_code)
            number_details.append(f"{flag} {num_data['number']} - {country_display_name}")
        except Exception as e:
            logging.error(f"Error inserting number: {e}")
            continue

    # Update countries collection
    await countries_coll.update_one(
        {"country_code": country_code},
        {"$set": {
            "country_code": country_code,
            "display_name": country_display_name,
            "detected_country": detected_country_code,  # Store detected country
            "last_updated": datetime.now(TIMEZONE),
            "number_count": inserted_count
        }},
        upsert=True
    )

    uploaded_csv = None
    # Clear user state
    if user_id in user_states:
        del user_states[user_id]

    # Prepare report
    report_lines = [
        "📊 Upload Report:",
        f"✅ Successfully uploaded {inserted_count} numbers",
        f"🌍 Custom Name: {country_display_name}",
    ]
    
    if most_common_country:
        detected_country_name = "Unknown"
        try:
            country = pycountry.countries.get(alpha_2=most_common_country.upper())
            if country:
                detected_country_name = country.name
        except:
            pass
        report_lines.append(f"🏳️ Detected Country: {detected_country_name} ({most_common_country.upper()})")
    
    report_lines.extend([
        "",
        "📋 Sample numbers:",
        *number_details[:10]
    ])

    if len(number_details) > 10:
        report_lines.append(f"\n... and {len(number_details) - 10} more numbers")

    # Send report
    await update.message.reply_text("\n".join(report_lines))

    # Send complete list as file if many numbers
    if len(number_details) > 10:
        report_file = BytesIO()
        report_file.write("\n".join([
            "Number,Custom Country,Detected Country",
            *[f"{num.split(' - ')[0]},{country_display_name},{detected_country_code.upper()}" 
              for num in number_details]
        ]).encode('utf-8'))
        report_file.seek(0)
        await update.message.reply_document(
            document=report_file,
            filename="number_upload_report.csv",
            caption="📄 Complete number upload report"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for various inputs"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if user_id in user_states:
        state = user_states[user_id]
        text = update.message.text.strip()
        
        if state == "waiting_for_country":
            country_name = text
            await process_csv_with_country(update, context, country_name)
        
        elif state == "waiting_for_manual_numbers":
            if text.lower() == "done":
                if manual_numbers[user_id]:
                    # Skip CSV upload step and go directly to asking for country name
                    user_states[user_id] = "waiting_for_name"
                    await update.message.reply_text(
                        "✅ Numbers saved!\n"
                        f"📱 Total numbers entered: {len(manual_numbers[user_id])}\n\n"
                        "🌍 Please enter the name for the numbers:\n"
                        "Examples: Sri Lanka Ws, Sri Lanka Tg, etc.\n"
                        "This name will be used for all numbers."
                    )
                else:
                    await update.message.reply_text("❌ No numbers entered. Please enter some numbers first.")
            
            elif text.lower() == "cancel":
                # Clear user state
                if user_id in user_states:
                    del user_states[user_id]
                if user_id in manual_numbers:
                    del manual_numbers[user_id]
                await update.message.reply_text("❌ Operation cancelled.")
            
            else:
                # Process multiple numbers from the same message
                lines = text.split('\n')
                valid_numbers = []
                invalid_numbers = []
                
                for line in lines:
                    line = line.strip()
                    if line:  # Skip empty lines
                        cleaned_number = clean_number(line)
                        # Accept numbers with 8+ digits (including country codes)
                        if cleaned_number and len(cleaned_number) >= 8 and cleaned_number.isdigit():
                            valid_numbers.append(cleaned_number)
                        else:
                            invalid_numbers.append(line)
                
                # Add valid numbers
                for number in valid_numbers:
                    manual_numbers[user_id].append(number)
                
                # Send response
                if valid_numbers:
                    response = f"✅ Added {len(valid_numbers)} number(s):\n"
                    for number in valid_numbers:
                        response += f"• {number}\n"
                    response += f"\n📱 Total numbers: {len(manual_numbers[user_id])}\n\n"
                    
                    if invalid_numbers:
                        response += f"❌ Invalid numbers (skipped):\n"
                        for number in invalid_numbers:
                            response += f"• {number}\n"
                        response += "\n"
                    
                    response += "Enter more numbers or send 'done' when finished."
                    await update.message.reply_text(response)
                else:
                    await update.message.reply_text(
                        "❌ No valid numbers found. Please enter valid phone numbers.\n"
                        "Example: 94741854027\n"
                        f"Your input: {text}"
                    )
        
        elif state == "waiting_for_csv":
            # User sent a message instead of uploading CSV, proceed to ask for name
            user_states[user_id] = "waiting_for_name"
            await update.message.reply_text(
                "🌍 Please enter the name for the numbers:\n"
                "Examples: Sri Lanka Ws, Sri Lanka Tg, etc.\n"
                "This name will be used for all numbers."
            )
        
        elif state == "waiting_for_name":
            country_name = text
            await process_all_numbers_with_country(update, context, country_name)

async def background_otp_cleanup_task(app):
    """Background task that runs every minute to check all numbers for OTPs and clean them"""
    logging.info("🔄 Background OTP cleanup task started - checking every minute")
    
    # Wait for bot to fully initialize
    await asyncio.sleep(10)
    
    while True:
        try:
            await asyncio.sleep(60)  # Wait 1 minute
            
            logging.info("🔍 Starting background OTP cleanup check...")
            
            # Get database connection
            if "db" not in app.bot_data:
                logging.error("❌ Database not available for background cleanup")
                continue
                
            db = app.bot_data["db"]
            coll = db[COLLECTION_NAME]
            countries_coll = db[COUNTRIES_COLLECTION]
            
            # Get all numbers from database
            all_numbers = await coll.find({}).to_list(length=None)
            
            if not all_numbers:
                logging.info("ℹ️ No numbers in database to check")
                continue
                
            logging.info(f"🔍 Checking {len(all_numbers)} numbers for OTPs...")
            
            cleaned_count = 0
            skipped_count = 0
            
            for number_doc in all_numbers:
                try:
                    phone_number = str(number_doc.get('number', ''))
                    country_code = number_doc.get('country_code', '')
                    
                    if not phone_number:
                        continue
                    
                    # Skip numbers that have active monitoring sessions
                    has_active_session = False
                    for session_id, session_data in active_number_monitors.items():
                        if session_data.get('phone_number') == phone_number and not session_data.get('stop', True):
                            has_active_session = True
                            logging.info(f"⏭️ Background cleanup: Skipping {phone_number} - has active monitoring session {session_id}")
                            break
                    
                    if has_active_session:
                        skipped_count += 1
                        continue  # Skip this number, let real-time monitoring handle it
                    
                    # Check if this number has received an OTP
                    sms_info = await get_latest_sms_for_number(phone_number)
                    
                    if sms_info and sms_info.get('otp'):
                        otp = sms_info['otp']
                        sender = sms_info['sms'].get('sender', 'Unknown')
                        
                        logging.info(f"🎯 Background cleanup: Found OTP for {phone_number} - {sender}: {otp}")
                        
                        # Delete the number from database
                        delete_result = await coll.delete_one({"number": phone_number})
                        
                        if delete_result.deleted_count > 0:
                            # Update country count
                            if country_code:
                                await countries_coll.update_one(
                                    {"country_code": country_code},
                                    {"$inc": {"number_count": -1}}
                                )
                            
                            cleaned_count += 1
                            formatted_number = format_number_display(phone_number)
                            
                            logging.info(f"🗑️ Background cleanup: Deleted {phone_number} after detecting OTP: {otp}")
                            
                            # Send OTP notification to any users who had this number
                            users_notified = 0
                            for user_id, user_sessions in user_monitoring_sessions.items():
                                for session_id, session_data in user_sessions.items():
                                    if session_data.get('phone_number') == phone_number:
                                        try:
                                            await app.bot.send_message(
                                                chat_id=user_id,
                                                text=f"📞 Number: {formatted_number}\n🔐 {sender} : {otp}"
                                            )
                                            users_notified += 1
                                            logging.info(f"📱 Background cleanup: Sent OTP notification to user {user_id}")
                                        except Exception as notify_error:
                                            logging.error(f"Failed to notify user {user_id}: {notify_error}")
                                        break  # Only notify each user once
                            
                            # Stop any active monitoring sessions for this number
                            sessions_stopped = 0
                            sessions_to_remove = []
                            
                            for session_id, session_data in active_number_monitors.items():
                                if session_data.get('phone_number') == phone_number:
                                    logging.info(f"🛑 Background cleanup: Stopping monitoring session {session_id} for {phone_number}")
                                    session_data['stop'] = True
                                    sessions_to_remove.append(session_id)
                                    sessions_stopped += 1
                            
                            # Remove stopped sessions from active monitors
                            for session_id in sessions_to_remove:
                                if session_id in active_number_monitors:
                                    del active_number_monitors[session_id]
                            
                            # Also clean up user monitoring sessions
                            for user_id, user_sessions in user_monitoring_sessions.items():
                                user_sessions_to_remove = []
                                for session_id, session_data in user_sessions.items():
                                    if session_data.get('phone_number') == phone_number:
                                        logging.info(f"🛑 Background cleanup: Removing user session {session_id} for user {user_id}")
                                        user_sessions_to_remove.append(session_id)
                                
                                # Remove user sessions
                                for session_id in user_sessions_to_remove:
                                    if session_id in user_sessions:
                                        del user_sessions[session_id]
                            
                            # Send notification to all admins about the cleanup
                            for admin_id in ADMIN_IDS:
                                try:
                                    session_info = f"\n🛑 Stopped {sessions_stopped} monitoring session(s)" if sessions_stopped > 0 else ""
                                    user_info = f"\n📱 Notified {users_notified} user(s)" if users_notified > 0 else ""
                                    await app.bot.send_message(
                                        chat_id=admin_id,
                                        text=f"🔄 **Background Cleanup**\n\n"
                                             f"📞 Number: {formatted_number}\n"
                                             f"🔐 {sender} : {otp}\n"
                                             f"🗑️ Auto-deleted from server{session_info}{user_info}\n\n"
                                             f"ℹ️ _Background cleanup at {datetime.now(TIMEZONE).strftime('%H:%M:%S')}_",
                                        parse_mode=ParseMode.MARKDOWN
                                    )
                                except Exception as notify_error:
                                    logging.error(f"Failed to notify admin {admin_id}: {notify_error}")
                        
                        # Small delay between number checks to avoid overwhelming the API
                        await asyncio.sleep(1)
                        
                except Exception as number_error:
                    logging.error(f"Error checking number {phone_number}: {number_error}")
                    continue
            
            if cleaned_count > 0:
                logging.info(f"✅ Background cleanup completed: {cleaned_count} numbers cleaned, {skipped_count} numbers skipped (active sessions)")
            else:
                skip_info = f", {skipped_count} numbers skipped (active sessions)" if skipped_count > 0 else ""
                logging.info(f"ℹ️ Background cleanup completed: No numbers with OTPs found{skip_info}")
                
        except Exception as e:
            logging.error(f"❌ Background cleanup task error: {e}")
            # Continue running despite errors
            continue

# === MAIN BOT SETUP ===
async def post_init(app):
    """Initialize background tasks after bot startup"""
    logging.info("🔄 Starting background cleanup task...")
    try:
        asyncio.create_task(background_otp_cleanup_task(app))
    except Exception as e:
        logging.error(f"Failed to start background task: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    app.bot_data["db"] = db

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test", test_command))
    app.add_handler(CommandHandler("add", add_command))
    app.add_handler(CommandHandler("delete", delete_country))
    app.add_handler(CommandHandler("checkapi", check_api_connection))
    app.add_handler(CommandHandler("deleteall", delete_all_numbers))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("list", list_numbers))
    app.add_handler(CommandHandler("addlist", addlist))
    app.add_handler(CommandHandler("cleanup", cleanup_used_numbers))
    app.add_handler(CommandHandler("forceotp", force_otp_check))
    app.add_handler(CommandHandler("monitoring", check_monitoring_status))
    app.add_handler(CommandHandler("countrynumbers", check_country_numbers))
    app.add_handler(CommandHandler("resetnumber", reset_current_number))
    app.add_handler(CommandHandler("morningcalls", show_my_morning_calls))
    app.add_handler(CommandHandler("updatesms", update_sms_session))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(request_number, pattern="request_number"))
    app.add_handler(CallbackQueryHandler(send_number, pattern="^country_"))
    app.add_handler(CallbackQueryHandler(change_number, pattern="^change_"))
    app.add_handler(CallbackQueryHandler(show_sms, pattern="^sms_"))
    app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv") & filters.User(ADMIN_IDS), upload_csv))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), handle_text_message))
    
    logging.info("Bot started and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()