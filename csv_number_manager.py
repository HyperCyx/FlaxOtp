#!/usr/bin/env python3
"""
CSV Number Manager - File-based number storage and retrieval system
Stores CSV files on server filesystem and provides numbers on demand
"""

import os
import csv
import json
import random
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from io import StringIO
import asyncio

# Configuration
CSV_STORAGE_DIR = "/app/csv_files"
USAGE_TRACKING_FILE = "/app/csv_files/usage_tracking.json"
CSV_METADATA_FILE = "/app/csv_files/metadata.json"

class CSVNumberManager:
    def __init__(self):
        self.csv_storage_dir = CSV_STORAGE_DIR
        self.usage_tracking_file = USAGE_TRACKING_FILE
        self.metadata_file = CSV_METADATA_FILE
        self.ensure_directories()
        
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.csv_storage_dir, exist_ok=True)
        
    async def save_csv_file(self, file_bytes, country_name: str, admin_id: int) -> Tuple[bool, str]:
        """
        Save CSV file to server filesystem
        Returns: (success: bool, message: str)
        """
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{country_name.replace(' ', '_')}_{timestamp}.csv"
            filepath = os.path.join(self.csv_storage_dir, filename)
            
            # Validate and process CSV content
            file_text = file_bytes.getvalue().decode('utf-8')
            csv_reader = csv.DictReader(StringIO(file_text))
            
            # Verify required columns
            if 'Number' not in csv_reader.fieldnames:
                return False, "CSV file must contain a 'Number' column"
            
            # Count valid numbers
            valid_numbers = 0
            processed_content = []
            
            # Re-read for processing (csv reader consumed)
            csv_reader = csv.DictReader(StringIO(file_text))
            
            for row in csv_reader:
                number = row.get('Number', '').strip()
                if number:
                    valid_numbers += 1
                    processed_content.append(row)
            
            if valid_numbers == 0:
                return False, "No valid numbers found in CSV file"
            
            # Save CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                if processed_content:
                    fieldnames = processed_content[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(processed_content)
            
            # Update metadata
            await self.update_metadata(filename, country_name, admin_id, valid_numbers)
            
            logging.info(f"CSV file saved: {filepath} with {valid_numbers} numbers")
            return True, f"Successfully saved {valid_numbers} numbers to file: {filename}"
            
        except Exception as e:
            logging.error(f"Error saving CSV file: {e}")
            return False, f"Error saving CSV file: {str(e)}"
    
    async def update_metadata(self, filename: str, country_name: str, admin_id: int, number_count: int):
        """Update metadata file with CSV information"""
        try:
            metadata = {}
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            metadata[filename] = {
                "country_name": country_name,
                "admin_id": admin_id,
                "number_count": number_count,
                "created_at": datetime.now().isoformat(),
                "usage_count": 0
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error updating metadata: {e}")
    
    async def get_random_number(self, country_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Get a random number from stored CSV files
        Returns: (number: str, source_file: str) or (None, None) if no numbers available
        """
        try:
            # Get available CSV files
            csv_files = self.get_available_csv_files(country_name)
            
            if not csv_files:
                return None, None
            
            # Select random file (weighted by number count)
            selected_file = random.choice(csv_files)
            filepath = os.path.join(self.csv_storage_dir, selected_file)
            
            # Read numbers from selected file
            numbers = []
            with open(filepath, 'r', newline='', encoding='utf-8') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                for row in csv_reader:
                    number = row.get('Number', '').strip()
                    if number:
                        numbers.append(number)
            
            if not numbers:
                return None, None
            
            # Select random number
            selected_number = random.choice(numbers)
            
            # Track usage
            await self.track_usage(selected_file, selected_number)
            
            logging.info(f"Provided number {selected_number} from file {selected_file}")
            return selected_number, selected_file
            
        except Exception as e:
            logging.error(f"Error getting random number: {e}")
            return None, None
    
    def get_available_csv_files(self, country_name: Optional[str] = None) -> List[str]:
        """Get list of available CSV files, optionally filtered by country"""
        try:
            if not os.path.exists(self.csv_storage_dir):
                return []
            
            csv_files = []
            for filename in os.listdir(self.csv_storage_dir):
                if filename.endswith('.csv'):
                    if country_name:
                        # Filter by country name if specified
                        if country_name.lower().replace(' ', '_') in filename.lower():
                            csv_files.append(filename)
                    else:
                        csv_files.append(filename)
            
            return csv_files
            
        except Exception as e:
            logging.error(f"Error getting CSV files: {e}")
            return []
    
    async def track_usage(self, filename: str, number: str):
        """Track number usage for statistics"""
        try:
            usage_data = {}
            if os.path.exists(self.usage_tracking_file):
                with open(self.usage_tracking_file, 'r') as f:
                    usage_data = json.load(f)
            
            if filename not in usage_data:
                usage_data[filename] = {
                    "total_usage": 0,
                    "numbers_used": {},
                    "last_used": None
                }
            
            usage_data[filename]["total_usage"] += 1
            usage_data[filename]["last_used"] = datetime.now().isoformat()
            
            if number not in usage_data[filename]["numbers_used"]:
                usage_data[filename]["numbers_used"][number] = 0
            usage_data[filename]["numbers_used"][number] += 1
            
            with open(self.usage_tracking_file, 'w') as f:
                json.dump(usage_data, f, indent=2)
                
            # Update metadata usage count
            await self.update_metadata_usage(filename)
            
        except Exception as e:
            logging.error(f"Error tracking usage: {e}")
    
    async def update_metadata_usage(self, filename: str):
        """Update usage count in metadata"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                if filename in metadata:
                    metadata[filename]["usage_count"] = metadata[filename].get("usage_count", 0) + 1
                
                with open(self.metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                    
        except Exception as e:
            logging.error(f"Error updating metadata usage: {e}")
    
    async def get_statistics(self) -> Dict:
        """Get statistics about stored CSV files and usage"""
        try:
            stats = {
                "total_files": 0,
                "total_numbers": 0,
                "total_usage": 0,
                "files": []
            }
            
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                for filename, info in metadata.items():
                    stats["total_files"] += 1
                    stats["total_numbers"] += info.get("number_count", 0)
                    stats["total_usage"] += info.get("usage_count", 0)
                    
                    stats["files"].append({
                        "filename": filename,
                        "country_name": info.get("country_name", "Unknown"),
                        "number_count": info.get("number_count", 0),
                        "usage_count": info.get("usage_count", 0),
                        "created_at": info.get("created_at", "Unknown")
                    })
            
            return stats
            
        except Exception as e:
            logging.error(f"Error getting statistics: {e}")
            return {"error": str(e)}
    
    async def list_countries(self) -> List[Dict]:
        """List available countries from stored CSV files"""
        try:
            countries = []
            
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                country_summary = {}
                for filename, info in metadata.items():
                    country_name = info.get("country_name", "Unknown")
                    
                    if country_name not in country_summary:
                        country_summary[country_name] = {
                            "country_name": country_name,
                            "total_numbers": 0,
                            "files_count": 0,
                            "total_usage": 0
                        }
                    
                    country_summary[country_name]["total_numbers"] += info.get("number_count", 0)
                    country_summary[country_name]["files_count"] += 1
                    country_summary[country_name]["total_usage"] += info.get("usage_count", 0)
                
                countries = list(country_summary.values())
            
            return countries
            
        except Exception as e:
            logging.error(f"Error listing countries: {e}")
            return []
    
    async def delete_csv_file(self, filename: str) -> Tuple[bool, str]:
        """Delete a CSV file and its metadata"""
        try:
            filepath = os.path.join(self.csv_storage_dir, filename)
            
            if not os.path.exists(filepath):
                return False, f"File {filename} not found"
            
            # Remove file
            os.remove(filepath)
            
            # Remove from metadata
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                if filename in metadata:
                    del metadata[filename]
                
                with open(self.metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            # Remove from usage tracking
            if os.path.exists(self.usage_tracking_file):
                with open(self.usage_tracking_file, 'r') as f:
                    usage_data = json.load(f)
                
                if filename in usage_data:
                    del usage_data[filename]
                
                with open(self.usage_tracking_file, 'w') as f:
                    json.dump(usage_data, f, indent=2)
            
            logging.info(f"Deleted CSV file: {filename}")
            return True, f"Successfully deleted file: {filename}"
            
        except Exception as e:
            logging.error(f"Error deleting CSV file {filename}: {e}")
            return False, f"Error deleting file: {str(e)}"


# Global instance
csv_manager = CSVNumberManager()

# Convenience functions for bot integration
async def save_csv_file(file_bytes, country_name: str, admin_id: int) -> Tuple[bool, str]:
    """Save CSV file to filesystem"""
    return await csv_manager.save_csv_file(file_bytes, country_name, admin_id)

async def get_random_number(country_name: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """Get random number from CSV files"""
    return await csv_manager.get_random_number(country_name)

async def get_csv_statistics() -> Dict:
    """Get CSV storage statistics"""
    return await csv_manager.get_statistics()

async def list_csv_countries() -> List[Dict]:
    """List countries available in CSV files"""
    return await csv_manager.list_countries()

async def delete_csv_file(filename: str) -> Tuple[bool, str]:
    """Delete CSV file"""
    return await csv_manager.delete_csv_file(filename)