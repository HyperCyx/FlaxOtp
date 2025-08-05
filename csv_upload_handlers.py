#!/usr/bin/env python3
"""
Modified upload handlers for file-based CSV storage system
Replaces MongoDB storage with filesystem-based approach
"""

import logging
from io import BytesIO
from telegram import Update
from telegram.ext import ContextTypes
from csv_number_manager import save_csv_file, get_csv_statistics, list_csv_countries

# Global variable to track uploaded CSV for processing
uploaded_csv_file = None
uploaded_csv_country = None

async def upload_csv_to_filesystem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle CSV file upload and save to filesystem instead of MongoDB
    """
    global uploaded_csv_file, uploaded_csv_country
    
    user_id = update.effective_user.id
    
    # Check admin privileges (assuming ADMIN_IDS is imported from config)
    from config import ADMIN_IDS
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Only administrators can upload CSV files.")
        return

    if not update.message.document:
        await update.message.reply_text("❌ Please upload a CSV file.")
        return

    file = update.message.document
    if not file.file_name.lower().endswith('.csv'):
        await update.message.reply_text("❌ Only CSV files are supported.")
        return

    try:
        await update.message.reply_text("📥 Processing CSV file...")
        
        # Download file
        file_obj = await context.bot.get_file(file.file_id)
        file_bytes = BytesIO()
        await file_obj.download_to_memory(file_bytes)
        
        # Store temporarily for country name input
        uploaded_csv_file = file_bytes
        
        await update.message.reply_text(
            "🌍 Please enter the country/category name for this CSV file:\n\n"
            "Example: 'Saudi Arabia Mobile', 'UAE Numbers', 'Test Data'\n\n"
            "This name will be used to organize and identify the numbers."
        )
        
    except Exception as e:
        logging.error(f"Error processing CSV upload: {e}")
        await update.message.reply_text(f"❌ Error processing file: {str(e)}")

async def process_csv_with_country_name(update: Update, context: ContextTypes.DEFAULT_TYPE, country_name: str):
    """
    Process the uploaded CSV file with the provided country name
    """
    global uploaded_csv_file
    
    if not uploaded_csv_file:
        await update.message.reply_text("❌ No CSV file found. Please upload a file first.")
        return

    try:
        user_id = update.effective_user.id
        
        # Save CSV file to filesystem
        success, message = await save_csv_file(uploaded_csv_file, country_name, user_id)
        
        if success:
            # Get updated statistics
            stats = await get_csv_statistics()
            
            response_message = [
                "✅ **CSV File Successfully Saved!**",
                "",
                f"📊 **Upload Details:**",
                f"• {message}",
                f"• Country/Category: {country_name}",
                f"• Uploaded by: {update.effective_user.first_name or 'Admin'}",
                "",
                f"📈 **System Statistics:**",
                f"• Total CSV files: {stats.get('total_files', 0)}",
                f"• Total numbers available: {stats.get('total_numbers', 0)}",
                f"• Total numbers used: {stats.get('total_usage', 0)}",
                "",
                "🔄 **Numbers are now available for users!**",
                "Use `/csvstats` to view detailed statistics."
            ]
            
            await update.message.reply_text("\n".join(response_message))
            
        else:
            await update.message.reply_text(f"❌ Failed to save CSV file: {message}")
            
    except Exception as e:
        logging.error(f"Error saving CSV file: {e}")
        await update.message.reply_text(f"❌ Error saving file: {str(e)}")
    
    finally:
        # Clear temporary storage
        uploaded_csv_file = None

async def show_csv_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show detailed CSV storage statistics
    """
    user_id = update.effective_user.id
    
    # Check admin privileges
    from config import ADMIN_IDS
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Only administrators can view CSV statistics.")
        return
    
    try:
        stats = await get_csv_statistics()
        
        if "error" in stats:
            await update.message.reply_text(f"❌ Error getting statistics: {stats['error']}")
            return
        
        message_parts = [
            "📊 **CSV Storage Statistics**",
            "",
            f"📁 **Overview:**",
            f"• Total CSV files: {stats.get('total_files', 0)}",
            f"• Total numbers stored: {stats.get('total_numbers', 0):,}",
            f"• Total numbers used: {stats.get('total_usage', 0):,}",
            ""
        ]
        
        if stats.get('files'):
            message_parts.append("📋 **File Details:**")
            
            for file_info in stats['files'][:10]:  # Show first 10 files
                usage_percent = (file_info['usage_count'] / file_info['number_count'] * 100) if file_info['number_count'] > 0 else 0
                
                message_parts.extend([
                    f"",
                    f"**{file_info['country_name']}**",
                    f"• File: `{file_info['filename']}`",
                    f"• Numbers: {file_info['number_count']:,}",
                    f"• Used: {file_info['usage_count']:,} ({usage_percent:.1f}%)",
                    f"• Created: {file_info['created_at'][:10]}"  # Just date part
                ])
            
            if len(stats['files']) > 10:
                message_parts.append(f"\n... and {len(stats['files']) - 10} more files")
        
        else:
            message_parts.append("📭 No CSV files uploaded yet.")
        
        await update.message.reply_text("\n".join(message_parts))
        
    except Exception as e:
        logging.error(f"Error showing CSV statistics: {e}")
        await update.message.reply_text(f"❌ Error retrieving statistics: {str(e)}")

async def list_csv_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    List available CSV files and countries
    """
    user_id = update.effective_user.id
    
    # Check admin privileges
    from config import ADMIN_IDS
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Access denied. Only administrators can view CSV files.")
        return
    
    try:
        countries = await list_csv_countries()
        
        if not countries:
            await update.message.reply_text("📭 No CSV files uploaded yet.")
            return
        
        message_parts = [
            "🌍 **Available Countries/Categories:**",
            ""
        ]
        
        for country in countries:
            usage_percent = (country['total_usage'] / country['total_numbers'] * 100) if country['total_numbers'] > 0 else 0
            
            message_parts.extend([
                f"**{country['country_name']}**",
                f"• Numbers: {country['total_numbers']:,}",
                f"• Files: {country['files_count']}",
                f"• Usage: {country['total_usage']:,} ({usage_percent:.1f}%)",
                ""
            ])
        
        await update.message.reply_text("\n".join(message_parts))
        
    except Exception as e:
        logging.error(f"Error listing CSV files: {e}")
        await update.message.reply_text(f"❌ Error listing files: {str(e)}")

async def handle_csv_country_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle country name input for CSV processing
    This should be called when admin sends text after uploading CSV
    """
    global uploaded_csv_file
    
    user_id = update.effective_user.id
    
    # Check if user is admin and has uploaded CSV
    from config import ADMIN_IDS
    if user_id not in ADMIN_IDS:
        return False  # Not handling this message
    
    if not uploaded_csv_file:
        return False  # No CSV file waiting for processing
    
    # Get country name from message
    country_name = update.message.text.strip()
    
    if len(country_name) < 2:
        await update.message.reply_text("❌ Please enter a valid country/category name (at least 2 characters).")
        return True
    
    # Process the CSV file
    await process_csv_with_country_name(update, context, country_name)
    return True