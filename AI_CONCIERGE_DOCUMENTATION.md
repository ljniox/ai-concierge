# AI Concierge - WhatsApp Auto-Reply System

## 🌟 Overview

The AI Concierge is an intelligent WhatsApp auto-reply system built with FastAPI and WAHA (WhatsApp HTTP API) that provides automated responses to customer messages based on configurable rules, keywords, and business hours.

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp     │    │     WAHA        │    │   FastAPI       │
│   User         │───▶│   Core API     │───▶│   Webhook       │
│   221765005555 │    │   (Webhook)    │    │   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   WAHA Session  │    │   Auto-Reply    │
                       │   Configuration │    │   Service       │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   Auto-Reply    │
                                               │   Configuration │
                                               └─────────────────┘
```

### Core Components

1. **WAHA API**: WhatsApp HTTP API for message handling
2. **FastAPI Webhook**: Receives and processes incoming messages
3. **Auto-Reply Service**: Handles message logic and API communication
4. **Configuration Manager**: Manages business rules and settings
5. **Docker Container**: Deployment and environment management

## 📁 Project Structure

```
ai-concierge/
├── webhook.py                 # Main FastAPI application
├── auto_reply_service.py      # Auto-reply business logic
├── auto_reply_config.py       # Configuration management
├── Dockerfile                 # Container configuration
├── docker-compose.yaml        # Coolify deployment
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables
├── test_*.py                 # Test scripts
└── AI_CONCIERGE_DOCUMENTATION.md  # This documentation
```

## 🔧 Configuration

### Environment Variables

```bash
# WAHA API Configuration
WAHA_API_KEY=28C5435535C2487DAFBD1164B9CD4E34
WAHA_BASE_URL=https://waha-core.niox.ovh/api
SESSION_NAME=default

# Auto-Reply Settings
AUTO_REPLY_ENABLED=true
WORKING_HOURS_START=09:00
WORKING_HOURS_END=18:00
WEEKEND_AUTO_REPLY=false
GROUP_AUTO_REPLY=false

# Message Templates
DEFAULT_REPLY=🤖 Merci pour votre message! Nous avons bien reçu votre demande et vous répondrons dès que possible.
OUT_OF_HOURS_REPLY=🌙 Bonsoir! Nous sommes actuellement hors de nos heures de bureau.

# Security
WEBHOOK_VERIFY_TOKEN=your-verify-token
BLACKLISTED_CONTACTS=
```

### Custom Keyword Replies

The system supports regex pattern matching for custom responses:

```python
{
    r'bonjour|salut|hello|hi|hey': "👋 Bonjour! Comment puis-je vous aider aujourd'hui?",
    r'merci|thanks|thank you': "🙏 Avec plaisir! N'hésitez pas si vous avez d'autres questions.",
    r'au revoir|bye|goodbye': "👋 Au revoir! Passez une excellente journée!",
    r'urgence|urgent|help|aide': "🚨 Nous avons bien reçu votre demande d'urgence.",
    r'prix|tarif|cost|price': "💰 Pour nos tarifs, merci de consulter notre site web.",
    r'horaires|ouverture|hours': "🕒 Nous sommes ouverts Lundi-Vendredi de 9h à 18h.",
    r'contact|téléphone|phone|call': "📞 Vous pouvez nous contacter au [votre numéro]."
}
```

## 🚀 Deployment

### Prerequisites

- Docker and Docker Compose
- Coolify account
- GitHub repository
- Domain name (ai-concierge.niox.ovh)

### Deployment Steps

1. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Coolify Setup**
   - Connect GitHub repository
   - Use `docker-compose.yaml` configuration
   - Set up domain and SSL
   - Configure health checks

3. **WAHA Configuration**
   ```bash
   curl -k -H "X-API-Key: $WAHA_API_KEY" \
     -X PUT https://waha-core.niox.ovh/api/sessions/default \
     -H "Content-Type: application/json" \
     -d '{
       "config": {
         "webhooks": [{
           "url": "https://ai-concierge.niox.ovh/webhook",
           "events": ["message", "session.status"]
         }]
       }
     }'
   ```

## 📡 Webhook Integration

### Webhook Endpoints

- `POST /webhook` - Main webhook receiver for WAHA events
- `GET /webhook` - Webhook verification endpoint
- `GET /` - Health check endpoint
- `GET /auto-reply/status` - Auto-reply configuration status
- `POST /auto-reply/toggle` - Enable/disable auto-reply
- `POST /auto-reply/test` - Send test message
- `POST /auto-reply/custom-replies` - Update custom replies

### Webhook Payload Structure

```json
{
  "id": "evt_01k52as4sv2vssjncnz17x77ta",
  "timestamp": 1757793784637,
  "event": "message",
  "session": "default",
  "me": {
    "id": "221773387902@c.us",
    "pushName": "Business Name"
  },
  "payload": {
    "id": "false_221765005555@c.us_3A1736EC0F71B53A0CCF",
    "timestamp": 1757793784,
    "from": "221765005555@c.us",
    "fromMe": false,
    "source": "app",
    "body": "bonjour",
    "hasMedia": false,
    "media": {
      "key": {
        "remoteJid": "221765005555@s.whatsapp.net"
      }
    }
  }
}
```

## 🤖 Auto-Reply Logic

### Message Processing Flow

1. **Message Reception**: Webhook receives message from WAHA
2. **Validation Checks**:
   - Auto-reply enabled?
   - Not from self (fromMe: false)?
   - Contact not blacklisted?
   - Not a group message?
3. **Content Analysis**: Extract message text from payload
4. **Response Selection**:
   - Check custom keyword matches
   - Apply time-based rules (working hours)
   - Select appropriate reply template
5. **Message Sending**: Send response via WAHA API

### Time-Based Rules

- **Working Hours**: Monday-Friday 09:00-18:00
- **Weekend**: Auto-reply disabled by default
- **Outside Hours**: Uses `OUT_OF_HOURS_REPLY` template

### Keyword Matching

System uses regex pattern matching with case-insensitive search:

```python
import re

