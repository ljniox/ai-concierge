# WhatsApp Webhook Contract: Automatic Account Creation

**Contract Version**: 1.0 | **Date**: 2025-10-11 | **Platform**: WhatsApp Business API (WAHA)
**Purpose**: Define webhook contract for automatic account creation via WhatsApp

## Webhook Endpoint

**URL**: `https://cate.sdb-dkr.ovh/api/v1/whatsapp/webhook`
**Method**: `POST`
**Content-Type**: `application/json`
**Authentication**: WAHA API token validation

## WAHA Configuration

**WAHA Base URL**: `https://waha-core.niox.ovh`
**API Token**: `28C5435535C2487DAFBD1164B9CD4E34`
**Session**: `default`

## Incoming Webhook Schema

### Message Update Structure (WAHA Format)

```json
{
  "event": "message",
  "session": "default",
  "payload": {
    "id": "wamid.HBgLNDQ3Njk3Nzg4MVVBTjRERDZCWThZNUhBAA==",
    "timestamp": 1728427087,
    "from": "4476978781@c.us",
    "fromMe": false,
    "pushname": "James Niox",
    "recipient": "14155238886@c.us",
    "text": {
      "body": "/start"
    },
    "type": "text",
    "source": "web"
  }
}
```

### Key Fields Extraction

**User Identification**:
- `payload.from`: WhatsApp User ID (STRING) - Format: `phone_number@c.us`
- `payload.pushname`: Contact name (STRING)
- Extracted phone number: `4476978781` from `4476978781@c.us`

**Message Content**:
- `payload.text.body`: Message text (STRING)
- `payload.timestamp`: Timestamp (UNIX milliseconds)
- `payload.type`: Message type - "text", "contact", "image", etc.

**Chat Information**:
- `payload.recipient`: Bot number (STRING)
- `payload.session`: WAHA session name

### Contact Message Structure

```json
{
  "event": "message",
  "session": "default",
  "payload": {
    "id": "wamid.HBgLNDQ3Njk3Nzg4MVVBTjRERDZCWThZNUhBAA==",
    "timestamp": 1728427087,
    "from": "4476978781@c.us",
    "fromMe": false,
    "pushname": "James Niox",
    "recipient": "14155238886@c.us",
    "contact": {
      "contacts": [
        {
          "phones": [
            {
              "phone": "+221765005555",
              "wa_id": "221765005555",
              "type": "MOBILE"
            }
          ],
          "name": {
            "formatted_name": "James Niox",
            "first_name": "James",
            "last_name": "Niox"
          }
        }
      ]
    },
    "type": "contact",
    "source": "web"
  }
}
```

## Processing Flow

### 1. Webhook Validation

```python
# Pseudo-code for webhook validation
def validate_whatsapp_webhook(request):
    # Verify WAHA session or API token
    if not verify_waha_session(request):
        return False, "Invalid WAHA session"

    # Parse JSON body
    try:
        webhook_data = request.json()
        return True, webhook_data
    except:
        return False, "Invalid JSON"
```

### 2. Phone Number Extraction

**Automatic Extraction**:
- Extract phone number from `payload.from` field
- Format: `4476978781@c.us` → `4476978781`
- Add country code: `+221` + `4476978781` → `+2214476978781`

**Contact Message Processing**:
- Extract phone number from `payload.contact.contacts[0].phones[0].phone`
- Use provided phone number directly if available
- Validate and normalize using python-phonenumbers

### 3. Account Creation Logic

```python
# Pseudo-code for account creation
async def handle_whatsapp_message(webhook_data):
    payload = webhook_data['payload']
    whatsapp_user_id = payload['from']

    # Extract phone number from user ID
    phone_match = re.match(r'(\d+)@c\.us$', whatsapp_user_id)
    if not phone_match:
        return await send_error_message(whatsapp_user_id, "Invalid user ID")

    phone_number = f"+221{phone_match.group(1)}"

    # Check existing account
    account = await get_user_by_whatsapp_id(whatsapp_user_id)

    if account is None:
        # Attempt automatic account creation
        success = await attempt_account_creation(
            whatsapp_user_id=whatsapp_user_id,
            phone_number=phone_number,
            contact_name=payload.get('pushname')
        )

        if success:
            await send_welcome_message(whatsapp_user_id)
        else:
            await send_phone_not_found_message(whatsapp_user_id)
        return

    # Process existing user message
    await process_user_message(account, webhook_data)
```

