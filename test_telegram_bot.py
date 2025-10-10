"""
Test script for Telegram bot integration
"""

import asyncio
import os
from dotenv import load_dotenv
from src.services.telegram_service import TelegramService
import structlog

logger = structlog.get_logger()

# Load environment variables
load_dotenv()


async def test_bot_info():
    """Test getting bot information"""
    print("=" * 60)
    print("Testing Telegram Bot Info")
    print("=" * 60)

    telegram_service = TelegramService()

    bot_info = await telegram_service.get_bot_info()

    if bot_info:
        print("\n✅ Bot info retrieved successfully!")
        print(f"Bot ID: {bot_info['id']}")
        print(f"Username: @{bot_info['username']}")
        print(f"First Name: {bot_info['first_name']}")
        print(f"Can join groups: {bot_info['can_join_groups']}")
        print(f"Can read all group messages: {bot_info['can_read_all_group_messages']}")
        print(f"Supports inline queries: {bot_info['supports_inline_queries']}")
    else:
        print("\n❌ Failed to retrieve bot info")
        return False

    return True


async def test_webhook_setup():
    """Test webhook configuration"""
    print("\n" + "=" * 60)
    print("Testing Webhook Setup")
    print("=" * 60)

    telegram_service = TelegramService()
    webhook_url = os.getenv('TELEGRAM_WEBHOOK_URL', 'https://cate.sdb-dkr.ovh/api/v1/telegram/webhook')

    print(f"\nSetting webhook URL: {webhook_url}")

    success = await telegram_service.set_webhook(webhook_url)

    if success:
        print("✅ Webhook set successfully!")

        # Verify webhook info
        webhook_info = await telegram_service.get_webhook_info()

        if webhook_info:
            print("\n📋 Webhook Information:")
            print(f"URL: {webhook_info['url']}")
            print(f"Pending updates: {webhook_info['pending_update_count']}")
            print(f"Max connections: {webhook_info['max_connections']}")

            if webhook_info['last_error_message']:
                print(f"⚠️  Last error: {webhook_info['last_error_message']}")

        return True
    else:
        print("❌ Failed to set webhook")
        return False


async def test_send_message():
    """Test sending a message to admin"""
    print("\n" + "=" * 60)
    print("Testing Message Sending")
    print("=" * 60)

    telegram_service = TelegramService()

    # Get admin chat ID from environment or use a test chat ID
    test_chat_id = os.getenv('TELEGRAM_TEST_CHAT_ID')

    if not test_chat_id:
        print("⚠️  TELEGRAM_TEST_CHAT_ID not set in .env")
        print("ℹ️  To test message sending, add TELEGRAM_TEST_CHAT_ID=<your_telegram_id> to .env")
        print("ℹ️  You can get your chat ID by messaging your bot and checking the webhook logs")
        return True  # Not a failure, just skipped

    test_message = """
🤖 *Telegram Bot Test*

✅ Bot integration is working!

This is a test message from your AI Concierge system.

🙏 Service Diocésain de la Catéchèse
    """

    result = await telegram_service.send_message(
        chat_id=int(test_chat_id),
        text=test_message.strip(),
        parse_mode="Markdown"
    )

    if result:
        print(f"✅ Test message sent successfully!")
        print(f"Message ID: {result['message_id']}")
    else:
        print("❌ Failed to send test message")
        return False

    return True


async def test_inline_keyboard():
    """Test inline keyboard functionality"""
    print("\n" + "=" * 60)
    print("Testing Inline Keyboard")
    print("=" * 60)

    telegram_service = TelegramService()

    test_chat_id = os.getenv('TELEGRAM_TEST_CHAT_ID')

    if not test_chat_id:
        print("⚠️  TELEGRAM_TEST_CHAT_ID not set - skipping")
        return True

    # Create inline keyboard
    buttons = [
        [
            {"text": "📚 RENSEIGNEMENT", "callback_data": "service:renseignement"},
            {"text": "👨‍👩‍👧 CATECHESE", "callback_data": "service:catechese"}
        ],
        [
            {"text": "👤 CONTACT_HUMAIN", "callback_data": "service:contact_humain"}
        ],
        [
            {"text": "ℹ️ À propos", "url": "https://cate.sdb-dkr.com"}
        ]
    ]

    keyboard = telegram_service.create_inline_keyboard(buttons)

    message = """
📋 *Choisissez un service:*

Utilisez les boutons ci-dessous pour sélectionner le service dont vous avez besoin.
    """

    result = await telegram_service.send_message(
        chat_id=int(test_chat_id),
        text=message.strip(),
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    if result:
        print(f"✅ Inline keyboard message sent successfully!")
        print(f"Message ID: {result['message_id']}")
    else:
        print("❌ Failed to send keyboard message")
        return False

    return True


async def run_all_tests():
    """Run all tests"""
    print("\n🚀 Starting Telegram Bot Integration Tests")
    print("=" * 60)

    results = {}

    # Test 1: Bot Info
    results['bot_info'] = await test_bot_info()

    # Test 2: Webhook Setup
    results['webhook'] = await test_webhook_setup()

    # Test 3: Send Message
    results['send_message'] = await test_send_message()

    # Test 4: Inline Keyboard
    results['inline_keyboard'] = await test_inline_keyboard()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Your Telegram bot is ready to use.")
        print("\n📝 Next steps:")
        print("1. Start your bot by sending /start in Telegram")
        print("2. Test the AI conversation by sending a message")
        print("3. Check the logs for any issues")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")

    return passed == total


async def main():
    """Main test function"""
    try:
        success = await run_all_tests()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
