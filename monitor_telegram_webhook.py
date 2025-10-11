#!/usr/bin/env python3
"""
Real-time Telegram Webhook Monitor

Monitors incoming Telegram messages and system responses in real-time.
Shows when messages are received and how they are processed.

Usage:
python3 monitor_telegram_webhook.py
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

async def monitor_webhook_info():
    """Monitor Telegram webhook info for pending updates."""
    bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

    print("🔍 Gust-IA Telegram Webhook Monitor")
    print("=" * 50)
    print("Monitoring for incoming Telegram messages...")
    print("Webhook URL: https://gust-ia-enrollment.loca.lt/api/v1/telegram/webhook")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        message_count = 0

        try:
            while True:
                try:
                    # Check webhook info
                    async with session.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo") as response:
                        if response.status == 200:
                            webhook_data = await response.json()
                            pending_count = webhook_data.get('result', {}).get('pending_update_count', 0)

                            if pending_count > 0:
                                timestamp = datetime.now().strftime("%H:%M:%S")
                                print(f"\n📨 [{timestamp}] New message detected! Pending updates: {pending_count}")

                                # Try to get the updates
                                async with session.get(f"https://api.telegram.org/bot{bot_token}/getUpdates") as updates_response:
                                    if updates_response.status == 200:
                                        updates_data = await updates_response.json()
                                        updates = updates_data.get('result', [])

                                        for update in updates:
                                            message_count += 1
                                            timestamp = datetime.now().strftime("%H:%M:%S")

                                            if 'message' in update:
                                                message = update['message']
                                                user = message.get('from', {})
                                                chat = message.get('chat', {})
                                                text = message.get('text', '')

                                                print(f"📩 Message #{message_count} [{timestamp}]")
                                                print(f"   From: {user.get('first_name', 'Unknown')} {user.get('last_name', '')}")
                                                print(f"   Chat ID: {chat.get('id', 'Unknown')}")
                                                print(f"   Text: {text}")
                                                print(f"   Update ID: {update.get('update_id')}")
                                                print("-" * 40)
                                            elif 'callback_query' in update:
                                                callback = update['callback_query']
                                                user = callback.get('from', {})
                                                data = callback.get('data', '')

                                                print(f"🔄 Callback Query #{message_count} [{timestamp}]")
                                                print(f"   From: {user.get('first_name', 'Unknown')} {user.get('last_name', '')}")
                                                print(f"   Data: {data}")
                                                print("-" * 40)

                    await asyncio.sleep(3)  # Check every 3 seconds

                except Exception as e:
                    print(f"❌ Error checking webhook: {e}")
                    await asyncio.sleep(5)

        except KeyboardInterrupt:
            print(f"\n\n📊 Monitoring stopped. Total messages detected: {message_count}")
            print("\n💡 If you sent messages but they weren't detected:")
            print("   1. Check if the tunnel is running: ps aux | grep lt")
            print("   2. Check if the app is running: ps aux | grep uvicorn")
            print("   3. Verify webhook is configured correctly")
            print("   4. Check application logs for errors")

async def check_application_health():
    """Check if the Gust-IA application is responding."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8001/health", timeout=5) as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ Gust-IA Application Status: HEALTHY")
                    print(f"   Services: {health_data.get('services', {}).get('overall', 'unknown')}")
                    print(f"   Version: {health_data.get('version', 'unknown')}")
                else:
                    print(f"❌ Application health check failed: {response.status}")
    except Exception as e:
        print(f"❌ Cannot connect to application: {e}")
        print("   Make sure the application is running on port 8001")

async def main():
    """Main monitor function."""
    await check_application_health()
    print()
    await monitor_webhook_info()

if __name__ == "__main__":
    asyncio.run(main())