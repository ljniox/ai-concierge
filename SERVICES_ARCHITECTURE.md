# WhatsApp AI Concierge Service Architecture

## Overview

The WhatsApp AI Concierge Service is a comprehensive AI-powered customer service system that integrates WhatsApp Business API with Claude AI for automated response handling. This document provides detailed information about the service architecture, data flow, and configuration.

## System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp      │    │   WAHA Core     │    │   Concierge     │
│   User          │◄──►│   (WhatsApp     │◄──►│   App           │
│                 │    │   HTTP API)     │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │
                               ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Redis         │    │   Supabase      │
                       │   (Cache)       │    │   (Database)    │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │   Claude AI     │
                                                │   API           │
                                                └─────────────────┘
```

### Service Breakdown

#### 1. WAHA Core (WhatsApp HTTP API)
- **Purpose**: Provides HTTP API interface for WhatsApp Business
- **Container**: `waha-core`
- **Port**: 3000 (internal), exposed via proxy
- **Key Features**:
  - Message sending and receiving
  - Session management
  - Webhook integration
  - Media handling

#### 2. Concierge App (FastAPI Backend)
- **Purpose**: Core application logic and AI orchestration
- **Container**: `ai-concierge-app-1`
- **Port**: 8000
- **Key Components**:
  - Webhook endpoint (`/api/v1/webhook`)
  - AI orchestration (`/api/v1/orchestrate`)
  - Session management (`/api/v1/sessions/*`)
  - Health monitoring (`/health`)

#### 3. Redis (Caching Layer)
- **Purpose**: Session state management and caching
- **Container**: `redis`
- **Port**: 6379
- **Usage**:
  - User session storage
  - Rate limiting
  - Temporary data caching

#### 4. Supabase (Database)
- **Purpose**: Persistent data storage
- **Service**: Managed PostgreSQL database
- **Key Tables**:
  - `sessions` - User session data
  - `services` - Available service configurations
  - `interactions` - Message history
  - `users` - User profiles

#### 5. Claude AI (AI Service)
- **Purpose**: Natural language processing and response generation
- **API**: Anthropic Claude API
- **Model**: `glm-4.5` (custom endpoint)
- **Features**:
  - Intent recognition
  - Response generation
  - Service routing

## Detailed Service Flow

### 1. Message Reception Flow

```
WhatsApp User → WAHA Core → Concierge Webhook → Message Processing
     ↓
  Session Check → Intent Analysis → Service Routing → AI Response
     ↓
  Response Generation → WAHA Core → WhatsApp User
```

#### Step-by-Step Process:

1. **Message Reception**
   - User sends message to WhatsApp business number
   - WAHA Core receives message via WhatsApp Business API
   - WAHA Core forwards message to Concierge webhook

2. **Webhook Processing** (`/api/v1/webhook`)
   ```python
   POST /api/v1/webhook
   Headers:
     - Content-Type: application/json
     - X-Waha-Token: [verification_token]

   Body:
   {
     "session": "default",
     "message": {
       "from": "1234567890",
       "text": "Je veux des informations",
       "timestamp": "2024-01-01T10:00:00Z"
     }
   }
   ```

3. **Session Management**
   - Check Redis for existing session
   - Create new session if none exists
   - Load user context and history

4. **Intent Analysis**
   - Analyze message content using Claude AI
   - Determine user intent and required service
   - Extract relevant entities and parameters

5. **Service Routing**
   - Map intent to appropriate service:
     - `RENSEIGNEMENT` - General information
     - `CATECHESE` - Catechism services (requires authentication)
     - `CONTACT_HUMAIN` - Human agent handoff

6. **Data Retrieval**
   - Query Supabase for user data
   - Integrate with external APIs (Baserow, Google Drive)
   - Fetch relevant information based on service type

7. **Response Generation**
   - Generate AI response using Claude
   - Format response according to service requirements
   - Include relevant data and action items

8. **Message Sending**
   - Send response back to user via WAHA Core
   - Log interaction in Supabase
   - Update session state in Redis

### 2. Service-Specific Flows

#### RENSEIGNEMENT Service
```
User Query → Intent Analysis → Baserow Query → Response Generation
```

#### CATECHESE Service
```
User Query → Parent Code Verification → Student Lookup → Certificate Generation
```

#### CONTACT_HUMAIN Service
```
User Request → Human Agent Assignment → Notification → Follow-up Creation
```

## Configuration

### Environment Variables (.env)

```bash
# Application Settings
SECRET_KEY=your-secret-key-here-change-in-production
ENVIRONMENT=production
TZ=Africa/Dakar
LOG_LEVEL=INFO

# WhatsApp Integration
WAHA_BASE_URL=https://waha-core.niox.ovh
WAHA_API_TOKEN=28C5435535C2487DAFBD1164B9CD4E34
WAHA_API_KEY=28C5435535C2487DAFBD1164B9CD4E34
SESSION_NAME=default

# Webhook Configuration
WEBHOOK_URL=http://ai-concierge-app-1:8000/api/v1/webhook
WEBHOOK_VERIFY_TOKEN=2MqxVV-vtba9Ha2vSn7CWu4qPGfdkEGbS8DzVv6gFaw

# AI Configuration
ANTHROPIC_AUTH_TOKEN=0ee8c49b8ea94d7e84bf747d4286fecd.SNHHi7BSHuxTofkf
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_MODEL=glm-4.5

# Database Configuration
SUPABASE_URL=https://ixzpejqzxvxpnkbznqnj.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# External Services
BASEROW_URL=https://sdbaserow.3xperts.tech
BASEROW_AUTH_KEY=q80kPF01T0zp9gXehV5bYennCIGrqQwk
FIRECRAWL_API_KEY=fc-a76902096b474a5090e1935d221df87b

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Performance Settings
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT_SECONDS=30
SESSION_TIMEOUT_MINUTES=30
```

### Docker Configuration

#### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: ai-concierge-app-1
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - concierge-network

  redis:
    image: redis:alpine
    container_name: ai-concierge-redis
    ports:
      - "6379:6379"
    networks:
      - concierge-network

networks:
  concierge-network:
    driver: bridge
```

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy environment file
COPY .env .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### API Endpoints

#### Webhook Endpoint
```
POST /api/v1/webhook
Description: Receive WhatsApp messages from WAHA
Authentication: X-Waha-Token header
```

#### Orchestration Endpoint
```
POST /api/v1/orchestrate
Description: Process AI requests and generate responses
Authentication: JWT token
```

#### Session Management
```
GET    /api/v1/sessions/{session_id}
POST   /api/v1/sessions/{session_id}
DELETE /api/v1/sessions/{session_id}
```

#### Health Check
```
GET /health
Description: System health monitoring
```

### Service Configuration

#### Service Types
```python
class ServiceType(Enum):
    RENSEIGNEMENT = "renseignement"
    CATECHESE = "catechese"
    CONTACT_HUMAIN = "contact_humain"
```

#### Service Routing Logic
```python
def route_service(user_input: str, context: dict) -> ServiceType:
    # Analyze user input using Claude AI
    intent = analyze_intent(user_input)

    # Route based on intent and context
    if intent == "information":
        return ServiceType.RENSEIGNEMENT
    elif intent == "catechism":
        return ServiceType.CATECHESE
    elif intent == "human_agent":
        return ServiceType.CONTACT_HUMAIN
```

## Deployment and Operations

### Container Management

#### Starting Services
```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Restart specific service
docker compose restart app
```

#### Health Checks
```bash
# Check application health
curl http://localhost:8000/health

# Check webhook accessibility
curl -X POST http://localhost:8000/api/v1/webhook \
  -H "Content-Type: application/json" \
  -H "X-Waha-Token: your-token" \
  -d '{"test": true}'
```

### Monitoring and Logging

#### Log Levels
- **INFO**: General operational information
- **WARN**: Warning conditions
- **ERROR**: Error conditions
- **DEBUG**: Detailed debugging information

#### Key Metrics
- Message processing time
- Response success rate
- Session duration
- API call latency

### Security Considerations

#### API Security
- JWT token authentication for protected endpoints
- Webhook verification tokens
- Rate limiting per user
- Input validation and sanitization

#### Data Security
- Environment variable encryption
- Database connection encryption
- Secure token storage
- Regular key rotation

## Troubleshooting

### Common Issues

#### 1. Webhook Not Receiving Messages
**Symptoms**: Messages not being processed
**Solutions**:
- Check WAHA webhook configuration
- Verify webhook URL accessibility
- Confirm verification token matches

#### 2. AI API Authentication Failures
**Symptoms**: 401 Unauthorized errors
**Solutions**:
- Verify ANTHROPIC_AUTH_TOKEN is correct
- Check API endpoint URL
- Ensure proper Bearer token format

#### 3. Database Connection Issues
**Symptoms**: Service unable to access data
**Solutions**:
- Check SUPABASE_URL and credentials
- Verify network connectivity
- Confirm database schema exists

#### 4. Redis Connection Problems
**Symptoms**: Session management failures
**Solutions**:
- Check REDIS_URL format
- Verify Redis container is running
- Confirm network accessibility

### Debug Commands

```bash
# Check container status
docker compose ps

# View application logs
docker compose logs app

# Test database connection
docker exec app python -c "from src.utils.database import test_connection; test_connection()"

# Test Redis connection
docker exec app python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

## Performance Optimization

### Caching Strategy
- Redis for session data
- Database query caching
- API response caching

### Rate Limiting
- Per-user rate limiting
- API endpoint throttling
- Concurrent request limits

### Scalability Considerations
- Horizontal scaling for app containers
- Redis cluster for large deployments
- Database connection pooling
- Load balancing configuration

## Future Enhancements

### Planned Features
- Multi-language support
- Advanced analytics dashboard
- Integration with additional messaging platforms
- Enhanced AI capabilities
- Mobile application interface

### Architecture Improvements
- Microservices architecture
- Event-driven messaging
- Advanced monitoring and alerting
- Automated scaling and deployment