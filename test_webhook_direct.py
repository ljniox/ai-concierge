#!/usr/bin/env python3
"""
Direct Webhook Test and Monitor

Tests the webhook endpoint directly and creates a simple monitoring solution.
This bypasses the tunnel to test if the webhook logic is working correctly.
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_webhook_directly():
    """Test the webhook endpoint by simulating Telegram requests."""
    webhook_url = "http://localhost:8001/api/v1/telegram/webhook"
    secret_token = "gust-ia-webhook-secret"

    print("🔧 Testing Webhook Endpoint Directly")
    print("=" * 50)
    print(f"URL: {webhook_url}")
    print(f"Secret Token: {secret_token}")
    print("=" * 50)

    test_messages = [
        {
            "name": "Basic Start Command",
            "text": "start",
            "user_id": 123456789,
            "user_name": "Test User"
        },
        {
            "name": "Help Command",
            "text": "aide",
            "user_id": 123456789,
            "user_name": "Test User"
        },
        {
            "name": "Status Command",
            "text": "statut",
            "user_id": 123456789,
            "user_name": "Test User"
        },
        {
            "name": "Enrollment Command",
            "text": "inscrire",
            "user_id": 123456789,
            "user_name": "Test User"
        }
    ]

    async with aiohttp.ClientSession() as session:
        for i, test in enumerate(test_messages, 1):
            print(f"\n📨 Test {i}: {test['name']}")
            print(f"   Message: '{test['text']}'")

            # Create Telegram update payload
            update_data = {
                "update_id": int(datetime.now().timestamp()) + i,
                "message": {
                    "message_id": 1000 + i,
                    "from": {
                        "id": test["user_id"],
                        "first_name": test["user_name"].split()[0],
                        "last_name": " ".join(test["user_name"].split()[1:]) if len(test["user_name"].split()) > 1 else "",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": test["user_id"],
                        "type": "private"
                    },
                    "text": test["text"],
                    "date": int(datetime.now().timestamp())
                }
            }

            headers = {
                "Content-Type": "application/json",
                "X-Telegram-Bot-Api-Secret-Token": secret_token
            }

            try:
                async with session.post(
                    webhook_url,
                    json=update_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    result_data = await response.json()

                    print(f"   Status: {response.status}")
                    print(f"   Response: {json.dumps(result_data, indent=6)}")

                    if response.status == 200:
                        print("   ✅ SUCCESS - Message processed")
                    else:
                        print("   ❌ FAILED - Processing error")

            except Exception as e:
                print(f"   ❌ ERROR: {e}")

            await asyncio.sleep(1)  # Small delay between tests

    print("\n" + "=" * 50)
    print("🏁 Direct webhook testing completed")
    print("\n💡 If these tests pass, the webhook logic is working.")
    print("   The issue might be with:")
    print("   1. LocalTunnel configuration")
    print("   2. Telegram-to-tunnel connectivity")
    print("   3. Network/firewall issues")

async def check_tunnel_connectivity():
    """Check if the tunnel is properly forwarding requests."""
    tunnel_url = "https://gust-ia-enrollment.loca.lt/health"

    print("\n🌐 Testing Tunnel Connectivity")
    print("=" * 50)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(tunnel_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Tunnel to application: CONNECTED")
                    print(f"   Status: {data.get('status')}")
                    print(f"   Version: {data.get('version')}")
                else:
                    print(f"❌ Tunnel response error: {response.status}")
    except Exception as e:
        print(f"❌ Tunnel connectivity failed: {e}")

async def main():
    """Run all webhook tests."""
    print("🚀 Gust-IA Webhook Diagnostics")
    print("=" * 60)

    await test_webhook_directly()
    await check_tunnel_connectivity()

    print("\n" + "=" * 60)
    print("📊 Diagnostic Summary:")
    print("1. If direct tests pass → Webhook logic is working")
    print("2. If tunnel test passes → Network connectivity is working")
    print("3. If both pass → Issue may be Telegram-to-tunnel delivery")
    print("\n🔍 Next steps:")
    print("- Send a real message from Telegram")
    print("- Check tunnel logs: monitor the lt process")
    print("- Check application logs for incoming requests")

if __name__ == "__main__":
    asyncio.run(main())