## Response Messages

### Welcome Message (New Account)

```json
{
  "chatId": "4476978781@c.us",
  "text": "👋 *Bienvenue au Service de la catéchèse de Saint Jean Bosco de Nord Foire!*\n\nVotre compte a été créé automatiquement. Vous pouvez maintenant accéder à tous les services pour les parents.\n\n*Options disponibles:*\n• Voir les informations de vos enfants\n• Inscrire un nouvel enfant\n• Contacter un responsable\n\nRépondez avec le numéro de votre choix ou tapez *aide* pour plus d'informations.",
  "type": "text"
}
```

### Phone Number Not Found

```json
{
  "chatId": "4476978781@c.us",
  "text": "❌ *Numéro non trouvé*\n\nNous n'avons pas pu trouver votre numéro dans notre base de données de parents.\n\nVeuillez contacter le secrétariat de la catéchèse:\n📍 *Saint Jean Bosco de Nord Foire*\n📞 *Téléphone*: [à compléter]\n\nOu répondez avec votre nom complet pour que nous puissions vous aider.",
  "type": "text"
}
```

### Interactive Menu

```json
{
  "chatId": "4476978781@c.us",
  "text": "📋 *Menu Principal*\n\nQue souhaitez-vous faire?",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": {
      "text": "Choisissez une option ci-dessous:"
    },
    "buttons": [
      {
        "id": "mes_enfants",
        "text": "👶 Mes enfants"
      },
      {
        "id": "inscription",
        "text": "📝 Inscription"
      },
      {
        "id": "contacter",
        "text": "📞 Contacter"
      },
      {
        "id": "aide",
        "text": "❓ Aide"
      }
    ]
  }
}
```

## WAHA API Integration

### Sending Messages

**Text Message**:
```python
async def send_whatsapp_message(chat_id, text):
    url = f"{WAHA_BASE_URL}/api/sendText"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WAHA_API_TOKEN}"
    }
    data = {
        "session": "default",
        "chatId": chat_id,
        "text": text
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            return await response.json()
```

**Interactive Message**:
```python
async def send_interactive_message(chat_id, text, buttons):
    url = f"{WAHA_BASE_URL}/api/sendInteractive"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {WAHA_API_TOKEN}"
    }
    data = {
        "session": "default",
        "chatId": chat_id,
        "text": text,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "buttons": buttons
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            return await response.json()
```

### Error Handling

**WAHA API Errors**:
```python
async def handle_waha_error(response):
    if response.status == 400:
        error_data = await response.json()
        logger.error(f"WAHA API error: {error_data}")
        return False, "Invalid request"
    elif response.status == 401:
        logger.error("WAHA authentication failed")
        return False, "Authentication error"
    elif response.status >= 500:
        logger.error(f"WAHA server error: {response.status}")
        return False, "Server error"

    return True, await response.json()
```

## Phone Number Normalization

### WhatsApp Number Processing

```python
import phonenumbers

def normalize_whatsapp_number(phone_number_str):
    """Normalize WhatsApp phone number to E.164 format"""

    # Extract from WhatsApp format (4476978781@c.us)
    if '@c.us' in phone_number_str:
        phone_number_str = phone_number_str.split('@')[0]

    # Add country code if missing (assume Senegal)
    if not phone_number_str.startswith('+'):
        phone_number_str = '+221' + phone_number_str

    try:
        # Parse and validate using phonenumbers
        parsed_number = phonenumbers.parse(phone_number_str, None)

        if phonenumbers.is_valid_number(parsed_number):
            return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        else:
            return None

    except phonenumbers.NumberParseException:
        return None
```

### Country Code Detection

**Supported Formats**:
- `+2214476978781` - Full E.164 format
- `002214476978781` - International format with 00 prefix
- `4476978781` - Local format (assumes +221)
- `447 697 87 81` - With spaces and separators

**Validation Rules**:
- Must be valid mobile number for Senegal
- Length should be 9 digits after country code
- Must start with valid mobile prefix (77, 76, 78, 70)

## Security Considerations

### Webhook Security

**WAHA Session Validation**:
- Validate WAHA session name and token
- Implement IP filtering for WAHA server
- Rate limit webhook processing per user

**Data Validation**:
- Validate all incoming JSON structures
- Sanitize user inputs before database operations
- Implement input length limits and content filtering

