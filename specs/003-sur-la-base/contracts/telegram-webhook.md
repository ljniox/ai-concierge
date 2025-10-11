# Telegram Webhook Contract: Automatic Account Creation

**Contract Version**: 1.0 | **Date**: 2025-10-11 | **Platform**: Telegram Bot API
**Purpose**: Define webhook contract for automatic account creation via Telegram

## Webhook Endpoint

**URL**: `https://cate.sdb-dkr.ovh/api/v1/telegram/webhook`
**Method**: `POST`
**Content-Type**: `application/json`
**Authentication**: Secret token validation (`gust-ia-webhook-secret`)

## Incoming Webhook Schema

### Message Update Structure

```json
{
  "update_id": 154821486,
  "message": {
    "message_id": 123,
    "from": {
      "id": 695065578,
      "is_bot": false,
      "first_name": "James",
      "last_name": "Niox",
      "username": "jamesniox",
      "language_code": "fr"
    },
    "chat": {
      "id": 695065578,
      "first_name": "James",
      "last_name": "Niox",
      "username": "jamesniox",
      "type": "private"
    },
    "date": 1728427087,
    "text": "/start"
  }
}
```

### Key Fields Extraction

**User Identification**:
- `message.from.id`: Telegram User ID (BIGINT) - Primary identifier
- `message.from.first_name`: User first name (STRING)
- `message.from.last_name`: User last name (STRING)
- `message.from.username`: Username (STRING, optional)

**Message Content**:
- `message.text`: Message text (STRING)
- `message.date`: Timestamp (UNIX)

**Chat Information**:
- `chat.id`: Chat ID (BIGINT) - Same as user_id for private chats
- `chat.type`: Chat type - always "private" for direct messages

## Processing Flow

### 1. Webhook Validation

```python
# Pseudo-code for webhook validation
def validate_webhook(request):
    # Verify secret token header
    if request.headers.get('X-Telegram-Bot-Api-Secret-Token') != 'gust-ia-webhook-secret':
        return False, "Invalid secret token"

    # Parse JSON body
    try:
        webhook_data = request.json()
        return True, webhook_data
    except:
        return False, "Invalid JSON"
```

### 2. Phone Number Extraction Strategy

**Primary Method**: User profile information
- Telegram doesn't provide phone numbers directly in messages
- Must request user to share phone number or use existing contact

**Secondary Method**: Contact message
```json
{
  "message": {
    "contact": {
      "phone_number": "+221765005555",
      "first_name": "James",
      "last_name": "Niox",
      "user_id": 695065578
    }
  }
}
```

**Account Creation Flow**:
1. Receive `/start` or first message from user
2. Check if user account exists by `telegram_user_id`
3. If no account exists, request phone number
4. Process phone number and create account
5. Send welcome message with available options

### 3. Account Creation Logic

```python
# Pseudo-code for account creation
async def handle_telegram_message(webhook_data):
    user_info = webhook_data['message']['from']
    telegram_user_id = user_info['id']

    # Check existing account
    account = await get_user_by_telegram_id(telegram_user_id)

    if account is None:
        # Request phone number for account creation
        await request_phone_number(telegram_user_id)
        return

    # Process existing user message
    await process_user_message(account, webhook_data)
```

## Response Messages

### Welcome Message (New Account)

```json
{
  "method": "sendMessage",
  "chat_id": 695065578,
  "text": "👋 *Bienvenue au Service de la catéchèse de Saint Jean Bosco de Nord Foire!*\n\nVotre compte a été créé automatiquement. Vous pouvez maintenant accéder à tous les services pour les parents.\n\n*Options disponibles:*\n• Voir les informations de vos enfants\n• Inscrire un nouvel enfant\n• Contacter un responsable\n\nQue souhaitez-vous faire?",
  "parse_mode": "Markdown",
  "reply_markup": {
    "keyboard": [
      [{"text": "👶 Mes enfants"}, {"text": "📝 Inscription"}],
      [{"text": "📞 Contacter"}, {"text": "❓ Aide"}]
    ],
    "resize_keyboard": true,
    "one_time_keyboard": false
  }
}
```

### Phone Number Request

```json
{
  "method": "sendMessage",
  "chat_id": 695065578,
  "text": "🔐 *Vérification requise*\n\nPour créer votre compte, veuillez partager votre numéro de téléphone. Cela nous permet de vous identifier dans notre base de données de parents.\n\nCliquez sur le bouton ci-dessous pour partager votre numéro:",
  "parse_mode": "Markdown",
  "reply_markup": {
    "keyboard": [
      [{"text": "📱 Partager mon numéro", "request_contact": true}]
    ],
    "resize_keyboard": true,
    "one_time_keyboard": true
  }
}
```

### Error Messages