pattern = r'bonjour|salut|hello|hi|hey'
message = "Bonjour, comment allez-vous?"
if re.search(pattern, message, re.IGNORECASE):
    return custom_reply
```

## 🔒 Security Features

### Authentication

- **WAHA API**: X-API-Key header authentication
- **Webhook**: Verify token for endpoint verification
- **Environment**: Sensitive data stored in environment variables

### Contact Management

- **Blacklist**: Block specific contacts from auto-replies
- **Group Control**: Optional group message responses
- **Rate Limiting**: Built-in API rate limiting

## 📊 Monitoring & Logging

### Log Levels

- **INFO**: General operation logs
- **DEBUG**: Detailed processing information
- **ERROR**: Error and exception tracking
- **WARNING**: Configuration and validation warnings

### Key Metrics

- Message processing success rate
- Auto-reply response time
- WAHA API call success/failure
- System health and availability

## 🧪 Testing

### Automated Tests

```bash
# Run auto-reply tests
python test_auto_reply.py

# Test phone number extraction
python debug_phone_extraction.py

# Manual testing
python test_manual_reply.py
```

### Manual Testing

1. **Send test message** via WhatsApp
2. **Check webhook logs** for processing
3. **Verify auto-reply** received
4. **Test different keywords** and time scenarios

## 🚨 Troubleshooting

### Common Issues

**No Auto-Reply Received**
1. Check working hours configuration
2. Verify WAHA webhook configuration
3. Review application logs for errors
4. Test phone number extraction

**WAHA API Timeouts**
1. Verify phone number format (should be `221765005555`, not `@c.us`)
2. Check WAHA session status
3. Validate API key and endpoint URL

**Deployment Issues**
1. Verify Docker image build
2. Check Coolify configuration
3. Ensure domain and SSL setup
4. Validate environment variables

### Debug Commands

```bash
# Check WAHA session
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default

# Test auto-reply status
curl -s https://ai-concierge.niox.ovh/auto-reply/status

# View application logs
docker logs ai-concierge-container
```

## 🔄 Future Enhancements

### Planned Features

- [ ] **Multi-language Support**: Reply templates in multiple languages
- [ ] **AI Integration**: GPT-based intelligent responses
- [ ] **Database Integration**: Store conversation history
- [ ] **Analytics Dashboard**: Message metrics and insights
- [ ] **Media Handling**: Process images, documents, audio
- [ ] **Appointment Booking**: Calendar integration
- [ ] **Payment Processing**: Payment request handling

### API Extensions

- Customer management endpoints
- Conversation history API
- Bulk messaging capabilities
- Template management system
- Analytics and reporting

## 📞 Support

### Technical Support

For technical issues and questions:
1. Check application logs
2. Review this documentation
3. Test with provided scripts
4. Verify WAHA API status

### Business Configuration

For business rule changes:
- Update environment variables
- Modify custom reply patterns
- Adjust working hours
- Manage contact blacklist

---

## 📋 Version History

### v1.0.0 (Current)
- ✅ Basic auto-reply functionality
- ✅ Time-based response rules
- ✅ Keyword pattern matching
- ✅ WAHA API integration
- ✅ Docker deployment
- ✅ Coolify configuration
- ✅ Webhook verification
- ✅ Health monitoring

### Known Issues

- Limited media message support
- No conversation history storage
- Basic error handling
- Single language support

---

**Last Updated**: September 13, 2025
**Version**: 1.0.0
**Maintainer**: AI Concierge Team