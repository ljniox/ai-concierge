# AI Concierge System Architecture Documentation

**Version**: 2.0 - Production Ready
**Last Updated**: October 4, 2025
**Purpose**: Complete system architecture guide for development, deployment, and troubleshooting

## 📋 Overview

The AI Concierge system is a multi-platform conversational AI service that integrates with WhatsApp and Telegram to provide intelligent responses for the Service Diocésain de la Catéchèse (SDB). The system features a multi-provider AI architecture with automatic failover, load balancing, and comprehensive monitoring.

## 🏗️ System Architecture

### High-Level Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │    Telegram     │    │   Web Client    │
│   (WAHA)        │    │   Bot API       │    │   (Optional)    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   Caddy Reverse Proxy     │
                    │   (TLS Termination)      │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │   AI Concierge API        │
                    │   (FastAPI)               │
                    │   Container:              │
                    │   ai-concierge-app-1      │
                    │   IP: 172.18.0.3:8000     │
                    └─────────────┬─────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│   Supabase      │    │     Redis       │    │  AI Providers   │
│   (PostgreSQL)  │    │   (Session)     │    │  (Multi-API)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Container Network Architecture

**Docker Network Configuration:**
- **Network Name**: `ai-concierge_default`
- **Gateway**: `172.18.0.1`
- **Subnet**: `172.18.0.0/16`

**Container IP Mapping:**
- `ai-concierge-app-1`: `172.18.0.3:8000` (Main API)
- `redis`: `172.18.0.2:6379` (Session Cache)
- `waha-core`: External service at `waha-core.niox.ovh`

## 🔧 Core Services

### 1. AI Concierge API (FastAPI)

**Location**: `src/main.py`
**Container**: `ai-concierge-app-1`
**Port**: `8000` (internal) / `443` (external via Caddy)

**Key Endpoints:**
- `/api/v1/webhook` - WhatsApp message handling
- `/api/v1/telegram/webhook` - Telegram message handling
- `/api/v1/orchestrate` - AI response orchestration
- `/api/v1/sessions/*` - Session management
- `/health` - System health monitoring
- `/docs` - API documentation

**Middleware Stack:**
1. **CORS Middleware** - Cross-origin requests
2. **Request Logging** - Structured JSON logging
3. **Exception Handler** - Global error handling

### 2. Multi-Provider AI Service

**Location**: `src/services/claude_service.py`
**Providers**: Anthropic (GLM), Gemini, OpenRouter

**Features:**
- **Round-robin API key rotation** for load balancing
- **Automatic failover** between providers
- **Provider-specific payload formatting**
- **Credit monitoring** for OpenRouter
- **Thread-safe operations**

**Provider Configuration:**
```python
# Environment Variables
AI_PROVIDER=openrouter                    # Default provider
ENABLE_ANTHROPIC=true                     # Enable Anthropic
ENABLE_GEMINI=true                        # Enable Gemini
ENABLE_OPENROUTER=true                    # Enable OpenRouter

# API Keys (Round-robin)
GEMINI_API_KEY_1=xxx
GEMINI_API_KEY_2=xxx
GEMINI_API_KEY_3=xxx
OPENROUTER_API_KEY_1=xxx
OPENROUTER_API_KEY_2=xxx
```

**Load Balancing Logic:**
```python
class APIKeyManager:
    """Thread-safe round-robin API key rotation"""

    def get_next_key(self) -> Optional[str]:
        with self.lock:
            key = self.api_keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.api_keys)
            return key
```

### 3. Message Processing Pipeline

**Flow: WhatsApp/Telegram → AI Response**

```
1. Message Received
   ↓
2. User Validation/Creation
   ↓
3. Session Management
   ↓
4. Service Detection (RENSEIGNEMENT/CATECHESE/CONTACT_HUMAIN)
   ↓
5. AI Provider Selection
   ↓
6. API Call (with Round-robin)
   ↓
7. Response Formatting
   ↓
8. Send Response
```

**Key Components:**

**User Model** (`src/models/user.py`):
- Supports WhatsApp phone numbers (E.164 format)
- Supports Telegram identifiers (`telegram_<user_id>`)
- Phone number validation with platform detection