**Phone Number Not Found**:
```json
{
  "method": "sendMessage",
  "chat_id": 695065578,
  "text": "❌ *Numéro non trouvé*\n\nNous n'avons pas pu trouver votre numéro dans notre base de données de parents.\n\nVeuillez contacter le secrétariat de la catéchèse pour mettre à jour vos informations.\n\n📞 *Contact*: [Secrétariat]",
  "parse_mode": "Markdown"
}
```

**Account Creation Failed**:
```json
{
  "method": "sendMessage",
  "chat_id": 695065578,
  "text": "⚠️ *Erreur technique*\n\nUne erreur est survenue lors de la création de votre compte. Nos équipes ont été notifiées.\n\nVeuillez réessayer plus tard ou contacter le support technique.",
  "parse_mode": "Markdown"
}
```

## Error Handling

### HTTP Response Codes

- `200 OK`: Webhook processed successfully
- `400 Bad Request`: Invalid webhook format or validation failed
- `500 Internal Server Error`: Processing error (account creation failure)

### Error Response Format

```json
{
  "error": "Validation failed",
  "details": "Invalid secret token",
  "timestamp": "2025-10-11T12:34:56Z"
}
```

### Retry Logic

**Automatic Retries**:
- Telegram automatically retries on 5xx errors
- Implement idempotent operations to handle duplicate webhooks
- Use `update_id` to detect and ignore duplicate updates

**Manual Recovery**:
- Log all failed account creation attempts
- Provide admin interface for manual account creation
- Support for phone number lookup and account creation by admin

## Security Considerations

### Webhook Security

**Secret Token Validation**:
- Validate `X-Telegram-Bot-Api-Secret-Token` header
- Use environment variable for secret token
- Implement rate limiting per user

**Data Validation**:
- Validate all incoming data fields
- Sanitize user inputs before processing
- Implement input length limits

### Phone Number Protection

**Secure Storage**:
- Encrypt phone numbers in database (optional)
- Implement access controls for phone data
- Log all phone number access attempts

**Privacy Compliance**:
- Obtain explicit consent for phone number collection
- Provide data deletion capabilities
- Implement retention policies

## Rate Limiting

### Per-User Limits

- **Messages**: 10 messages per minute per user
- **Account Creation**: 1 attempt per hour per phone number
- **Phone Requests**: 3 requests per conversation

### Global Limits

- **Webhook Processing**: 1000 requests per minute
- **Concurrent Processing**: 100 simultaneous account creations

## Monitoring and Logging

### Key Metrics

**Business Metrics**:
- Account creation success rate
- Time to first successful interaction
- Phone number validation success rate
- User engagement after account creation

**Technical Metrics**:
- Webhook processing latency
- Error rates by type
- Database query performance
- Memory and CPU usage

### Logging Format

```json
{
  "timestamp": "2025-10-11T12:34:56Z",
  "level": "INFO",
  "event": "account_creation_started",
  "telegram_user_id": 695065578,
  "phone_number": "+221765005555",
  "processing_time_ms": 150,
  "success": true,
  "user_id": 12345
}
```

## Testing Scenarios

### Positive Test Cases

1. **New User Account Creation**
   - Input: First message from new user
   - Expected: Phone number request → Account creation → Welcome message

2. **Existing User Login**
   - Input: Message from existing user
   - Expected: Direct access to user functions

3. **Phone Number Validation**
   - Input: Valid Senegalese phone number
   - Expected: Successful account creation

### Negative Test Cases

1. **Invalid Webhook**
   - Input: Missing secret token
   - Expected: 400 Bad Request

2. **Phone Number Not Found**
   - Input: Phone number not in parent database
   - Expected: Error message with guidance

3. **Duplicate Account Creation**
   - Input: Existing user tries to create new account
   - Expected: Login to existing account

### Edge Cases

1. **International Phone Numbers**
   - Input: Various international formats
   - Expected: Proper normalization and validation

2. **Concurrent Account Creation**
   - Input: Multiple users creating accounts simultaneously
   - Expected: All accounts created successfully without conflicts

3. **Network Failures**
   - Input: Database connection failure during creation
   - Expected: Graceful error handling and retry logic

## Integration Points

### Database Integration

**Required Tables**:
- `user_accounts`: Store Telegram user accounts
- `account_creation_audit`: Log all creation attempts
- `user_sessions`: Manage conversation state

**Queries**:
- Get user by Telegram ID
- Create new user account
- Log creation attempts
- Update session state

### External Services

**Parent Database**:
- Query catechese database for phone number matching
- Handle database connection failures gracefully

**Notification Service**:
- Send notifications to admins for failed creations
- Log events for monitoring

---

**Contract Status**: Ready for implementation. The webhook contract provides comprehensive coverage of the Telegram integration requirements for automatic account creation.