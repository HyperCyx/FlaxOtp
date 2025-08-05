# 📊 CSV Upload System Guide

## 🎯 **Overview**

Your Telegram bot includes a powerful CSV upload system that allows admins to bulk upload phone numbers directly from CSV files. The system automatically processes numbers, detects countries, and stores them in the MongoDB database.

## 🔐 **Access Control**

- ✅ **Admin Only**: Only users with admin privileges can upload CSV files
- ✅ **Automatic Detection**: Admin status automatically detected from `ADMIN_IDS` config
- ✅ **Secure Upload**: All uploads are validated and processed securely

## 📋 **CSV File Format Requirements**

### **Required Column:**
- `Number` - Phone numbers (with or without country codes)

### **Optional Column:**
- `Range` - Description/category for the numbers (e.g., "US-Mobile", "UK-London")

### **Supported Formats:**

#### **Format 1: Number Only (Minimal)**
```csv
Number
+1234567890
+447911123456
+966501234567
```

#### **Format 2: Number + Range (Recommended)**
```csv
Number,Range
+1234567890,US-Mobile
+447911123456,UK-Mobile
+966501234567,SA-Riyadh
```

## 🚀 **How to Upload CSV Files**

### **Step 1: Prepare Your CSV File**
1. Create a CSV file with the required format
2. Ensure the `Number` column exists
3. Include country codes for better detection
4. Save as `.csv` format

### **Step 2: Upload via Telegram**
1. Open your Telegram bot chat
2. Simply drag and drop the CSV file OR click the attachment button
3. Select your CSV file
4. Send the file to the bot

### **Step 3: Automatic Processing**
1. Bot validates the file format
2. Processes each number in the CSV
3. Detects country codes automatically
4. Asks for a country/category name
5. Stores all numbers in the database

## 🔄 **Upload Workflow**

```
Admin sends CSV file
        ↓
Bot validates file format
        ↓
Bot processes numbers
        ↓
Bot asks for country name
        ↓
Admin provides country name
        ↓
Bot stores numbers in database
        ↓
Bot sends confirmation report
```

## 📱 **Available Commands**

### **Direct CSV Upload:**
- Simply send a CSV file to the bot
- Bot will guide you through the process

### **Combined Upload:**
- `/add` - Allows manual numbers + CSV file upload
- Combines both manual entry and CSV data

### **Processing Commands:**
- Upload happens automatically upon file reception
- No additional commands needed

## 🎯 **Features**

### **Automatic Processing:**
- ✅ **Country Detection** - Automatically detects country from phone numbers
- ✅ **Number Cleaning** - Removes invalid characters and formats numbers
- ✅ **Duplicate Handling** - Prevents duplicate numbers in database
- ✅ **Error Handling** - Skips invalid numbers and continues processing

### **Database Integration:**
- ✅ **MongoDB Storage** - All numbers stored in MongoDB database
- ✅ **Metadata Tracking** - Tracks source (CSV vs manual), timestamps
- ✅ **Country Categorization** - Numbers categorized by detected country
- ✅ **Admin Tracking** - Records which admin uploaded the data

### **Reporting:**
- ✅ **Upload Reports** - Detailed reports after each upload
- ✅ **Success/Failure Counts** - Shows how many numbers were processed
- ✅ **CSV Export** - Can export processed data back to CSV
- ✅ **Error Logs** - Detailed error messages for failed uploads

## 📊 **Sample CSV Files**

Three example CSV files are included in your project:

### **1. `minimal_numbers.csv`**
- Basic format with just phone numbers
- 5 sample numbers from different countries
- Perfect for testing

### **2. `example_numbers.csv`**
- Includes Number and Range columns
- 25 sample numbers with country information
- Shows proper formatting

### **3. `bulk_numbers_sample.csv`**
- Larger dataset for bulk testing
- 36 numbers across multiple countries
- Demonstrates bulk upload capabilities

## 🔍 **Supported Countries**

Your bot supports **190+ countries** with automatic detection:

**Popular Countries:**
- 🇺🇸 USA (+1)
- 🇬🇧 UK (+44)
- 🇸🇦 Saudi Arabia (+966)
- 🇦🇪 UAE (+971)
- 🇪🇬 Egypt (+20)
- 🇮🇳 India (+91)
- 🇨🇳 China (+86)
- 🇯🇵 Japan (+81)
- 🇰🇷 South Korea (+82)
- 🇩🇪 Germany (+49)
- 🇫🇷 France (+33)
- And many more...

## ⚠️ **Important Notes**

### **File Requirements:**
- ✅ File must be `.csv` format
- ✅ Must contain `Number` column header
- ✅ Numbers should include country codes for best results
- ✅ Maximum file size: Follow Telegram limits (~20MB)

### **Number Format:**
- ✅ **With Country Code**: `+1234567890` (recommended)
- ✅ **Without Plus**: `1234567890`
- ✅ **With Spaces**: `+1 234 567 890`
- ✅ **With Dashes**: `+1-234-567-890`

### **Processing Notes:**
- ⚠️ Invalid numbers are skipped (not stored)
- ⚠️ Duplicate numbers are prevented
- ⚠️ Numbers without detectable country codes may be rejected
- ⚠️ Processing is sequential (larger files take longer)

## 🛠️ **Troubleshooting**

### **CSV File Not Accepted:**
- ✅ Check file extension is `.csv`
- ✅ Ensure you're an admin user
- ✅ Verify file is not corrupted

### **Numbers Not Processing:**
- ✅ Check `Number` column exists
- ✅ Verify numbers have country codes
- ✅ Remove any non-numeric characters (except +, -, spaces)

### **Upload Failed:**
- ✅ Check file size (under Telegram limits)
- ✅ Verify CSV format is correct
- ✅ Check bot logs for detailed errors

## 📈 **Best Practices**

### **File Preparation:**
1. **Include Country Codes** - Always use `+countrycode` format
2. **Clean Data** - Remove invalid/test numbers before upload
3. **Use Range Column** - Helps categorize and track numbers
4. **Test Small First** - Upload a small file first to test format

### **Upload Strategy:**
1. **Batch Upload** - Split large files into smaller batches
2. **Verify Results** - Check upload reports after each file
3. **Monitor Database** - Use `/stats` command to verify storage
4. **Backup Data** - Keep original CSV files as backup

## 🎉 **Success Indicators**

After a successful upload, you'll see:
- ✅ **Confirmation message** with upload statistics
- ✅ **Number counts** (processed, successful, failed)
- ✅ **CSV report file** with detailed results
- ✅ **Database update** reflected in `/stats` command

---

## 🚀 **Quick Start Example**

1. **Create a test CSV file:**
```csv
Number,Range
+1234567890,US-Test
+447911123456,UK-Test
+966501234567,SA-Test
```

2. **Send to bot** via Telegram

3. **Enter country name** when prompted (e.g., "Test Upload")

4. **Receive confirmation** with upload report

**Your CSV upload system is ready to handle bulk number imports efficiently! 📊**