**Session Service** (`src/services/session_service.py`):
- Redis-backed session storage
- 30-minute session timeout
- Context preservation across conversations

**Interaction Service** (`src/services/interaction_service.py`):
- Message orchestration and routing
- Emergency detection and human handoff
- Response formatting for different platforms

## 🌐 External Integrations

### 1. WhatsApp Integration (WAHA)

**Base URL**: `https://waha-core.niox.ovh`
**API Token**: `28C5435535C2487DAFBD1164B9CD4E34`
**Webhook**: `/api/v1/webhook`

**Message Types Supported:**
- Text messages
- Images (with OCR)
- Documents
- Audio messages
- Location data

### 2. Telegram Integration

**Bot Token**: `8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus`
**Webhook**: `https://cate.sdb-dkr.ovh/api/v1/telegram/webhook`

**Features:**
- Full Markdown support
- Command handling (`/start`, `/help`, `/services`, `/contact`, `/cancel`)
- Photo and document processing
- Callback query support

**User Identification:**
- Format: `telegram_<user_id>`
- Example: `telegram_695065578`

### 3. AI Provider APIs

**Anthropic (GLM Models):**
- Base URL: `https://api.z.ai/api/anthropic`
- Models: `glm-4.5-air`, `glm-4.6`
- Auth: Bearer token

**Google Gemini:**
- Base URL: `https://generativelanguage.googleapis.com`
- Model: `gemini-1.5-flash`
- Auth: API key in query parameter

**OpenRouter:**
- Base URL: `https://openrouter.ai/api/v1`
- Model: `gpt-oss-20b` (free tier)
- Auth: Bearer token
- Credit monitoring available

## 🗄️ Data Architecture

### 1. Supabase (PostgreSQL)

**Connection**: `https://ixzpejqzxvxpnkbznqnj.supabase.co`
**Tables:**
- `users` - User profiles and metadata
- `sessions` - Conversation sessions
- `interactions` - Message history and responses
- `temporary_pages` - Temporary access pages

**Key Features:**
- Row Level Security (RLS)
- Automatic backups
- Real-time subscriptions
- RESTful API

### 2. Redis (Session Cache)

**Connection**: `redis://redis:6379/0`
**Usage:**
- Session state management
- Conversation context caching
- Rate limiting
- Temporary data storage

**Data Structure:**
```
session:{session_id} -> {
    "user_id": "uuid",
    "context": [...],
    "last_activity": "timestamp",
    "service_type": "RENSEIGNEMENT|CATECHESE|CONTACT_HUMAIN"
}
```

### 3. Baserow Integration

**Base URL**: `https://sdbaserow.3xperts.tech`
**Auth Token**: `q80kPF01T0zp9gXehV5bYennCIGrqQwk`

**Key Tables:**
- `Catechumenes` (ID: 575) - Student information
- `Parents` (ID: 572) - Parent contacts
- `Inscriptions` (ID: 574) - Enrollment records
- `Notes` (ID: 576) - Student grades

## 🔒 Security Architecture

### 1. Authentication & Authorization

**JWT Tokens:**
- Secret: `JWT_SECRET_KEY`
- Algorithm: `HS256`
- Expiration: 30 minutes

**API Keys:**
- Environment variable storage
- Rotation support
- Provider-specific validation

### 2. Webhook Security

**WhatsApp:**
- Hub signature verification
- Token-based validation

**Telegram:**
- Webhook URL validation
- Bot token authentication

### 3. Network Security

**Caddy Configuration** (`/etc/caddy/Caddyfile`):
```caddy
cate.sdb-dkr.ovh {
    reverse_proxy 172.18.0.3:8000 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    header {
        Strict-Transport-Security "max-age=31536000; includeSubdomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }

    tls {
        protocols tls1.2 tls1.3
    }
}
```

## 📊 Monitoring & Logging

### 1. Structured Logging

**Format**: JSON
**Logger**: `structlog`
**Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Log Structure:**
```json
{
    "timestamp": "2025-10-04T12:00:00Z",
    "level": "INFO",
    "message": "telegram_message_received",
    "chat_id": 695065578,
    "user_id": "telegram_695065578",
    "message_length": 25,
    "service": "openrouter"
}
```

