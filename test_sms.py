#!/usr/bin/env python3

import asyncio
import aiohttp
import json
from datetime import datetime

# SMS API Configuration
SMS_API_BASE_URL = "http://54.37.252.85"
SMS_API_ENDPOINT = "/ints/agent/res/data_smscdr.php"
SMS_API_COOKIE = "PHPSESSID=pq0oq4ckbcjnm7dbp6rna1dfdo"

async def test_sms_api():
    """Test the SMS API directly"""
    phone_number = "94741854027"
    date_str = "2025-08-01"
    
    print(f"Testing SMS API for number: {phone_number}")
    
    # Build the API URL with parameters
    params = {
        'fdate1': f"{date_str} 00:00:00",
        'fdate2': f"{date_str} 23:59:59",
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
        'iDisplayLength': '25',
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
            print(f"Making API request to: {url}")
            print(f"With params: {params}")
            
            async with session.get(url, params=params, headers=headers) as response:
                print(f"API response status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"API response data: {json.dumps(data, indent=2)}")
                    
                    # Process the data
                    if data and 'aaData' in data and data['aaData']:
                        print(f"\nFound {len(data['aaData'])} rows in response")
                        
                        # Filter out summary rows and get actual SMS messages
                        sms_messages = []
                        for i, row in enumerate(data['aaData']):
                            print(f"Row {i}: {row}")
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
                        
                        print(f"\nFound {len(sms_messages)} valid SMS messages:")
                        for i, sms in enumerate(sms_messages):
                            print(f"\nMessage {i+1}:")
                            print(f"  Time: {sms['datetime']}")
                            print(f"  Number: {sms['number']}")
                            print(f"  Sender: {sms['sender']}")
                            print(f"  Message: {sms['message']}")
                    else:
                        print("No data found in response")
                else:
                    response_text = await response.text()
                    print(f"SMS API error: {response.status}, Response: {response_text}")
    except Exception as e:
        print(f"Error testing SMS API: {e}")

if __name__ == "__main__":
    asyncio.run(test_sms_api())