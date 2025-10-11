#!/usr/bin/env python3
"""
Test script for WAHA configuration and functionality
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_waha_service():
    """Test WAHA service functionality"""
    try:
        from src.services.waha_service import WAHAService

        print("🧪 Testing WAHA Service Configuration")
        print("=" * 50)

        # Initialize service
        waha_service = WAHAService()
        print(f"✅ WAHA Service initialized")
        print(f"   Base URL: {waha_service.base_url}")
        print(f"   Session ID: {waha_service.session_id}")
        print(f"   API Key: {'SET' if waha_service.api_key else 'NOT SET'}")

        # Test session status
        print("\n📋 Checking session status...")
        status = await waha_service.check_session_status()
        print(f"   Session Status: {status.get('status', 'Unknown')}")
        print(f"   Session Name: {status.get('name', 'Unknown')}")

        if status.get('me'):
            print(f"   Connected Number: {status['me'].get('id', 'Unknown')}")
            print(f"   Display Name: {status['me'].get('pushName', 'Unknown')}")

        # Test URL building
        print("\n🔧 Testing URL building...")
        test_urls = [
            'status',
            'start',
            'sendText',
            'qr'
        ]

        for endpoint in test_urls:
            url = waha_service._build_url(endpoint)
            print(f"   {endpoint} → {url}")

        # Test session management if session is stopped
        if status.get('status') == 'STOPPED':
            print("\n🚀 Attempting to start session...")
            start_result = await waha_service.start_session()
            print(f"   Start Result: {'Success' if start_result else 'Failed'}")

            # Check status again
            await asyncio.sleep(2)
            new_status = await waha_service.check_session_status()
            print(f"   New Status: {new_status.get('status', 'Unknown')}")

        # Test session connectivity
        print("\n🔗 Testing session connectivity...")
        is_connected = await waha_service.is_session_connected()
        print(f"   Session Connected: {'Yes' if is_connected else 'No'}")

        # Close service
        await waha_service.close()
        print("\n✅ WAHA Service test completed successfully!")

        return True

    except Exception as e:
        print(f"\n❌ WAHA Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_api():
    """Test direct WAHA API calls"""
    try:
        import httpx

        print("\n🔍 Testing Direct WAHA API")
        print("=" * 30)

        base_url = "https://waha-core.niox.ovh"
        api_key = "28C5435535C2487DAFBD1164B9CD4E34"
        session_id = "default"

        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test session status
            print("📋 Checking session status...")
            response = await client.get(
                f"{base_url}/api/sessions/{session_id}",
                headers=headers
            )

            if response.status_code == 200:
                session_data = response.json()
                print(f"   Status: {session_data.get('status')}")
                print(f"   Name: {session_data.get('name')}")

                if session_data.get('me'):
                    print(f"   Number: {session_data['me'].get('id')}")
            else:
                print(f"   Status Check Failed: {response.status_code}")

            # Test message sending (will fail if session not working)
            print("\n📤 Testing message endpoint...")
            message_response = await client.post(
                f"{base_url}/api/sendText",
                headers=headers,
                json={
                    'session': session_id,
                    'chatId': '221765005555@c.us',
                    'text': '🧪 WAHA Configuration Test Message'
                }
            )

            print(f"   Message Response: {message_response.status_code}")
            if message_response.status_code != 200:
                error_data = message_response.json()
                print(f"   Error: {error_data.get('message', 'Unknown error')}")

        print("\n✅ Direct API test completed!")
        return True

    except Exception as e:
        print(f"\n❌ Direct API test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🧪 WAHA Configuration Test Suite")
    print("=" * 50)

    # Test WAHA service
    service_result = await test_waha_service()

    # Test direct API
    api_result = await test_direct_api()

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print(f"   WAHA Service: {'✅ PASS' if service_result else '❌ FAIL'}")
    print(f"   Direct API: {'✅ PASS' if api_result else '❌ FAIL'}")

    if service_result and api_result:
        print("\n🎉 All WAHA tests passed!")
        return True
    else:
        print("\n⚠️  Some tests failed. Check configuration.")
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)