### 2. Health Monitoring

**Endpoint**: `/health`
**Checks:**
- Database connectivity (Supabase)
- Redis connectivity
- AI provider availability
- External service status

**Response Format:**
```json
{
    "status": "healthy",
    "timestamp": "2025-10-04T12:00:00Z",
    "services": {
        "database": "healthy",
        "redis": "healthy",
        "ai_providers": {
            "anthropic": "healthy",
            "gemini": "healthy",
            "openrouter": "healthy"
        }
    },
    "version": "1.0.0"
}
```

### 3. Performance Metrics

**Key Indicators:**
- Request latency (p50, p95, p99)
- AI provider response times
- Error rates by provider
- API key usage distribution
- Message processing throughput

## 🚀 Deployment Architecture

### 1. Docker Configuration

**Compose File**: `docker-compose.yml`
**Services:**
- `ai-concierge-app-1` - Main application
- `redis` - Session cache
- `nginx`/`caddy` - Reverse proxy

**Container Details:**
```yaml
ai-concierge-app-1:
  build: .
  environment:
    - REDIS_URL=redis://redis:6379/0
    - SUPABASE_URL=${SUPABASE_URL}
    - AI_PROVIDER=openrouter
  networks:
    - ai-concierge_default
  restart: unless-stopped
```

### 2. Environment Configuration

**File**: `.env`
**Critical Variables:**
```bash
# Database
SUPABASE_URL=https://ixzpejqzxvxpnkbznqnj.supabase.co
SUPABASE_PASSWORD=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx

# AI Providers
AI_PROVIDER=openrouter
ENABLE_ANTHROPIC=true
ENABLE_GEMINI=true
ENABLE_OPENROUTER=true

# API Keys
ANTHROPIC_AUTH_TOKEN=xxx
GEMINI_API_KEY_1=xxx
GEMINI_API_KEY_2=xxx
OPENROUTER_API_KEY_1=xxx
OPENROUTER_API_KEY_2=xxx

# External Services
WEBHOOK_URL=http://ai-concierge-app-1:8000/api/v1/webhook
TELEGRAM_BOT_TOKEN=xxx
EXTERNAL_BASE_URL=https://cate.sdb-dkr.ovh
```

### 3. SSL/TLS Configuration

**Provider**: Let's Encrypt (via Caddy)
**Domains**:
- `cate.sdb-dkr.ovh` - Main API endpoint
- `waha-core.niox.ovh` - WhatsApp service

**Certificate Auto-renewal**: Enabled

## 🔄 Service Types & Logic

### 1. RENSEIGNEMENT (Information Service)

**Purpose**: General information about catechism programs
**Triggers**: General questions, information requests
**Response Style**: Informative, helpful
**Data Sources**: Baserow, static information

### 2. CATECHESE (Catechism Service)

**Purpose**: Student-specific information access
**Authentication**: `code_parent` required
**Features**:
- Grade viewing
- Schedule access
- Certificate downloads
- Progress tracking

**Security**: Parent code validation before data access

### 3. CONTACT_HUMAIN (Human Handoff)

**Purpose**: Connect to human agents
**Triggers**:
- Explicit requests
- Complex issues
- Emergency detection
- Failed AI responses

**Process**:
1. Acknowledge user request
2. Collect contact information
3. Create notification for human agents
4. Provide estimated response time

## 🛠️ Development Workflow

### 1. Local Development

**Setup:**
```bash
# Clone repository
git clone <repository>
cd ai-concierge

# Copy environment template
cp .env.example .env
# Edit .env with local values

# Build and run
docker-compose up --build
```

**Testing:**
```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Test Telegram webhook
curl -X POST http://localhost:8000/api/v1/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "test", "from": {"id": 123}, "chat": {"id": 123}}}'
```

### 2. Production Deployment

**Process:**
1. Update environment variables
2. Build new Docker image
3. Run database migrations
4. Deploy with zero downtime
5. Verify health endpoints
6. Monitor error rates

