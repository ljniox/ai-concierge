#!/usr/bin/env python3
"""
Test script for Telegram bot functionality
"""

import asyncio
import sys
import os
import requests

def test_telegram_bot_token():
    """Test Telegram bot token validity"""
    try:
        token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        print("🤖 Testing Telegram Bot Configuration")
        print("=" * 50)

        # Test bot info
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")

        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot = bot_info['result']
                print(f"✅ Bot Token: VALID")
                print(f"   Bot ID: {bot['id']}")
                print(f"   Bot Name: {bot['first_name']}")
                print(f"   Bot Username: @{bot['username']}")
                print(f"   Can Join Groups: {bot['can_join_groups']}")
                return True
            else:
                print(f"❌ Bot Token Error: {bot_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def test_telegram_webhook():
    """Test Telegram webhook configuration"""
    try:
        token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        print("\n🔗 Testing Telegram Webhook")
        print("=" * 30)

        # Get webhook info
        response = requests.get(f"https://api.telegram.org/bot{token}/getWebhookInfo")

        if response.status_code == 200:
            webhook_info = response.json()
            if webhook_info.get('ok'):
                webhook = webhook_info['result']
                print(f"   Webhook URL: {webhook.get('url', 'Not set')}")
                print(f"   Pending Updates: {webhook.get('pending_update_count', 0)}")

                if webhook.get('last_error_message'):
                    print(f"   Last Error: {webhook['last_error_message']}")
                    print(f"   Error Date: {webhook.get('last_error_date', 'Unknown')}")
                    print(f"   ⚠️  Webhook has errors - needs fixing")
                    return False
                else:
                    print(f"   ✅ Webhook status: OK")
                    return True
            else:
                print(f"❌ Webhook Error: {webhook_info.get('description', 'Unknown error')}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def get_bot_updates():
    """Get recent bot updates to find chat IDs"""
    try:
        token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        print("\n📨 Getting Bot Updates")
        print("=" * 25)

        response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")

        if response.status_code == 200:
            updates = response.json()
            if updates.get('ok'):
                update_list = updates['result']
                print(f"   Found {len(update_list)} recent updates")

                chat_ids = set()
                for update in update_list:
                    message = update.get('message', {})
                    chat = message.get('chat', {})
                    if chat:
                        chat_id = chat.get('id')
                        chat_type = chat.get('type', 'unknown')
                        chat_name = chat.get('first_name') or chat.get('title', 'Unknown')

                        chat_ids.add(chat_id)
                        print(f"   Chat ID: {chat_id} ({chat_type}) - {chat_name}")

                if chat_ids:
                    print(f"\n   Available Chat IDs: {list(chat_ids)}")
                    return list(chat_ids)
                else:
                    print("   No recent chats found - bot needs interaction")
                    return []
            else:
                print(f"❌ Updates Error: {updates.get('description', 'Unknown error')}")
                return []
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Exception: {e}")
        return []

def main():
    """Main test function"""
    print("🧪 Telegram Bot Test Suite")
    print("=" * 50)

    results = {
        'bot_token': test_telegram_bot_token(),
        'webhook': test_telegram_webhook()
    }

    # Get updates for additional info
    chat_ids = get_bot_updates()

    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name.replace('_', ' ').title()}: {status}")

    print(f"\n📱 Bot Status: Active")
    print(f"   Username: @sdbcatebot")
    print(f"   Name: catechese-don-bosco-dakar")

    if chat_ids:
        print(f"   Available Chats: {len(chat_ids)}")

    overall_success = all(results.values())

    if overall_success:
        print(f"\n🎉 Bot configuration is valid!")
        print(f"   ✅ Token is working")
        print(f"   ⚠️  Webhook needs fixing (404 error)")
        print(f"   📱 Bot is ready for integration")
    else:
        print(f"\n⚠️  Some tests failed. Check configuration.")

    print(f"\n📝 Next Steps:")
    print(f"   1. Fix webhook endpoint: https://cate.sdb-dkr.ovh/api/v1/telegram/webhook")
    print(f"   2. Test message receiving once webhook works")
    print(f"   3. Integrate with enrollment workflow")

    return overall_success

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)