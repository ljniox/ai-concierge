# Quick Start Guide: Automatic Account Creation System

**Feature**: Automatic Account Creation Based on Phone Number
**Date**: 2025-01-25
**Version**: 1.0

## Overview

This guide provides step-by-step instructions for setting up and deploying the automatic account creation system for catechism parents. The system enables automatic account creation when parents contact the service via WhatsApp or Telegram.

## Prerequisites

### System Requirements
- Python 3.11+ with type hints support
- Supabase account with PostgreSQL database
- Redis server for session caching
- WhatsApp Business API access (via WAHA)
- Telegram Bot API token
- Docker and Docker Compose for deployment

### External Services
- **Supabase**: Database and authentication
- **Redis**: Session caching and rate limiting
- **WAHA**: WhatsApp Business API integration
- **Telegram Bot API**: Telegram integration
- **Catechism Database**: Parent records lookup

## Environment Setup

### 1. Clone and Setup Repository
```bash
git clone <repository-url>
cd ai-concierge
git checkout 003-sur-la-base
```

### 2. Configure Environment Variables
```bash
# Copy template and configure
cp .env.template .env

# Edit .env with your configuration
nano .env
```

### 3. Required Environment Variables
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# WhatsApp Integration
WAHA_BASE_URL=https://your-waha-instance.com
WAHA_API_TOKEN=your-waha-api-token
WHATSAPP_APP_SECRET=your-whatsapp-app-secret
WHATSAPP_VERIFY_TOKEN=your-verify-token

# Telegram Integration
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Application Settings
WEBHOOK_URL=https://your-domain.com/api/v1/webhook
JWT_SECRET_KEY=your-jwt-secret-key
LOG_LEVEL=INFO
```

## Database Setup

### 1. Initialize Supabase Database
```sql
-- Connect to your Supabase SQL editor and run:

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create tables using the migration script
-- (See: /scripts/migrations/001_create_account_tables.sql)
```

### 2. Run Database Migration
```bash
# Run the database migration script
python -m scripts.migrations.run_migration 001_create_account_tables.sql
```

### 3. Insert Default Roles
```sql
-- Default system roles are automatically inserted during migration
-- Verify roles were created:
SELECT * FROM user_roles WHERE is_system_role = true;
```

## Redis Configuration

### 1. Setup Redis Server
```bash
# Using Docker
docker run -d --name redis \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine

# Or install locally
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. Test Redis Connection
```bash
# Test Redis connection
redis-cli ping
# Expected response: PONG
```

## WhatsApp Integration

### 1. Setup WAHA Instance
```bash
# Using Docker Compose (recommended)
docker-compose up -d waha-core

# Or manual setup
docker run -d \
  --name waha-core \
  -p 3000:3000 \
  --env WHATSAPP_APP_SECRET=your-secret \
  devlikeapro/waha-core
```

### 2. Configure WhatsApp Business API
1. Create a WhatsApp Business account on Meta Business Suite
2. Set up webhook endpoint: `https://your-domain.com/api/v1/webhooks/whatsapp`
3. Configure webhook verification token
4. Get your app secret for signature verification

### 3. Test WhatsApp Integration
```bash
# Test WAHA connection
curl -H "Authorization: Bearer $WAHA_API_TOKEN" \
  "$WAHA_BASE_URL/api/sessions"

# Expected response: List of WhatsApp sessions
```

## Telegram Integration

### 1. Create Telegram Bot
1. Contact @BotFather on Telegram
2. Create new bot with `/newbot`
3. Get your bot token
4. Set webhook URL: `https://your-domain.com/api/v1/webhooks/telegram`

### 2. Test Telegram Integration
```bash
# Test bot connection
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Expected response: Bot information
```

## Application Deployment

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install additional requirements for this feature
pip install python-phonenumbers python-jose fastapi-users
```

### 2. Run Database Migrations
```bash
# Run all pending migrations
python scripts/migrations/migrate.py

# Verify migration status
python scripts/migrations/status.py
```

### 3. Start Application
```bash
# Using Docker Compose (recommended)
docker-compose up -d ai-concierge-app

# Or run directly
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify Health Check
```bash
# Check application health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "webhook_security": {"status": "healthy"}
  }
}
```

## Testing the System

### 1. Test Phone Number Validation
```bash
# Test phone validation endpoint
curl -X POST http://localhost:8000/api/v1/utils/validate-phone \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+221 76 500 55 55",
    "country_code": "SN"
  }'

# Expected response:
{
  "is_valid": true,
  "normalized_phone": "+221765005555",
  "country_code": "SN",
  "carrier": "Orange",
  "number_type": "MOBILE"
}
```