**Commands:**
```bash
# Deploy new version
docker-compose pull
docker-compose up -d --no-deps ai-concierge-app-1

# Check logs
docker logs ai-concierge-app-1 -f

# Verify health
curl https://cate.sdb-dkr.ovh/health
```

## 🔧 Troubleshooting Guide

### 1. Common Issues

**Telegram Messages Not Responding:**
```bash
# Check webhook status
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo

# Check container logs
docker logs ai-concierge-app-1 -f | grep telegram

# Verify Caddy configuration
sudo caddy validate --config /etc/caddy/Caddyfile
```

**AI Provider Errors:**
```bash
# Check provider status
curl https://cate.sdb-dkr.ovh/health

# Test API keys
python -c "from src.services.claude_service import ClaudeService; import asyncio; asyncio.run(ClaudeService().test_providers())"

# Check environment variables
docker exec ai-concierge-app-1 env | grep AI_
```

**Database Connection Issues:**
```bash
# Test Supabase connection
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"

# Check Redis
docker exec redis redis-cli ping
```

### 2. Performance Issues

**High Response Times:**
```bash
# Check AI provider latency
docker logs ai-concierge-app-1 | grep "api_request_duration"

# Monitor Redis performance
docker exec redis redis-cli info stats

# Check database query performance
# (Add query logging to Supabase dashboard)
```

**Memory Issues:**
```bash
# Check container resources
docker stats ai-concierge-app-1

# Monitor Redis memory usage
docker exec redis redis-cli info memory
```

### 3. Debug Mode

**Enable Debug Logging:**
```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or update .env
echo "LOG_LEVEL=DEBUG" >> .env

# Restart container
docker-compose restart ai-concierge-app-1
```

**Detailed Request Tracing:**
```bash
# Follow logs with request IDs
docker logs ai-concierge-app-1 -f | grep "request_id"

# Monitor specific user session
docker logs ai-concierge-app-1 -f | grep "telegram_<user_id>"
```

## 📈 Scaling Architecture

### 1. Horizontal Scaling

**Application Layer:**
- Multiple API containers behind load balancer
- Shared Redis session store
- Database connection pooling

**AI Provider Layer:**
- Round-robin API key distribution
- Provider-level load balancing
- Automatic failover

### 2. Caching Strategy

**Response Caching:**
- Redis for common queries
- TTL-based expiration
- Cache invalidation on updates

**Session Caching:**
- User conversation context
- Service type persistence
- Session recovery

### 3. Monitoring for Scale

**Metrics Collection:**
- Request per minute tracking
- AI provider latency monitoring
- Error rate alerting
- Resource utilization tracking

## 📋 Configuration Reference

### 1. Complete .env Template

