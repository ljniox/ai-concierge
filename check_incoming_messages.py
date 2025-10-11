#!/usr/bin/env python3
"""
Check for Incoming Telegram Messages

Monitors the Gust-IA system for incoming Telegram messages through the
production proxy at https://cate.sdb-dkr.ovh
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def check_webhook_status():
    """Check current Telegram webhook status."""
    bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo") as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})

                    print("📡 Telegram Webhook Status")
                    print("=" * 40)
                    print(f"URL: {result.get('url')}")
                    print(f"Pending Updates: {result.get('pending_update_count', 0)}")
                    print(f"Last Error: {result.get('last_error_message', 'None')}")
                    print(f"Last Error Date: {result.get('last_error_date', 'None')}")
                    print(f"Max Connections: {result.get('max_connections', 'N/A')}")

                    return result
                else:
                    print(f"❌ Failed to get webhook info: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Error checking webhook: {e}")
        return None

async def check_system_health():
    """Check if the system is healthy and ready."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cate.sdb-dkr.ovh/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    print("\n🏥 System Health Status")
                    print("=" * 40)
                    print(f"Overall Status: {data.get('services', {}).get('overall', 'unknown')}")
                    print(f"Version: {data.get('version', 'unknown')}")
                    print(f"Environment: {data.get('environment', 'unknown')}")

                    services = data.get('services', {}).get('sqlite_databases', {})
                    for service, status in services.items():
                        print(f"{service}: {'✅' if status else '❌'}")

                    return data
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return None
    except Exception as e:
        print(f"❌ Error checking health: {e}")
        return None

async def test_webhook_connectivity():
    """Test if the webhook endpoint is responding."""
    test_payload = {
        "update_id": int(time.time()),
        "message": {
            "message_id": int(time.time()),
            "from": {
                "id": 123456789,
                "first_name": "Health",
                "last_name": "Check"
            },
            "chat": {
                "id": 123456789,
                "type": "private"
            },
            "text": "health_check",
            "date": int(time.time())
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Telegram-Bot-Api-Secret-Token": "gust-ia-webhook-secret"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://cate.sdb-dkr.ovh/api/v1/telegram/webhook",
                json=test_payload,
                headers=headers,
                timeout=10
            ) as response:
                result = await response.json()

                print("\n🧪 Webhook Connectivity Test")
                print("=" * 40)
                print(f"Response Status: {response.status}")
                print(f"Response: {json.dumps(result, indent=2)}")

                return response.status == 200 and result.get("status") == "success"
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

async def monitor_for_messages():
    """Monitor for incoming messages temporarily."""
    print("\n🔍 Monitoring for Incoming Messages")
    print("=" * 40)
    print("Send a message to your Telegram bot now!")
    print("Try commands like: start, aide, statut, inscrire")
    print("Monitoring for 60 seconds...")
    print("=" * 40)

    bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"
    message_count = 0

    try:
        async with aiohttp.ClientSession() as session:
            for i in range(12):  # Check for 60 seconds (12 * 5 seconds)
                # Check webhook info for pending updates
                async with session.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo") as response:
                    if response.status == 200:
                        data = await response.json()
                        result = data.get('result', {})
                        pending_count = result.get('pending_update_count', 0)

                        if pending_count > 0:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"\n📨 [{timestamp}] 🎯 MESSAGE DETECTED!")
                            print(f"   Pending updates: {pending_count}")
                            message_count += pending_count

                            # Temporarily delete webhook to get message details
                            await session.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")

                            # Get the actual messages
                            async with session.get(f"https://api.telegram.org/bot{bot_token}/getUpdates") as updates_response:
                                if updates_response.status == 200:
                                    updates_data = await updates_response.json()
                                    updates = updates_data.get('result', [])

                                    for update in updates:
                                        if 'message' in update:
                                            message = update['message']
                                            user = message.get('from', {})
                                            text = message.get('text', '')

                                            print(f"   From: {user.get('first_name', 'Unknown')} {user.get('last_name', '')}")
                                            print(f"   Text: {text}")
                                            print(f"   Time: {datetime.fromtimestamp(message.get('date', 0)).strftime('%H:%M:%S')}")
                                            print("-" * 40)

                            # Restore webhook
                            await session.post(
                                f"https://api.telegram.org/bot{bot_token}/setWebhook",
                                json={
                                    "url": "https://cate.sdb-dkr.ovh/api/v1/telegram/webhook",
                                    "secret_token": "gust-ia-webhook-secret"
                                }
                            )

                if i < 11:  # Don't show countdown on last iteration
                    remaining = 60 - (i * 5)
                    print(f"   Checking... {remaining}s remaining", end='\r')

                await asyncio.sleep(5)

            print("\n" + "=" * 40)
            if message_count > 0:
                print(f"🎉 SUCCESS: Detected {message_count} message(s)!")
            else:
                print("ℹ️  No messages received during monitoring period")
                print("   Make sure you're sending messages to the correct bot")

            return message_count > 0

    except Exception as e:
        print(f"❌ Monitoring error: {e}")
        return False

async def show_system_info():
    """Display system information for user reference."""
    print("\n📋 System Information")
    print("=" * 40)
    print("🌐 Production URL: https://cate.sdb-dkr.ovh")
    print("🤖 Telegram Webhook: https://cate.sdb-dkr.ovh/api/v1/telegram/webhook")
    print("🔧 Health Check: https://cate.sdb-dkr.ovh/health")
    print("📊 Statistics: https://cate.sdb-dkr.ovh/stats")
    print("=" * 40)
    print("Available Telegram Commands:")
    print("• start     - Begin enrollment process")
    print("• aide      - Get help information")
    print("• statut    - Check system status")
    print("• inscrire  - Start enrollment")
    print("• information - Get system information")
    print("• contact   - Request human assistance")
    print("=" * 40)

async def main():
    """Main function to check for incoming messages."""
    print("🚀 Gust-IA Incoming Message Checker")
    print("=" * 60)
    print("Checking system status and monitoring for Telegram messages...")
    print("=" * 60)

    # Show system info
    await show_system_info()

    # Check system health
    health = await check_system_health()
    if not health:
        print("❌ System health check failed - aborting")
        return

    # Check webhook status
    webhook_info = await check_webhook_status()
    if not webhook_info:
        print("❌ Webhook status check failed - aborting")
        return

    # Test webhook connectivity
    webhook_test = await test_webhook_connectivity()
    if not webhook_test:
        print("❌ Webhook connectivity test failed - aborting")
        return

    # Monitor for messages
    messages_detected = await monitor_for_messages()

    print("\n📊 FINAL RESULTS")
    print("=" * 60)
    print(f"System Health: {'✅ OK' if health else '❌ FAILED'}")
    print(f"Webhook Status: {'✅ OK' if webhook_info else '❌ FAILED'}")
    print(f"Connectivity Test: {'✅ OK' if webhook_test else '❌ FAILED'}")
    print(f"Messages Detected: {'✅ YES' if messages_detected else '❌ NO'}")

    if messages_detected:
        print("\n🎉 SUCCESS: Telegram integration is working!")
        print("   Messages are being received through the production proxy.")
    else:
        print("\n💡 TIPS:")
        print("   • Ensure you're sending messages to the correct Telegram bot")
        print("   • Check if the bot token is correct")
        print("   • Verify the bot is running and accessible")
        print("   • Try sending a simple message like 'start'")

    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())