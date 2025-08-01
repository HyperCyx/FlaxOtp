import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# SMS API Configuration
SMS_API_BASE_URL = "http://51.83.103.80"
SMS_API_ENDPOINT = "/ints/agent/res/data_smscdr.php"
SMS_API_COOKIE = "PHPSESSID=dn1es46hla171cs6vunle9tq5v"
TIMEZONE = pytz.timezone('Asia/Riyadh')

async def test_sms_api(phone_number):
    """Test SMS API directly for a specific number"""
    print(f"🔍 Testing SMS API for number: {phone_number}")
    
    # Build the API URL with parameters - optimized for live monitoring
    now = datetime.now(TIMEZONE)
    yesterday = now - timedelta(hours=24)
    date_str = yesterday.strftime("%Y-%m-%d")
    
    params = {
        'fdate1': f"{date_str} 00:00:00",
        'fdate2': f"{now.strftime('%Y-%m-%d %H:%M:%S')}",  # Current time
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
        'iDisplayLength': '50',  # Get more messages
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
            print(f"🌐 Making API request to: {url}")
            print(f"📅 Date range: {params['fdate1']} to {params['fdate2']}")
            print(f"📱 Phone number: {phone_number}")
            
            async with session.get(url, params=params, headers=headers) as response:
                print(f"📊 API response status: {response.status}")
                
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    print(f"📄 Content-Type: {content_type}")
                    
                    if 'application/json' in content_type or 'text/html' in content_type:
                        try:
                            data = await response.json()
                            print(f"✅ JSON response received")
                            print(f"📊 Response keys: {list(data.keys())}")
                            
                            if 'aaData' in data:
                                messages = data['aaData']
                                print(f"📨 Total messages in response: {len(messages)}")
                                
                                # Filter and display messages
                                valid_messages = []
                                for i, row in enumerate(messages):
                                    if isinstance(row, list) and len(row) >= 6:
                                        first_item = str(row[0])
                                        if not first_item.startswith('0.') and not ',' in first_item and len(first_item) > 10:
                                            message_data = {
                                                'datetime': row[0],
                                                'range': row[1],
                                                'number': row[2],
                                                'sender': row[3] if len(row) > 3 else 'Unknown',
                                                'message': row[5] if len(row) > 5 else 'No message content'
                                            }
                                            valid_messages.append(message_data)
                                            print(f"📱 Message {i+1}: {message_data}")
                                
                                print(f"\n🎯 Found {len(valid_messages)} valid messages for {phone_number}")
                                
                                if valid_messages:
                                    latest = valid_messages[0]
                                    print(f"\n📞 Latest message:")
                                    print(f"   🕐 Time: {latest['datetime']}")
                                    print(f"   👤 Sender: {latest['sender']}")
                                    print(f"   💬 Message: {latest['message']}")
                                    
                                    # Test OTP extraction
                                    import re
                                    message_lower = latest['message'].lower()
                                    patterns = [
                                        r'\b(\d{4,6})\b',  # 4-6 digit OTP
                                        r'code[:\s]*(\d{4,6})',  # "code: 123456"
                                        r'verification[:\s]*(\d{4,6})',  # "verification: 123456"
                                        r'OTP[:\s]*(\d{4,6})',  # "OTP: 123456"
                                        r'password[:\s]*(\d{4,6})',  # "password: 123456"
                                        r'pin[:\s]*(\d{4,6})',  # "pin: 123456"
                                        r'passcode[:\s]*(\d{4,6})',  # "passcode: 123456"
                                        r'(\d{4,6})[^\d]*$',  # OTP at end of message
                                        r'(\d{4,6})\s+is\s+your',  # "123456 is your"
                                        r'your\s+(\d{4,6})',  # "your 123456"
                                    ]
                                    
                                    for pattern in patterns:
                                        match = re.search(pattern, message_lower)
                                        if match:
                                            otp = match.group(1)
                                            if len(otp) >= 4 and len(otp) <= 6 and otp.isdigit():
                                                print(f"🎯 OTP DETECTED: {otp} (pattern: {pattern})")
                                                break
                                    else:
                                        print(f"❌ No OTP found in message")
                                else:
                                    print(f"❌ No valid messages found for {phone_number}")
                            else:
                                print(f"❌ No 'aaData' in response")
                                print(f"📄 Full response: {data}")
                                
                        except Exception as json_error:
                            print(f"❌ JSON parsing failed: {json_error}")
                            response_text = await response.text()
                            print(f"📄 Response text (first 500 chars): {response_text[:500]}...")
                    else:
                        response_text = await response.text()
                        print(f"❌ Unexpected content type: {content_type}")
                        print(f"📄 Response text (first 500 chars): {response_text[:500]}...")
                else:
                    response_text = await response.text()
                    print(f"❌ SMS API error: {response.status}")
                    print(f"📄 Response: {response_text}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    phone_number = "923297589678"
    await test_sms_api(phone_number)

if __name__ == "__main__":
    asyncio.run(main())