```bash
# ===========================================
# DATABASE CONFIGURATION
# ===========================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PASSWORD=your-password
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# ===========================================
# REDIS CONFIGURATION
# ===========================================
REDIS_URL=redis://redis:6379/0

# ===========================================
# AI PROVIDERS
# ===========================================
AI_PROVIDER=openrouter
ENABLE_ANTHROPIC=true
ENABLE_GEMINI=true
ENABLE_OPENROUTER=true

# ===========================================
# ANTHROPIC CONFIGURATION
# ===========================================
ANTHROPIC_AUTH_TOKEN=your-token
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.5-air
ANTHROPIC_DEFAULT_SONNET_MODEL=glm-4.6
ANTHROPIC_DEFAULT_OPUS_MODEL=glm-4.6

# ===========================================
# GEMINI CONFIGURATION
# ===========================================
GEMINI_API_KEY_1=your-key-1
GEMINI_API_KEY_2=your-key-2
GEMINI_API_KEY_3=your-key-3
GEMINI_BASE_URL=https://generativelanguage.googleapis.com
GEMINI_MODEL=gemini-1.5-flash

# ===========================================
# OPENROUTER CONFIGURATION
# ===========================================
OPENROUTER_API_KEY_1=your-key-1
OPENROUTER_API_KEY_2=your-key-2
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=gpt-oss-20b

# ===========================================
# WHATSAPP CONFIGURATION
# ===========================================
WEBHOOK_URL=http://ai-concierge-app-1:8000/api/v1/webhook
WAHA_BASE_URL=https://waha-core.niox.ovh
WAHA_API_TOKEN=your-waha-token

# ===========================================
# TELEGRAM CONFIGURATION
# ===========================================
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/v1/telegram/webhook

# ===========================================
# APPLICATION CONFIGURATION
# ===========================================
ENVIRONMENT=production
TZ=Africa/Dakar
LOG_LEVEL=INFO
PORT=8000

# ===========================================
# SECURITY
# ===========================================
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# ===========================================
# PERFORMANCE
# ===========================================
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT_SECONDS=30
SESSION_TIMEOUT_MINUTES=30
MAX_RETRY_ATTEMPTS=3

# ===========================================
# EXTERNAL SERVICES
# ===========================================
EXTERNAL_BASE_URL=https://your-domain.com
CONCIERGE_API_URL=http://ai-concierge-app-1:8000
CONCIERGE_HEALTH_URL=http://ai-concierge-app-1:8000/health

# ===========================================
# BASEROW INTEGRATION
# ===========================================
BASEROW_URL=https://sdbaserow.3xperts.tech
BASEROW_AUTH_KEY=your-baserow-token

# ===========================================
# MINIO STORAGE
# ===========================================
MINIO_ENDPOINT=https://minio.setu.ovh
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=your-minio-key
MINIO_BUCKET_NAME=ai-concierge
MINIO_SECURE=true

# ===========================================
# FIRECRAWL MCP
# ===========================================
FIRECRAWL_API_KEY=your-firecrawl-key
```

### 2. Container Health Checks

**Dockerfile Configuration:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**Health Check Endpoint:**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": await check_all_services()
    }
```

## 🎯 Best Practices

### 1. Code Quality

- **Type Hints**: All functions should have proper type annotations
- **Error Handling**: Comprehensive try-catch blocks with logging
- **Documentation**: Inline docs for all public methods
- **Testing**: Unit tests for business logic, integration tests for APIs

### 2. Security

- **Environment Variables**: Never commit sensitive data
- **API Keys**: Regular rotation and monitoring
- **Input Validation**: Sanitize all user inputs
- **Rate Limiting**: Implement per-user rate limits

### 3. Performance

- **Async/Await**: Use async patterns for I/O operations
- **Connection Pooling**: Reuse database and HTTP connections
- **Caching**: Cache frequently accessed data
- **Monitoring**: Track performance metrics continuously

### 4. Operations

- **Structured Logging**: Use JSON format for log aggregation
- **Health Checks**: Implement comprehensive health monitoring
- **Graceful Shutdown**: Handle SIGTERM properly
- **Configuration**: Externalize all configuration

## 🔄 Future Architecture Considerations

### 1. Microservices Migration

**Potential Split:**
- `auth-service` - User authentication and management
- `conversation-service` - Message processing and AI orchestration
- `notification-service` - WhatsApp/Telegram integrations
- `analytics-service` - Usage tracking and reporting

### 2. Event-Driven Architecture

**Components:**
- Message queue (RabbitMQ/Apache Kafka)
- Event sourcing for conversation history
- Async processing for non-critical operations
- Real-time notifications via WebSockets

### 3. Advanced AI Features

**Enhancements:**
- Multi-language support
- Context-aware responses
- Sentiment analysis
- Intent recognition
- Custom model fine-tuning

### 4. High Availability

**Improvements:**
- Multi-region deployment
- Database replication
- Automatic failover
- Disaster recovery procedures

---

## 📞 Emergency Contacts

**Technical Lead**: Gust-IA System
**Admin Notifications**: +221 76 500 5555 (WhatsApp)
**Documentation**: This file + `execution_logs/` directory

## 📚 Additional Resources

- **API Documentation**: https://cate.sdb-dkr.ovh/docs
- **Project Board**: Link to project management
- **Code Repository**: Link to Git repository
- **Monitoring Dashboard**: Link to observability platform

---

*This documentation is maintained as part of the AI Concierge project. For questions or updates, please contact the development team or create an issue in the project repository.*