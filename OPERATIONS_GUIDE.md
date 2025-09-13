# AI Concierge - Operations Guide

## 🚀 Quick Start

### System Status Check

```bash
# Check if application is running
curl -s https://ai-concierge.niox.ovh/

# Check WAHA session status
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default

# Check auto-reply configuration
curl -s https://ai-concierge.niox.ovh/auto-reply/status
```

### Testing Auto-Reply

```bash
# Send test message via WAHA API
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  -X POST https://waha-core.niox.ovh/api/sendText \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "221773387902@c.us",
    "text": "bonjour test"
  }'

# Test auto-reply directly
curl -s -X POST https://ai-concierge.niox.ovh/auto-reply/test
```

## 🔧 Configuration Management

### Environment Variables

```bash
# View current configuration
echo "AUTO_REPLY_ENABLED: $AUTO_REPLY_ENABLED"
echo "WORKING_HOURS: $WORKING_HOURS_START - $WORKING_HOURS_END"
echo "WEEKEND_AUTO_REPLY: $WEEKEND_AUTO_REPLY"

# Edit configuration
nano .env
```

### Custom Replies Management

```bash
# Update custom replies
curl -s -X POST https://ai-concierge.niox.ovh/auto-reply/custom-replies \
  -H "Content-Type: application/json" \
  -d '{
    "bonjour|salut|hello": "👋 Bonjour! Comment puis-je vous aider?",
    "merci|thanks": "🙏 De rien!",
    "urgence|urgent": "🚨 Nous avons bien reçu votre demande d''urgence."
  }'

# View current custom replies
curl -s https://ai-concierge.niox.ovh/auto-reply/status | jq '.custom_replies_count'
```

### Toggle Auto-Reply

```bash
# Enable auto-reply
curl -s -X POST https://ai-concierge.niox.ovh/auto-reply/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

# Disable auto-reply
curl -s -X POST https://ai-concierge.niox.ovh/auto-reply/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## 📊 Monitoring

### Log Monitoring

```bash
# View application logs (if accessible)
docker logs ai-concierge-container --follow

# Check for recent webhook activity
# Monitor for:
# - "Received webhook data"
# - "Auto-reply sent successfully"
# - "Failed to send message"
```

### Health Checks

```bash
# Basic health check
curl -s https://ai-concierge.niox.ovh/ | jq .

# Auto-reply status
curl -s https://ai-concierge.niox.ovh/auto-reply/status | jq .

# WAHA session check
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default | jq '.status'
```

## 🚨 Troubleshooting

### Common Issues

#### No Auto-Reply Response

```bash
# 1. Check if auto-reply is enabled
curl -s https://ai-concierge.niox.ovh/auto-reply/status | jq '.enabled'

# 2. Check working hours
curl -s https://ai-concierge.niox.ovh/auto-reply/status | jq '.is_working_hours'

# 3. Check WAHA session status
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default | jq '.status'

# 4. Test manual reply
curl -s -X POST https://ai-concierge.niox.ovh/auto-reply/test
```

#### WAHA API Issues

```bash
# Test WAHA API connectivity
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default

# Send test message via WAHA
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  -X POST https://waha-core.niox.ovh/api/sendText \
  -H "Content-Type: application/json" \
  -d '{
    "session": "default",
    "chatId": "221773387902@c.us",
    "text": "API test message"
  }'
```

#### Phone Number Extraction Issues

```bash
# Test phone number extraction logic
python debug_phone_extraction.py

# Manual webhook test
python test_manual_reply.py
```

### Debug Commands

```bash
# Check webhook configuration
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default | jq '.config.webhooks'

# Test webhook connectivity
curl -s -X POST https://ai-concierge.niox.ovh/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "connection"}'

