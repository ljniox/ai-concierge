#!/usr/bin/env python3
"""
Check Current Incoming Messages

Monitors the Gust-IA system for new incoming Telegram messages
through the production proxy.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

async def check_telegram_messages():
    """Check for new incoming Telegram messages."""
    print("🔍 Checking for Incoming Telegram Messages")
    print("=" * 60)
    print(f"Service: Service de la catéchèse de Saint Jean Bosco de Nord Foire")
    print(f"Webhook: https://cate.sdb-dkr.ovh/api/v1/telegram/webhook")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

    try:
        async with aiohttp.ClientSession() as session:
            # Get current webhook status
            print("\n📡 Webhook Status:")
            async with session.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo") as response:
                if response.status == 200:
                    webhook_data = await response.json()
                    result = webhook_data.get('result', {})

                    print(f"   URL: {result.get('url')}")
                    print(f"   Pending Updates: {result.get('pending_update_count', 0)}")
                    print(f"   Last Error: {result.get('last_error_message', 'None')}")

                    # Check if there are pending messages
                    pending_count = result.get('pending_update_count', 0)

                    if pending_count > 0:
                        print(f"\n🎯 FOUND {pending_count} PENDING MESSAGES!")

                        # Temporarily delete webhook to get messages
                        await session.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")

                        # Get the messages
                        async with session.get(f"https://api.telegram.org/bot{bot_token}/getUpdates?limit=10") as updates_response:
                            if updates_response.status == 200:
                                updates_data = await updates_response.json()
                                updates = updates_data.get('result', [])

                                print(f"\n📨 Recent Messages ({len(updates)}):")
                                print("-" * 60)

                                for update in updates:
                                    if 'message' in update:
                                        message = update['message']
                                        user = message.get('from', {})
                                        text = message.get('text', '')
                                        msg_date = datetime.fromtimestamp(message.get('date', 0))

                                        print(f"🕐 Time: {msg_date.strftime('%H:%M:%S')}")
                                        print(f"👤 From: {user.get('first_name', 'Unknown')} {user.get('last_name', '')}")
                                        print(f"💬 Text: {text}")
                                        print(f"🆔 User ID: {user.get('id')}")
                                        print(f"📋 Message ID: {message.get('message_id')}")
                                        print("-" * 40)

                        # Restore webhook
                        await session.post(
                            f"https://api.telegram.org/bot{bot_token}/setWebhook",
                            json={
                                "url": "https://cate.sdb-dkr.ovh/api/v1/telegram/webhook",
                                "secret_token": "gust-ia-webhook-secret"
                            }
                        )

                        print(f"\n✅ Webhook restored")

                    else:
                        print(f"\nℹ️  No pending messages found")

                        # Check system health
                        print(f"\n🏥 System Health Check:")
                        async with session.get("https://cate.sdb-dkr.ovh/health") as health_response:
                            if health_response.status == 200:
                                health_data = await health_response.json()
                                print(f"   Status: {health_data.get('services', {}).get('overall', 'unknown')}")
                                print(f"   Version: {health_data.get('version', 'unknown')}")
                            else:
                                print(f"   Status: Error ({health_response.status})")

                        print(f"\n💡 To test the system:")
                        print(f"   1. Send a message to your Telegram bot")
                        print(f"   2. Try commands: start, aide, statut, inscrire")
                        print(f"   3. The system will respond automatically")

                else:
                    print(f"❌ Failed to get webhook info: {response.status}")
                    return False

    except Exception as e:
        print(f"❌ Error checking messages: {e}")
        return False

    return True

async def main():
    """Main function."""
    await check_telegram_messages()

if __name__ == "__main__":
    asyncio.run(main())