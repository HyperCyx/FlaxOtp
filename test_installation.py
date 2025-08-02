#!/usr/bin/env python3
"""
Telegram SMS Bot Installation Test Script
Run this script to verify your installation is correct.
"""

import sys
import os
import importlib
from datetime import datetime

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python Version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = [
        ('telegram', 'python-telegram-bot'),
        ('motor', 'motor'),
        ('aiohttp', 'aiohttp'),
        ('pytz', 'pytz'),
        ('pycountry', 'pycountry'),
        ('pymongo', 'pymongo'),
        ('asyncio', 'asyncio (built-in)'),
        ('json', 'json (built-in)'),
        ('re', 're (built-in)'),
        ('csv', 'csv (built-in)'),
        ('os', 'os (built-in)'),
        ('logging', 'logging (built-in)'),
        ('datetime', 'datetime (built-in)'),
    ]
    
    success_count = 0
    for module, package in dependencies:
        try:
            importlib.import_module(module)
            print(f"✅ {package}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {package} - {e}")
    
    print(f"\n📊 Dependencies: {success_count}/{len(dependencies)} successful")
    return success_count == len(dependencies)

def test_config_file():
    """Test configuration file"""
    print("\n⚙️ Testing Configuration...")
    
    try:
        import config
        
        # Required config variables
        required_vars = [
            'TOKEN', 'CHANNEL_ID', 'CHANNEL_LINK',
            'MONGO_URI', 'DB_NAME', 'COLLECTION_NAME',
            'COUNTRIES_COLLECTION', 'USERS_COLLECTION',
            'ADMIN_IDS', 'SMS_API_BASE_URL', 'SMS_API_ENDPOINT',
            'SMS_API_COOKIE', 'TIMEZONE_NAME', 'LOGGING_LEVEL',
            'USER_CACHE_DIR'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not hasattr(config, var):
                missing_vars.append(var)
            else:
                value = getattr(config, var)
                if var == 'TOKEN':
                    print(f"✅ {var}: {str(value)[:10]}..." if value else f"❌ {var}: Empty")
                elif var == 'ADMIN_IDS':
                    print(f"✅ {var}: {len(value)} admin(s)" if value else f"❌ {var}: Empty")
                elif var in ['SMS_API_COOKIE']:
                    print(f"✅ {var}: {str(value)[:20]}..." if value else f"❌ {var}: Empty")
                else:
                    print(f"✅ {var}: {value}")
        
        if missing_vars:
            print(f"❌ Missing config variables: {', '.join(missing_vars)}")
            return False
        else:
            print("✅ All required config variables present")
            return True
            
    except ImportError:
        print("❌ config.py file not found or has syntax errors")
        return False
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_directories():
    """Test required directories"""
    print("\n📁 Testing Directories...")
    
    directories = [
        'user_cache',
    ]
    
    success = True
    for directory in directories:
        if os.path.exists(directory):
            print(f"✅ {directory}/ exists")
        else:
            print(f"❌ {directory}/ missing - creating...")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"✅ {directory}/ created")
            except Exception as e:
                print(f"❌ Failed to create {directory}/: {e}")
                success = False
    
    return success

def test_bot_import():
    """Test bot.py import"""
    print("\n🤖 Testing Bot Import...")
    
    try:
        # Try importing bot functions
        from bot import (
            reload_config_session,
            get_current_sms_cookie,
            extract_otp_from_message,
            format_number_display
        )
        print("✅ Core bot functions imported successfully")
        
        # Test a simple function
        test_number = "1234567890"
        formatted = format_number_display(test_number)
        print(f"✅ Number formatting test: {test_number} -> {formatted}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Bot import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Bot test error: {e}")
        return False

def test_version_info():
    """Display version information"""
    print("\n📋 Version Information:")
    
    try:
        import telegram
        print(f"📱 python-telegram-bot: {telegram.__version__}")
    except:
        print("❌ python-telegram-bot version unavailable")
    
    try:
        import motor
        print(f"🗄️ motor: {motor.version}")
    except:
        print("❌ motor version unavailable")
    
    try:
        import aiohttp
        print(f"🌐 aiohttp: {aiohttp.__version__}")
    except:
        print("❌ aiohttp version unavailable")
    
    try:
        import pytz
        print(f"🌍 pytz: {pytz.__version__}")
    except:
        print("❌ pytz version unavailable")
    
    try:
        import pycountry
        print(f"🏳️ pycountry: {pycountry.__version__}")
    except:
        print("❌ pycountry version unavailable")

def main():
    """Run all tests"""
    print("🔍 Telegram SMS Bot Installation Test")
    print("=" * 50)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Python Executable: {sys.executable}")
    print(f"📂 Working Directory: {os.getcwd()}")
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Configuration", test_config_file),
        ("Directories", test_directories),
        ("Bot Import", test_bot_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Display version info
    test_version_info()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED! Your installation is ready.")
        print("🚀 You can now run: python3 bot.py")
        return True
    else:
        print(f"\n⚠️ {len(results) - passed} test(s) failed. Please fix the issues above.")
        print("📖 Check INSTALLATION.md for detailed setup instructions.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)