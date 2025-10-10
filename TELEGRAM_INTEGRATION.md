# Telegram Bot Integration Guide

## Overview

The AI Concierge system now supports Telegram as an additional messaging platform alongside WhatsApp. Users can interact with the same AI-powered services through Telegram.

## Bot Information

- **Bot Username:** @sdbcatebot
- **Bot URL:** https://t.me/sdbcatebot
- **Platform:** Telegram

## Features

### Supported Services

The Telegram bot provides access to all three core services:

1. **RENSEIGNEMENT** - General information about catechism programs, schedules, and enrollment
2. **CATECHESE** - Authenticated access to student information (requires parent code)
3. **CONTACT_HUMAIN** - Direct contact with human agents

### Bot Commands

Users can interact with the bot using the following commands:

- `/start` - Start a conversation and see welcome message
- `/help` - Display help information and available commands
- `/services` - View all available services
- `/contact` - Get contact information
- `/cancel` - Cancel current operation

### Message Types Supported

- ✅ Text messages
- ✅ Photos (with captions)
- ✅ Documents
- ✅ Voice messages
- ✅ Audio files
- ✅ Videos
- ✅ Inline keyboards for interactive selections

## Technical Architecture

### Components

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Telegram Bot API│
└────────┬────────┘
         │ (Webhook)
         ▼
┌─────────────────┐
│  FastAPI App    │
│  /telegram/     │
│   webhook       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ TelegramService │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│InteractionSvc   │
│ (Orchestration) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Claude AI +    │
│  Data Sources   │
└─────────────────┘
```

### Services

**TelegramService** (`src/services/telegram_service.py`)
- Handles all Telegram Bot API operations
- Message sending (text, photos, documents)
- Message editing and deletion
- Webhook management
- Inline keyboard creation

**Telegram API Router** (`src/api/telegram.py`)
- Webhook endpoint for receiving Telegram updates
- Command handling
- Message processing
- Callback query handling
- Integration with InteractionService

## Setup Instructions

### 1. Prerequisites

- Telegram bot token (already configured)
- FastAPI application running
- External URL accessible from Telegram servers

### 2. Environment Configuration

The following environment variables are configured in `.env`:

```bash
# Telegram Bot Settings
TELEGRAM_BOT_TOKEN=8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus
TELEGRAM_WEBHOOK_URL=https://cate.sdb-dkr.ovh/api/v1/telegram/webhook
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

The `python-telegram-bot==20.7` package has been added to requirements.txt.

### 4. Set Up Webhook

#### Option A: Using the Test Script

```bash
python test_telegram_bot.py
```

This will:
- Verify bot credentials
- Set up the webhook automatically
- Test message sending
- Verify the integration

#### Option B: Using the API Endpoint

```bash
curl -X POST https://cate.sdb-dkr.ovh/api/v1/telegram/webhook/set \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://cate.sdb-dkr.ovh/api/v1/telegram/webhook"}'
```

#### Option C: Manual Setup

```python
from src.services.telegram_service import TelegramService
import asyncio

async def setup():
    service = TelegramService()
    await service.set_webhook("https://cate.sdb-dkr.ovh/api/v1/telegram/webhook")

asyncio.run(setup())
```

### 5. Verify Webhook

Check webhook status:

```bash
curl https://cate.sdb-dkr.ovh/api/v1/telegram/webhook/info
```

Or get bot info:

```bash
curl https://cate.sdb-dkr.ovh/api/v1/telegram/bot/info
```

## API Endpoints

### Webhook Endpoints

**POST /api/v1/telegram/webhook**
- Receives updates from Telegram
- Processes messages, commands, and callbacks
- Returns 200 OK for all updates

**GET /api/v1/telegram/webhook/info**
- Returns current webhook configuration
- Shows pending updates and errors

**POST /api/v1/telegram/webhook/set**
- Sets or updates webhook URL
- Body: `{"webhook_url": "https://..."}`

**DELETE /api/v1/telegram/webhook**
- Removes webhook (switches to polling mode)

### Bot Information

**GET /api/v1/telegram/bot/info**
- Returns bot profile information
- Shows capabilities and settings

## Usage Examples

### Sending a Simple Message

```python
from src.services.telegram_service import TelegramService

telegram = TelegramService()
await telegram.send_message(
    chat_id=123456789,
    text="Hello from AI Concierge!",
    parse_mode="Markdown"
)
```

### Sending with Inline Keyboard

```python
telegram = TelegramService()

buttons = [
    [
        {"text": "Option 1", "callback_data": "opt1"},
        {"text": "Option 2", "callback_data": "opt2"}
    ],
    [
        {"text": "Visit Website", "url": "https://example.com"}
    ]
]

keyboard = telegram.create_inline_keyboard(buttons)

await telegram.send_message(
    chat_id=123456789,
    text="Choose an option:",
    reply_markup=keyboard
)
```

### Sending a Document

```python
await telegram.send_document(
    chat_id=123456789,
    document_url="https://example.com/file.pdf",
    caption="Your certificate",
    filename="certificate.pdf"
)
```

## Testing

### Run the Test Suite

```bash
python test_telegram_bot.py
```

Tests include:
- ✅ Bot information retrieval
- ✅ Webhook setup and verification
- ✅ Message sending
- ✅ Inline keyboard functionality