# Check environment variables
echo "WAHA_API_KEY: ${WAHA_API_KEY:0:10}..."
echo "WAHA_BASE_URL: $WAHA_BASE_URL"
echo "SESSION_NAME: $SESSION_NAME"
```

## 🔄 Deployment

### Update Configuration

```bash
# 1. Edit environment variables
nano .env

# 2. Commit changes
git add .env
git commit -m "Update configuration"

# 3. Push to trigger deployment
git push origin main

# 4. Monitor deployment
# Check Coolify dashboard for deployment status
```

### Rollback

```bash
# View recent commits
git log --oneline -10

# Reset to previous commit
git reset --hard HEAD~1

# Push rollback
git push --force origin main
```

## 📞 Emergency Procedures

### Disable Auto-Reply Immediately

```bash
# Quick disable via API
curl -s -X POST https://ai-concierge.niox.ovh/auto-reply/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'

# Verify disabled
curl -s https://ai-concierge.niox.ovh/auto-reply/status | jq '.enabled'
```

### Restart Application

```bash
# Via Coolify dashboard:
# 1. Navigate to ai-concierge service
# 2. Click "Restart"
# 3. Monitor logs for successful startup

# Or via API if available through Coolify
```

### WAHA Session Issues

```bash
# Check session status
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  https://waha-core.niox.ovh/api/sessions/default

# Restart WAHA session (if available)
curl -k -H "X-API-Key: $WAHA_API_KEY" \
  -X POST https://waha-core.niox.ovh/api/sessions/default/restart

# Reconfigure webhook
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

## 📈 Performance Monitoring

### Key Metrics to Monitor

- **Response Time**: Auto-reply should respond within 5 seconds
- **Success Rate**: Should be >95% for WAHA API calls
- **Webhook Processing**: Should complete within 2 seconds
- **Error Rate**: Should be <5% overall

### Monitoring Commands

```bash
# Monitor response times (in application logs)
# Look for: "Auto-reply sent successfully" or "Failed to send message"

# Check WAHA API success rate
# Monitor: WAHA API response status codes

# Track message volume
# Count: "Received webhook data" entries in logs
```

## 🛠️ Maintenance

### Regular Tasks

**Daily:**
- Check application health status
- Monitor error logs
- Verify auto-reply functionality

**Weekly:**
- Review message patterns
- Update custom replies if needed
- Check WAHA session health

**Monthly:**
- Rotate API keys if required
- Review configuration settings
- Update documentation

### Security Maintenance

```bash
# Rotate API keys (if needed)
# 1. Generate new WAHA API key
# 2. Update .env file
# 3. Redeploy application
# 4. Verify functionality

# Update dependencies
# 1. Update requirements.txt
# 2. Rebuild Docker image
# 3. Test thoroughly
# 4. Deploy to production
```

## 📚 Quick Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTO_REPLY_ENABLED` | Enable/disable auto-reply | `true` |
| `WORKING_HOURS_START` | Start of business hours | `09:00` |
| `WORKING_HOURS_END` | End of business hours | `18:00` |
| `WEEKEND_AUTO_REPLY` | Enable weekend replies | `false` |
| `WAHA_API_KEY` | WAHA API authentication | Required |
| `WAHA_BASE_URL` | WAHA API endpoint | Required |
| `SESSION_NAME` | WAHA session name | `default` |

### Default Keywords

| Pattern | Response |
|---------|----------|
| `bonjour|salut|hello` | 👋 Bonjour greeting |
| `merci|thanks` | 🙏 Thank you response |
| `urgence|urgent` | 🚨 Emergency response |
| `prix|tarif` | 💰 Pricing information |
| `horaires|hours` | 🕒 Business hours |

### Important URLs

- **Application**: https://ai-concierge.niox.ovh
- **WAHA API**: https://waha-core.niox.ovh/api
- **Health Check**: https://ai-concierge.niox.ovh/
- **Status**: https://ai-concierge.niox.ovh/auto-reply/status

---

**Remember**: Always test configuration changes in a controlled environment before applying them to production.