### 2. Test WhatsApp Webhook
```bash
# Simulate WhatsApp webhook
curl -X POST http://localhost:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=your-signature" \
  -d '{
    "object": "whatsapp",
    "entry": [{
      "id": "123456789",
      "changes": [{
        "value": {
          "messaging_product": "whatsapp",
          "contacts": [{
            "profile": {"name": "Test Parent"},
            "wa_id": "221765005555"
          }],
          "messages": [{
            "from": "221765005555",
            "id": "msg123",
            "timestamp": "1695140642",
            "text": {"body": "Bonjour"}
          }]
        }
      }]
    }]
  }'
```

### 3. Test Telegram Webhook
```bash
# Simulate Telegram webhook
curl -X POST http://localhost:8000/api/v1/webhooks/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "update_id": 123456789,
    "message": {
      "message_id": 123,
      "from": {
        "id": 987654321,
        "first_name": "Test Parent"
      },
      "chat": {
        "id": 987654321,
        "type": "private"
      },
      "date": 1695140642,
      "text": "Bonjour"
    }
  }'
```

## Monitoring and Logging

### 1. Application Logs
```bash
# View application logs
docker-compose logs -f ai-concierge-app

# Or if running directly
tail -f logs/application.log
```

### 2. Redis Monitoring
```bash
# Monitor Redis
redis-cli monitor

# Check Redis memory usage
redis-cli info memory
```

### 3. Database Monitoring
```bash
# Check database connections
curl -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  "$SUPABASE_URL/rest/v1/health"

# Monitor slow queries in Supabase dashboard
```

## Common Issues and Solutions

### Issue 1: WhatsApp Webhook Not Verified
**Problem**: WhatsApp returns 404 or 500 for webhook verification
**Solution**:
1. Verify webhook URL is accessible
2. Check verify token matches WhatsApp configuration
3. Ensure your server can receive HTTPS requests

### Issue 2: Phone Number Validation Fails
**Problem**: Invalid phone numbers for Senegal
**Solution**:
1. Check phone format: +221 7X XXX XX XX
2. Verify country code is set to "SN"
3. Test with known valid numbers

### Issue 3: Database Connection Errors
**Problem**: Cannot connect to Supabase
**Solution**:
1. Verify Supabase URL and keys in .env
2. Check network connectivity
3. Ensure RLS policies allow access

### Issue 4: Redis Connection Fails
**Problem**: Cannot connect to Redis
**Solution**:
1. Verify Redis is running: `redis-cli ping`
2. Check Redis URL in .env
3. Verify firewall settings

### Issue 5: Session Expiration Issues
**Problem**: Sessions expiring too quickly
**Solution**:
1. Check Redis TTL settings
2. Verify session timeout configuration
3. Check system time synchronization

## Performance Tuning

### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_user_accounts_phone_normalized
ON user_accounts(normalized_phone);

CREATE INDEX CONCURRENTLY idx_user_sessions_platform_user
ON user_sessions(platform, platform_user_id);
```

### 2. Redis Configuration
```bash
# Optimize Redis for session storage
redis-cli CONFIG SET maxmemory 256mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET save "900 1 300 10 60 10000"
```

### 3. Application Configuration
```bash
# Optimize worker processes
export WORKERS=4
export WORKER_CONNECTIONS=1000
export MAX_REQUESTS=1000
export MAX_REQUESTS_JITTER=100
```

## Security Considerations

### 1. Environment Variables
```bash
# Secure .env file
chmod 600 .env

# Never commit .env to version control
echo ".env" >> .gitignore
```

### 2. API Security
```bash
# Use HTTPS in production
export FORCE_HTTPS=true

# Set secure headers
export SECURITY_HEADERS=true
```

### 3. Database Security
```sql
-- Enable Row Level Security
ALTER TABLE user_accounts ENABLE ROW LEVEL SECURITY;

-- Create appropriate RLS policies
CREATE POLICY "Users can view own accounts" ON user_accounts
  FOR SELECT USING (auth.uid()::text = id::text);
```

## Troubleshooting Checklist

### Pre-deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Redis server running
- [ ] WhatsApp webhook configured
- [ ] Telegram bot configured
- [ ] SSL certificates installed
- [ ] Health checks passing

### Post-deployment Verification
- [ ] Application responds to health checks
- [ ] Webhooks receive and process messages
- [ ] Phone number validation working
- [ ] Account creation functioning
- [ ] Sessions persist correctly
- [ ] Audit logs are created
- [ ] Performance metrics are collected

## Support and Documentation

### Getting Help
- **Documentation**: Check `/docs` directory
- **API Reference**: `/docs/api.md`
- **Architecture**: `/docs/architecture.md`
- **Troubleshooting**: `/docs/troubleshooting.md`

### Monitoring Dashboards
- **Application Metrics**: Grafana dashboard
- **Database Performance**: Supabase dashboard
- **Redis Performance**: Redis monitoring tools

---

**Quick Start Complete**: Your automatic account creation system is now ready to process parent registrations via WhatsApp and Telegram!

**Next Steps**:
1. Monitor system performance
2. Set up alerting for critical issues
3. Configure backup and disaster recovery
4. Plan for scaling based on usage

**Support**: For technical issues, contact the development team or check the troubleshooting documentation.