#!/usr/bin/env python3
"""
Test script for auto-reply functionality
"""

import asyncio
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_auto_reply_status():
    """Test auto-reply status endpoint"""
    try:
        response = requests.get(
            "https://ai-concierge.niox.ovh/auto-reply/status",
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Auto-reply Status:")
            print(f"   Enabled: {data['enabled']}")
            print(f"   Working Hours: {data['working_hours_start']} - {data['working_hours_end']}")
            print(f"   Weekend Enabled: {data['weekend_enabled']}")
            print(f"   Is Working Hours: {data['is_working_hours']}")
            print(f"   Custom Replies: {data['custom_replies_count']}")
            return True
        else:
            print(f"❌ Error getting status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing auto-reply status: {e}")
        return False

async def test_auto_reply_toggle():
    """Test auto-reply toggle endpoint"""
    try:
        # Test enabling
        response = requests.post(
            "https://ai-concierge.niox.ovh/auto-reply/toggle",
            json={"enabled": True},
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Auto-reply enabled: {data['enabled']}")
        else:
            print(f"❌ Error enabling auto-reply: {response.status_code}")
            return False

        # Test disabling
        response = requests.post(
            "https://ai-concierge.niox.ovh/auto-reply/toggle",
            json={"enabled": False},
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Auto-reply disabled: {data['enabled']}")
        else:
            print(f"❌ Error disabling auto-reply: {response.status_code}")
            return False

        # Re-enable for normal operation
        response = requests.post(
            "https://ai-concierge.niox.ovh/auto-reply/toggle",
            json={"enabled": True},
            verify=False
        )
        if response.status_code == 200:
            print("✅ Auto-reply re-enabled")
            return True

    except Exception as e:
        print(f"❌ Error testing auto-reply toggle: {e}")
        return False

async def test_auto_reply_test():
    """Test auto-reply test message"""
    try:
        response = requests.post(
            "https://ai-concierge.niox.ovh/auto-reply/test",
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Test message sent: {data['message']}")
            return True
        else:
            print(f"❌ Error sending test message: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing auto-reply test: {e}")
        return False

async def test_custom_replies():
    """Test custom replies endpoint"""
    try:
        custom_replies = {
            r"test|testing": "🧪 Ceci est une réponse de test!",
            r"info|information": "ℹ️ Voici les informations que vous demandiez.",
            r"merci": "🙏 De rien! Nous sommes là pour vous aider."
        }

        response = requests.post(
            "https://ai-concierge.niox.ovh/auto-reply/custom-replies",
            json=custom_replies,
            verify=False
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Custom replies updated: {data['message']}")
            return True
        else:
            print(f"❌ Error updating custom replies: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing custom replies: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing Auto-Reply Functionality")
    print("=" * 50)

    tests = [
        ("Auto-reply Status", test_auto_reply_status),
        ("Auto-reply Toggle", test_auto_reply_toggle),
        ("Auto-reply Test", test_auto_reply_test),
        ("Custom Replies", test_custom_replies)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\n🎯 Passed: {passed}/{len(results)} tests")

    if passed == len(results):
        print("🎉 All tests passed! Auto-reply functionality is working.")
    else:
        print("⚠️  Some tests failed. Check the logs above.")

if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    asyncio.run(main())