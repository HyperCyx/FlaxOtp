#!/usr/bin/env python3
"""
CSV Number Provider - Provides numbers from CSV files instead of MongoDB
Replaces the MongoDB-based number retrieval with file-based system
"""

import logging
from typing import Optional, Tuple, Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from csv_number_manager import get_random_number, list_csv_countries

async def get_number_from_csv(country_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Get a random number from CSV files
    Returns: (number, source_info) or (None, None) if no numbers available
    """
    try:
        number, source_file = await get_random_number(country_name)
        
        if number and source_file:
            # Format the number for display
            formatted_number = format_number_display(number)
            return formatted_number, source_file
        
        return None, None
        
    except Exception as e:
        logging.error(f"Error getting number from CSV: {e}")
        return None, None

def format_number_display(number: str) -> str:
    """Format phone number for display"""
    if not number:
        return ""
    
    # Clean the number
    cleaned = ''.join(filter(str.isdigit, number.replace('+', '')))
    
    # Add + prefix if not present
    if not number.startswith('+'):
        number = '+' + cleaned
    
    return number

async def show_csv_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show available countries from CSV files instead of MongoDB
    """
    try:
        countries = await list_csv_countries()
        
        if not countries:
            await update.message.reply_text(
                "📭 **No numbers available**\n\n"
                "No CSV files have been uploaded yet.\n"
                "Please contact an administrator to upload number files."
            )
            return
        
        # Create inline keyboard with countries
        keyboard = []
        for country in countries[:20]:  # Limit to 20 countries for UI
            country_name = country['country_name']
            number_count = country['total_numbers']
            
            # Create button text with count
            button_text = f"{country_name} ({number_count:,})"
            callback_data = f"csvnum_{country_name}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        # Add "Any Country" option
        keyboard.insert(0, [InlineKeyboardButton("🌍 Any Country (Random)", callback_data="csvnum_any")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message_text = [
            "🌍 **Choose Country/Category:**",
            "",
            "Select a country or category to get a phone number:",
            "",
            f"📊 **Available Options: {len(countries)}**"
        ]
        
        if len(countries) > 20:
            message_text.append(f"Showing first 20 options")
        
        await update.message.reply_text(
            "\n".join(message_text),
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logging.error(f"Error showing CSV countries: {e}")
        await update.message.reply_text(f"❌ Error loading countries: {str(e)}")

async def handle_csv_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle country selection from CSV files
    """
    query = update.callback_query
    await query.answer()
    
    try:
        # Extract country name from callback data
        callback_data = query.data
        if not callback_data.startswith("csvnum_"):
            return
        
        country_selection = callback_data.replace("csvnum_", "")
        
        # Handle "any" selection
        if country_selection == "any":
            country_name = None
            display_name = "Random Country"
        else:
            country_name = country_selection
            display_name = country_name
        
        # Get number from CSV files
        number, source_file = await get_number_from_csv(country_name)
        
        if not number:
            await query.edit_message_text(
                f"❌ **No numbers available**\n\n"
                f"No numbers found for {display_name}.\n"
                f"Please try a different category or contact an administrator."
            )
            return
        
        # Store the current number for this user
        user_id = update.effective_user.id
        current_user_numbers = context.bot_data.get("current_user_numbers", {})
        current_user_numbers[user_id] = number
        context.bot_data["current_user_numbers"] = current_user_numbers
        
        # Create response message
        response_parts = [
            f"📱 **Your Phone Number:**",
            "",
            f"🔢 **Number:** `{number}`",
            f"🌍 **Source:** {display_name}",
            f"📁 **File:** {source_file}",
            "",
            f"⏰ **Ready for OTP reception!**",
            "",
            "🔄 Use the buttons below to manage your number:"
        ]
        
        # Create inline keyboard for number management
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status"),
                InlineKeyboardButton("📱 New Number", callback_data="request_number")
            ],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="menu")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "\n".join(response_parts),
            reply_markup=reply_markup
        )
        
        # Start OTP monitoring for this number
        await start_csv_number_monitoring(update, context, number, source_file)
        
    except Exception as e:
        logging.error(f"Error handling CSV country selection: {e}")
        await query.edit_message_text(f"❌ Error getting number: {str(e)}")

async def start_csv_number_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE, number: str, source_file: str):
    """
    Start OTP monitoring for a number from CSV files
    This integrates with the existing OTP monitoring system
    """
    try:
        user_id = update.effective_user.id
        
        # Import existing OTP monitoring functions
        # These should work the same way regardless of number source
        from bot import get_latest_sms_for_number
        
        # Check for immediate SMS
        sms_info = await get_latest_sms_for_number(number)
        
        if sms_info and sms_info.get('otp'):
            # Found immediate OTP
            otp_message = [
                f"🎉 **OTP Found Immediately!**",
                "",
                f"📱 **Number:** `{number}`",
                f"🔐 **OTP:** `{sms_info['otp']}`",
                f"📅 **Time:** {sms_info.get('timestamp', 'Unknown')}",
                "",
                f"📄 **Message:** {sms_info.get('message', 'N/A')}"
            ]
            
            await context.bot.send_message(
                chat_id=user_id,
                text="\n".join(otp_message)
            )
        
        # Continue with regular monitoring
        # The existing monitoring system should work with any number
        
    except Exception as e:
        logging.error(f"Error starting CSV number monitoring: {e}")

async def get_csv_number_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show statistics for CSV-based numbers (user-facing)
    """
    try:
        countries = await list_csv_countries()
        
        if not countries:
            await update.message.reply_text("📭 No number sources available.")
            return
        
        total_numbers = sum(country['total_numbers'] for country in countries)
        total_usage = sum(country['total_usage'] for country in countries)
        
        message_parts = [
            "📊 **Number Statistics**",
            "",
            f"🌍 **Available Categories:** {len(countries)}",
            f"📱 **Total Numbers:** {total_numbers:,}",
            f"🔄 **Numbers Used:** {total_usage:,}",
            "",
            "🏆 **Top Categories:**"
        ]
        
        # Sort by number count and show top 5
        top_countries = sorted(countries, key=lambda x: x['total_numbers'], reverse=True)[:5]
        
        for i, country in enumerate(top_countries, 1):
            usage_percent = (country['total_usage'] / country['total_numbers'] * 100) if country['total_numbers'] > 0 else 0
            message_parts.append(
                f"{i}. **{country['country_name']}** - {country['total_numbers']:,} numbers ({usage_percent:.1f}% used)"
            )
        
        await update.message.reply_text("\n".join(message_parts))
        
    except Exception as e:
        logging.error(f"Error getting CSV number stats: {e}")
        await update.message.reply_text(f"❌ Error getting statistics: {str(e)}")

# Integration helper functions
def replace_mongodb_number_functions():
    """
    Helper function to replace MongoDB number functions with CSV versions
    This can be called during bot initialization
    """
    # This would replace the existing MongoDB functions in the main bot
    # The exact implementation depends on how you want to integrate
    pass