### Phone Number Protection

**Secure Processing**:
- Process phone numbers in memory only
- Log phone numbers in hashed format for audit
- Implement access controls for phone data

**Privacy Compliance**:
- Automatic consent inferred from WhatsApp contact
- Provide opt-out mechanism
- Implement data retention policies

## Rate Limiting

### WAHA API Limits

- **Messages**: 50 messages per second per session
- **Concurrent Requests**: 10 simultaneous API calls
- **Media Upload**: 100 MB per day per session

### Application Limits

- **Account Creation**: 1 attempt per phone number per hour
- **Message Processing**: 100 messages per minute per user
- **Interactive Menus**: 10 requests per conversation per minute

## Error Handling

### HTTP Response Codes

- `200 OK`: Webhook processed successfully
- `400 Bad Request`: Invalid webhook format or validation failed
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Processing error

### Error Response Format

```json
{
  "error": "Phone number validation failed",
  "details": "Invalid Senegalese phone number format",
  "phone_number": "+2214476978781",
  "timestamp": "2025-10-11T12:34:56Z"
}
```

### Recovery Strategies

**Account Creation Failures**:
- Retry with exponential backoff
- Log failed attempts for admin review
- Provide manual account creation interface

**WAHA API Failures**:
- Implement circuit breaker pattern
- Queue messages for retry when API is available
- Fallback to basic text messages if interactive fails

## Monitoring and Logging

### Key Metrics

**Business Metrics**:
- Account creation success rate by phone number
- Message response times
- User engagement with interactive menus
- Phone number validation accuracy

**Technical Metrics**:
- WAHA API response times
- Webhook processing latency
- Error rates by category
- Database query performance

### Logging Format

```json
{
  "timestamp": "2025-10-11T12:34:56Z",
  "level": "INFO",
  "event": "whatsapp_account_creation",
  "whatsapp_user_id": "4476978781@c.us",
  "phone_number": "+2214476978781",
  "processing_time_ms": 200,
  "success": true,
  "user_id": 12345,
  "waha_response_time_ms": 150
}
```

## Testing Scenarios

### Positive Test Cases

1. **Automatic Account Creation**
   - Input: First message from new WhatsApp user
   - Expected: Extract phone number → Create account → Send welcome message

2. **Contact Message Processing**
   - Input: User shares contact vCard
   - Expected: Extract phone number from contact → Create account

3. **Interactive Menu Response**
   - Input: User clicks button in interactive message
   - Expected: Process button response → Send relevant information

### Negative Test Cases

1. **Invalid Phone Number**
   - Input: WhatsApp user with invalid number format
   - Expected: Error message with guidance

2. **Phone Number Not in Database**
   - Input: Valid number not in parent database
   - Expected: Guidance message with contact information

3. **WAHA API Unavailable**
   - Input: WAHA server not responding
   - Expected: Graceful error handling and retry

### Edge Cases

1. **International Numbers**
   - Input: Various international phone number formats
   - Expected: Proper normalization and validation

2. **Duplicate Accounts**
   - Input: User tries to create multiple accounts
   - Expected: Login to existing account

3. **Message Flood**
   - Input: User sends many messages quickly
   - Expected: Rate limiting applied gracefully

## Integration Points

### WAHA Service Integration

**Required Configuration**:
- WAHA base URL and API token
- Session management (default session)
- Webhook endpoint registration

**API Methods**:
- `/api/sendText` - Send text messages
- `/api/sendInteractive` - Send interactive messages
- `/api/getChats` - Get chat information
- `/api/startSession` - Start/restart session

### Database Integration

**Required Tables**:
- `user_accounts`: Store WhatsApp user accounts
- `account_creation_audit`: Log creation attempts
- `user_sessions`: Manage conversation state

**Query Patterns**:
- Get user by WhatsApp ID (`4476978781@c.us`)
- Create user with phone number validation
- Log WAHA-specific events

### External Services

**Parent Database**:
- Query catechese database by phone number
- Handle different phone number formats
- Match against existing parent records

**Admin Notifications**:
- Notify admins of failed account creations
- Provide manual account creation interface
- Monitor system health and performance

---

**Contract Status**: Ready for implementation. The WhatsApp webhook contract provides comprehensive coverage of the WAHA integration requirements for automatic account creation via WhatsApp.