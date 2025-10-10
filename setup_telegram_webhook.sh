#!/bin/bash
# Setup Telegram webhook for AI Concierge
# This script sets up the Telegram bot webhook

set -e

echo "========================================"
echo "Telegram Webhook Setup Script"
echo "========================================"
echo ""

# Load environment variables
if [ -f .env ]; then
    # Source specific variables we need
    export TELEGRAM_BOT_TOKEN=$(grep "^TELEGRAM_BOT_TOKEN=" .env | cut -d '=' -f2)
    export TELEGRAM_WEBHOOK_URL=$(grep "^TELEGRAM_WEBHOOK_URL=" .env | cut -d '=' -f2)
    echo "✓ Environment variables loaded from .env"
else
    echo "✗ .env file not found!"
    exit 1
fi

# Check if bot token is set
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "✗ TELEGRAM_BOT_TOKEN not set in .env"
    exit 1
fi

echo "✓ Bot token found"
echo ""

# Get webhook URL
WEBHOOK_URL="${TELEGRAM_WEBHOOK_URL:-https://cate.sdb-dkr.ovh/api/v1/telegram/webhook}"

echo "Setting webhook to: $WEBHOOK_URL"
echo ""

# Set webhook using Telegram API
RESPONSE=$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
    -d "url=${WEBHOOK_URL}" \
    -d "allowed_updates=[\"message\",\"edited_message\",\"callback_query\"]")

echo "Response from Telegram:"
echo "$RESPONSE" | python3 -m json.tool
echo ""

# Check if successful
if echo "$RESPONSE" | grep -q '"ok":true'; then
    echo "✅ Webhook set successfully!"
else
    echo "❌ Failed to set webhook"
    exit 1
fi

echo ""
echo "Getting webhook info..."
echo ""

# Get webhook info
INFO_RESPONSE=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo")

echo "Current webhook configuration:"
echo "$INFO_RESPONSE" | python3 -m json.tool
echo ""

# Get bot info
echo "Getting bot info..."
echo ""

BOT_INFO=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe")

echo "Bot information:"
echo "$BOT_INFO" | python3 -m json.tool
echo ""

# Extract bot username
BOT_USERNAME=$(echo "$BOT_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['username'])" 2>/dev/null || echo "unknown")

echo "========================================"
echo "✅ Setup complete!"
echo "========================================"
echo ""
echo "Your bot is now ready to receive messages!"
echo ""
echo "Bot: @${BOT_USERNAME}"
echo "Webhook: ${WEBHOOK_URL}"
echo ""
echo "Next steps:"
echo "1. Open Telegram and search for @${BOT_USERNAME}"
echo "2. Send /start to begin"
echo "3. Test the conversation"
echo ""
echo "To test programmatically:"
echo "  python test_telegram_bot.py"
echo ""