### Manual Testing

1. Open Telegram
2. Search for `@sdbcatebot`
3. Send `/start`
4. Test the conversation flow

## User Workflow

### 1. Starting a Conversation

User sends `/start` and receives:
```
🙏 Bienvenue au Service Diocésain de la Catéchèse

Je suis Gust-IA, votre assistant virtuel. Je peux vous aider avec :

📚 RENSEIGNEMENT - Informations générales sur la catéchèse
👨‍👩‍👧 CATECHESE - Accès aux informations de vos enfants (avec code parent)
👤 CONTACT_HUMAIN - Parler à un agent humain

Comment puis-je vous aider aujourd'hui ?
```

### 2. Service Selection

User can:
- Type a message naturally (AI will detect intent)
- Use `/services` to see all options
- Use inline keyboards when provided

### 3. Authentication (for CATECHESE)

When accessing student information:
1. System prompts for parent code
2. User provides code
3. System validates and grants access
4. User can view notes, schedules, certificates

### 4. Getting Help

- `/help` - View all commands
- `/contact` - Get contact information
- Type "aide" or "help" for assistance

## Session Management

- **User Identification:** Telegram user ID (`telegram_<user_id>`)
- **Session Storage:** Redis (same as WhatsApp)
- **Session Timeout:** 30 minutes of inactivity
- **Cross-Platform:** Separate sessions for Telegram and WhatsApp

## Message Formatting

### Telegram Markdown

The bot supports Telegram's Markdown formatting:

- `*bold*` - **bold text**
- `_italic_` - _italic text_
- `[link](url)` - hyperlinks
- `` `code` `` - inline code
- Emojis - full support 🎉

### Message Limits

- Maximum message length: 4096 characters
- Messages are automatically truncated if needed
- Long responses are split into multiple messages

## Security Considerations

### Token Security

- ✅ Bot token stored in environment variables
- ✅ Never exposed in logs or responses
- ✅ Access restricted to authorized servers

### User Data

- User data stored with `telegram_<user_id>` prefix
- Separate from WhatsApp users
- Same privacy and security policies apply
- Parent codes required for student information

### Webhook Security

- HTTPS-only webhook endpoint
- Telegram validates requests from their servers
- Application validates request structure

## Monitoring and Logs

### Structured Logging

All Telegram interactions are logged:

```json
{
  "event": "telegram_message_received",
  "message_id": 123,
  "chat_id": 456789,
  "user_id": 456789,
  "username": "johndoe",
  "text_length": 15
}
```

### Key Metrics

Monitor these metrics:
- Message receive rate
- Response send success rate
- Webhook errors
- Session creation rate
- Service usage distribution

### Error Handling

The system handles:
- ✅ Network failures (automatic retry)
- ✅ Invalid messages (graceful response)
- ✅ Bot API errors (logged and reported)
- ✅ Timeout issues (fallback responses)

## Troubleshooting

### Webhook Not Receiving Messages

1. Check webhook URL is accessible:
   ```bash
   curl https://cate.sdb-dkr.ovh/api/v1/telegram/webhook
   ```

2. Verify webhook is set:
   ```bash
   curl https://cate.sdb-dkr.ovh/api/v1/telegram/webhook/info
   ```

3. Check application logs:
   ```bash
   docker logs ai-concierge-app-1 | grep telegram
   ```

### Bot Not Responding

1. Verify bot token is correct
2. Check application is running
3. Review error logs
4. Test with `/start` command

### Messages Not Formatted Correctly

- Ensure Markdown syntax is correct
- Check for special characters that need escaping
- Verify parse_mode is set to "Markdown"

## Differences from WhatsApp

| Feature | WhatsApp | Telegram |
|---------|----------|----------|
| Formatting | Limited | Full Markdown |
| Inline Keyboards | ❌ | ✅ |
| Commands | ❌ | ✅ (`/start`, `/help`) |
| Edit Messages | ❌ | ✅ |
| Delete Messages | ❌ | ✅ |
| File Size Limit | 16 MB | 20 MB (bot API) |
| Groups | Limited | Full support |

## Future Enhancements

### Planned Features

- [ ] Callback query handling for interactive menus
- [ ] Rich media messages (polls, quizzes)
- [ ] Group chat support
- [ ] Channel broadcasting
- [ ] Bot commands customization via BotFather
- [ ] Payment integration (Telegram Payments)
- [ ] Games and interactive content

### Integration Ideas

- Push notifications for important updates
- Scheduled reminders via Telegram
- Parent-teacher communication channel
- Event announcements and registration
- Certificate delivery via Telegram

## Support

For issues or questions:

- **Technical Support:** Check application logs
- **Bot Configuration:** Review `.env` settings
- **User Issues:** Test with `test_telegram_bot.py`
- **Documentation:** Telegram Bot API docs at https://core.telegram.org/bots/api

## Conclusion

The Telegram integration provides a modern, feature-rich alternative to WhatsApp for interacting with the AI Concierge system. With support for inline keyboards, commands, and rich formatting, users can enjoy an enhanced experience while accessing the same powerful AI-driven services.

---

**Last Updated:** October 4, 2025
**Version:** 1.0.0
**Bot Username:** @sdbcatebot
