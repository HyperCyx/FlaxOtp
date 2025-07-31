import logging
from io import BytesIO, StringIO
from datetime import datetime
import csv
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
import re

# === CONFIGURATION ===
TOKEN = "7650570527:AAG9K_XGEZ2MGcXkBc2h7cltVPQTWayhh00"
CHANNEL_ID = -1002555911826
CHANNEL_LINK = "https://t.me/+6Cw11PRcrFc1NmI1"
MONGO_URI = "mongodb+srv://noob:K3a4ofLngiMG8Hl9@tele.fjm9acq.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "TelegramBotDB"
COLLECTION_NAME = "numbers"
COUNTRIES_COLLECTION = "countries"
ADMIN_IDS = {7762548831}

TIMEZONE = pytz.timezone('Asia/Riyadh')
logging.basicConfig(level=logging.INFO)
uploaded_csv = None
user_states = {}  # Store user states for country input

# === UTILITY FUNCTIONS ===
def get_country_flag(country_code):
    """Get country flag emoji from country code"""
    try:
        country_code = country_code.upper()
        if country_code == 'XK':
            return '🇽🇰'
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
    """Detect country code from number and range string"""
    # First try to detect from range string
    if range_str:
        country_code = extract_country_from_range(range_str)
        if country_code:
            return country_code
    
    # Then try to detect from number prefix
    number = clean_number(str(number))
    
    # Known country prefixes
    country_prefixes = {
        '591': 'bo',  # Bolivia
        '51': 'pe',   # Peru
        '1': 'us',    # USA
        '44': 'gb',   # UK
        '91': 'in',   # India
        '966': 'sa',  # Saudi Arabia
    }
    
    # Check if number starts with known prefix
    for prefix, code in country_prefixes.items():
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
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ("member", "administrator", "creator"):
            await update.message.reply_text(
                "✅ Channel join confirmed!\nYou can now request a number.",
                reply_markup=number_keyboard()
            )
        else:
            await update.message.reply_text("🚫 You haven't joined the channel yet!")
            await update.message.reply_text(
                "Please join the channel and check again.",
                reply_markup=join_channel_keyboard()
            )
    except Exception:
        await update.message.reply_text("🚫 You haven't joined the channel yet!")
        await update.message.reply_text(
            "Please join the channel and check again.",
            reply_markup=join_channel_keyboard()
        )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if chat_member.status in ("member", "administrator", "creator"):
            await query.edit_message_text(
                "✅ Channel join confirmed!\nYou can now request a number.",
                reply_markup=number_keyboard()
            )
        else:
            await query.answer("You haven't joined the channel yet!", show_alert=True)
    except Exception:
        await query.answer("You haven't joined the channel yet!", show_alert=True)

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

    result = await coll.find_one_and_delete({"country_code": country_code})
    
    if result and "number" in result:
        number = result["number"]
        formatted_number = format_number_display(number)
        
        message = (
            f"🌐 Country: {country_name}\n"
            f"📞 Number: {formatted_number}\n\n"
            "Select an option:"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=number_options_keyboard(number, country_code)
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

    result = await coll.find_one_and_delete({"country_code": country_code})
    
    if result and "number" in result:
        number = result["number"]
        formatted_number = format_number_display(number)
        
        message = (
            f"🌐 Country: {country_name}\n"
            f"📞 Number: {formatted_number}\n\n"
            "Select an option:"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=number_options_keyboard(number, country_code)
        )
    else:
        keyboard = await countries_keyboard(db)
        await query.edit_message_text(
            f"⚠️ No more numbers available for {country_name}. Please select another country.",
            reply_markup=keyboard
        )

async def show_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    number = query.data.split('_', 1)[1]
    await query.answer(f"SMS for {number} will be displayed here", show_alert=True)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    db = context.bot_data["db"]
    keyboard = await countries_keyboard(db)
    await query.edit_message_text(
        "🌍 Select Country:",
        reply_markup=keyboard
    )

async def delete_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to delete numbers.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Usage: /delete <country_code>\nExample: /delete sa")
        return

    country_code = args[0].lower()
    
    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    country_exists = await countries_coll.count_documents({"country_code": country_code}) > 0
    if not country_exists:
        await update.message.reply_text(f"❌ Country code '{country_code}' not found in database.")
        return

    result = await coll.delete_many({"country_code": country_code})
    await update.message.reply_text(
        f"✅ Deleted {result.deleted_count} numbers for country `{country_code}`.",
        parse_mode=ParseMode.MARKDOWN
    )

def format_number_display(number):
    """Format number for display with proper spacing"""
    number = clean_number(number)
    if number.startswith("+"):
        return number
    elif len(number) == 12 and number.startswith("966"):
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

    # Set user state to wait for country input
    user_states[user_id] = "waiting_for_country"
    
    # Ask for country name
    await update.message.reply_text(
        "🌍 Please enter the country name for the numbers in this CSV file:\n"
        "Example: Saudi Arabia, USA, India, etc."
    )

async def addlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global uploaded_csv
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You are not authorized to perform this command.")
        return

    if not uploaded_csv:
        await update.message.reply_text("❌ No CSV file found. Please upload the file first.")
        return

    await update.message.reply_text("🔍 Analyzing and processing numbers...")

    db = context.bot_data["db"]
    coll = db[COLLECTION_NAME]
    countries_coll = db[COUNTRIES_COLLECTION]

    # Process CSV file
    numbers, process_msg = await process_csv_file(uploaded_csv)
    if not numbers:
        await update.message.reply_text(f"❌ {process_msg}")
        return

    # Upload to database
    inserted_count = 0
    country_stats = {}
    number_details = []

    for num_data in numbers:
        try:
            # Insert number
            await coll.insert_one({
                "country_code": num_data['country_code'],
                "number": num_data['number'],
                "original_number": num_data['original_number'],
                "range": num_data['range'],
                "added_at": datetime.now(TIMEZONE)
            })
            
            # Update statistics
            if num_data['country_code'] not in country_stats:
                country_stats[num_data['country_code']] = 0
            country_stats[num_data['country_code']] += 1
            inserted_count += 1
            
            # Get country info
            country = pycountry.countries.get(alpha_2=num_data['country_code'].upper())
            country_name = country.name if country else num_data['country_code']
            flag = get_country_flag(num_data['country_code'])
            
            number_details.append(f"{flag} {num_data['number']} - {country_name}")
        except Exception as e:
            logging.error(f"Error inserting number: {e}")
            continue

    # Update countries collection
    for country_code, count in country_stats.items():
        country = pycountry.countries.get(alpha_2=country_code.upper())
        display_name = country.name if country else country_code
        
        await countries_coll.update_one(
            {"country_code": country_code},
            {"$set": {
                "country_code": country_code,
                "display_name": display_name,
                "last_updated": datetime.now(TIMEZONE),
                "number_count": count
            }},
            upsert=True
        )

    uploaded_csv = None

    # Prepare report
    report_lines = [
        "📊 Upload Report:",
        f"✅ Successfully uploaded {inserted_count} numbers",
        "",
        "🌍 Countries detected:"
    ]

    # Add country statistics
    for country_code, count in country_stats.items():
        country_info = await countries_coll.find_one({"country_code": country_code})
        country_name = country_info["display_name"] if country_info else country_code
        flag = get_country_flag(country_code)
        report_lines.append(f"{flag} {country_name}: {count} numbers")

    # Add sample numbers (first 10)
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
            "Number,Country,Country Code",
            *[f"{num.split(' - ')[0]},{num.split(' - ')[1]},{num_data['country_code']}" 
              for num, num_data in zip(number_details, numbers)]
        ]).encode('utf-8'))
        report_file.seek(0)
        await update.message.reply_document(
            document=report_file,
            filename="number_upload_report.csv",
            caption="📄 Complete number upload report"
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

    # Try to find country code from the provided country name
    country_code = None
    try:
        # Search for country using pycountry
        countries = pycountry.countries.search_fuzzy(country_name)
        if countries:
            country_code = countries[0].alpha_2.lower()
            country_display_name = countries[0].name
        else:
            await update.message.reply_text(f"❌ Could not find country: {country_name}")
            return
    except Exception as e:
        await update.message.reply_text(f"❌ Error finding country: {str(e)}")
        return

    # Process CSV file
    numbers, process_msg = await process_csv_file(uploaded_csv)
    if not numbers:
        await update.message.reply_text(f"❌ {process_msg}")
        return

    # Override country codes with the provided country
    for num_data in numbers:
        num_data['country_code'] = country_code

    # Upload to database
    inserted_count = 0
    number_details = []

    for num_data in numbers:
        try:
            # Insert number
            await coll.insert_one({
                "country_code": num_data['country_code'],
                "number": num_data['number'],
                "original_number": num_data['original_number'],
                "range": num_data['range'],
                "added_at": datetime.now(TIMEZONE)
            })
            
            inserted_count += 1
            
            # Get country info
            flag = get_country_flag(num_data['country_code'])
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
        f"🌍 Country: {country_display_name}",
        "",
        "📋 Sample numbers:",
        *number_details[:10]
    ]

    if len(number_details) > 10:
        report_lines.append(f"\n... and {len(number_details) - 10} more numbers")

    # Send report
    await update.message.reply_text("\n".join(report_lines))

    # Send complete list as file if many numbers
    if len(number_details) > 10:
        report_file = BytesIO()
        report_file.write("\n".join([
            "Number,Country,Country Code",
            *[f"{num.split(' - ')[0]},{country_display_name},{country_code}" 
              for num in number_details]
        ]).encode('utf-8'))
        report_file.seek(0)
        await update.message.reply_document(
            document=report_file,
            filename="number_upload_report.csv",
            caption="📄 Complete number upload report"
        )

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for country input"""
    user_id = update.effective_user.id
    
    if user_id not in ADMIN_IDS:
        return
    
    if user_id in user_states and user_states[user_id] == "waiting_for_country":
        country_name = update.message.text.strip()
        await process_csv_with_country(update, context, country_name)

# === MAIN BOT SETUP ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[DB_NAME]
    app.bot_data["db"] = db

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
    app.add_handler(CallbackQueryHandler(request_number, pattern="request_number"))
    app.add_handler(CallbackQueryHandler(send_number, pattern="^country_"))
    app.add_handler(CallbackQueryHandler(change_number, pattern="^change_"))
    app.add_handler(CallbackQueryHandler(show_sms, pattern="^sms_"))
    app.add_handler(CallbackQueryHandler(menu, pattern="^menu$"))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv") & filters.User(ADMIN_IDS), upload_csv))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_IDS), handle_text_message))
    app.add_handler(CommandHandler("addlist", addlist))
    app.add_handler(CommandHandler("delete", delete_country))

    logging.info("Bot started and polling...")
    app.run_polling()

if __name__ == "__main__":
    main()