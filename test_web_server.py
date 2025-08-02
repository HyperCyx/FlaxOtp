#!/usr/bin/env python3
"""
Test script for the web server
Run this to test the web server locally before deployment
"""

import asyncio
import aiohttp
import time
import sys

async def test_web_server():
    """Test the web server endpoints"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing web server endpoints...")
    
    async with aiohttp.ClientSession() as session:
        # Test root endpoint
        try:
            async with session.get(f"{base_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Root endpoint: {data}")
                else:
                    print(f"❌ Root endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ Root endpoint error: {e}")
        
        # Test health endpoint
        try:
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health endpoint: {data}")
                else:
                    print(f"❌ Health endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ Health endpoint error: {e}")
        
        # Test status endpoint
        try:
            async with session.get(f"{base_url}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Status endpoint: {data}")
                else:
                    print(f"❌ Status endpoint failed: {response.status}")
        except Exception as e:
            print(f"❌ Status endpoint error: {e}")

def main():
    """Main function"""
    print("🚀 Starting web server test...")
    
    # Wait a bit for the server to start
    print("⏳ Waiting 5 seconds for server to start...")
    time.sleep(5)
    
    # Run the test
    asyncio.run(test_web_server())
    
    print("✅ Test completed!")

if __name__ == "__main__":
    main()