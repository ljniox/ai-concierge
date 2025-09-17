# Quickstart: WhatsApp AI Concierge Service

**Branch**: `001-projet-concierge-ia` | **Date**: 2025-09-16

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Supabase account
- WAHA instance
- WhatsApp Business API access

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# WAHA Configuration
WAHA_BASE_URL=https://your-waha-instance.com
WAHA_API_TOKEN=your-waha-token

# Claude AI Configuration
ANTHROPIC_API_KEY=sk-ant-api03-your-claude-api-key

# Application Configuration
SECRET_KEY=your-secret-key-here
ENVIRONMENT=development
TZ=Africa/Dakar

# Redis Configuration (optional for caching)
REDIS_URL=redis://localhost:6379/0
```

### 2. Database Setup

#### Supabase Schema

Execute these SQL commands in your Supabase SQL editor:

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create core tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_keywords TEXT[] NOT NULL,
    trigger_type VARCHAR(20) NOT NULL CHECK (trigger_type IN ('KEYWORD', 'PHONE_ROLE', 'INTRINSIC_ID')),
    processing_type VARCHAR(20) NOT NULL CHECK (processing_type IN ('AI', 'HUMAN', 'HYBRID')),
    artifact_types TEXT[] NOT NULL,
    intrinsic_id_field VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_id UUID REFERENCES services(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'COMPLETED', 'EXPIRED', 'HANDED_OFF')),
    state JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('USER', 'SYSTEM', 'AI')),
    content TEXT,
    media_url TEXT,
    media_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    content TEXT,
    file_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_interactions_session ON interactions(session_id);
CREATE INDEX idx_interactions_created ON interactions(created_at);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);

-- Insert default services
INSERT INTO services (name, display_name, description, trigger_keywords, trigger_type, processing_type, artifact_types, intrinsic_id_field) VALUES
('RENSEIGNEMENT', 'Renseignements', 'Service d''information générale', ARRAY['infos', 'renseignement', 'information'], 'KEYWORD', 'AI', ARRAY['response'], NULL),
('CATECHESE', 'Catéchèse', 'Service de catéchèse', ARRAY['catechese', 'catéchèse', 'cours'], 'INTRINSIC_ID', 'AI', ARRAY['response', 'document'], 'code_parent'),
('CONTACT_HUMAIN', 'Contact Humain', 'Service de contact avec un agent', ARRAY['humain', 'agent', 'james', 'parler'], 'KEYWORD', 'HUMAN', ARRAY['ticket'], NULL);

-- Create service contexts table
CREATE TABLE service_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_id UUID UNIQUE NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    system_prompt TEXT NOT NULL,
    service_prompts JSONB DEFAULT '{}',
    validation_rules JSONB DEFAULT '{}',
    required_fields TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default service contexts
INSERT INTO service_contexts (service_id, system_prompt, service_prompts, required_fields) VALUES
(
    (SELECT id FROM services WHERE name = 'RENSEIGNEMENT'),
    'Tu es un assistant IA pour le service de renseignements. Réponds aux questions générales avec précision et courtoisie.',
    '{"welcome": "Bonjour ! Je suis votre assistant pour les renseignements généraux. Comment puis-je vous aider ?", "goodbye": "Au revoir ! N''hésitez pas à revenir si vous avez d''autres questions."}',
    ARRAY['sujet']
),
(
    (SELECT id FROM services WHERE name = 'CATECHESE'),
    'Tu es un assistant spécialisé dans la catéchèse. Tu dois toujours demander le code parent avant de fournir des informations spécifiques.',
    '{"welcome": "Bonjour ! Bienvenue au service de catéchèse. Pour vous aider, j''ai besoin de votre code parent.", "code_prompt": "Quel est votre code parent ?", "invalid_code": "Ce code parent n''est pas valide. Veuillez vérifier et réessayer."}',
    ARRAY['code_parent', 'sujet']
),
(
    (SELECT id FROM services WHERE name = 'CONTACT_HUMAIN'),
    'Tu es un assistant qui oriente vers un agent humain. Explique que tu vas transférer la demande.',
    '{"welcome": "Je comprends que vous souhaitiez parler à un agent humain. Je vais vous transférer dès que possible.", "transfer": "Votre demande a été transmise à un agent. Il vous contactera bientôt."}',
    ARRAY['raison']
);

-- Create user services mapping table
CREATE TABLE user_services (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES services(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('CLIENT', 'ADMIN', 'SUPER_ADMIN')),
    intrinsic_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, service_id)
);

-- Create RLS policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE interactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_services ENABLE ROW LEVEL SECURITY;

-- Public policies
CREATE POLICY "Enable read access for all users" ON users FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for all users" ON users FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON sessions FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON sessions FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for all users" ON sessions FOR UPDATE USING (true);

CREATE POLICY "Enable read access for all users" ON interactions FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON interactions FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable read access for all users" ON artifacts FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON artifacts FOR INSERT WITH CHECK (true);

CREATE POLICY "Enable read access for all users" ON user_services FOR SELECT USING (true);
CREATE POLICY "Enable insert for all users" ON user_services FOR INSERT WITH CHECK (true);
```

### 3. Application Setup

#### Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd ai-concierge

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
supabase==2.5.0
anthropic==0.7.8
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
httpx==0.25.2
redis==5.0.1
celery==5.3.4
structlog==23.2.0
prometheus-client==0.19.0
```

### 4. Development Environment

#### Start with Docker Compose

```bash
# Create docker-compose.override.yml for development
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - SECRET_KEY=dev-secret-key
    volumes:
      - .:/app
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
EOF

# Start services
docker-compose up -d
```

#### Run Locally

```bash
# Start Redis (if using)
redis-server

# Start the application
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing the Service

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-16T10:00:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "whatsapp": "healthy"
  },
  "uptime": 42.5
}
```

### 2. WhatsApp Webhook Test

Simulate a WhatsApp message:

```bash
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "from": "+221123456789",
      "content": "Bonjour",
      "message_type": "text",
      "message_id": "wa123456"
    },
    "timestamp": "2025-09-16T10:00:00Z"
  }'
```

### 3. Session Management

Create a session manually:

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "user_id": "uuid-here",
    "service_id": "uuid-here"
  }'
```

### 4. API Documentation

- OpenAPI docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Service Context Examples

### Renseignement Service

```json
{
  "service_name": "RENSEIGNEMENT",
  "trigger_keywords": ["infos", "renseignement", "information"],
  "system_prompt": "Tu es un assistant IA pour le service de renseignements. Réponds aux questions générales avec précision et courtoisie.",
  "required_fields": ["sujet"],
  "example_flow": [
    "User: Quels sont les horaires d'ouverture ?",
    "AI: Nos horaires d'ouverture sont du lundi au vendredi de 9h à 18h."
  ]
}
```

### Catéchèse Service

```json
{
  "service_name": "CATECHESE",
  "trigger_keywords": ["catechese", "catéchèse", "cours"],
  "system_prompt": "Tu es un assistant spécialisé dans la catéchèse. Tu dois toujours demander le code parent avant de fournir des informations spécifiques.",
  "required_fields": ["code_parent", "sujet"],
  "intrinsic_id_field": "code_parent",
  "example_flow": [
    "User: Je veux des infos sur la catéchèse",
    "AI: Bienvenue au service de catéchèse. Pour vous aider, j'ai besoin de votre code parent.",
    "User: Mon code est ABC123",
    "AI: Merci ! Que souhaitez-vous savoir sur la catéchèse ?"
  ]
}
```

## Deployment

### 1. Production Build

```bash
# Build Docker image
docker build -t ai-concierge .

# Tag for registry
docker tag ai-concierge:latest your-registry/ai-concierge:latest

# Push to registry
docker push your-registry/ai-concierge:latest
```

### 2. Environment Variables

Production environment should have:

```bash
# Required
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
WAHA_BASE_URL=
WAHA_API_TOKEN=
ANTHROPIC_API_KEY=
SECRET_KEY=
ENVIRONMENT=production

# Optional but recommended
REDIS_URL=
LOG_LEVEL=INFO
SENTRY_DSN=
```

### 3. Health Monitoring

Set up monitoring for:
- HTTP response times (<5s for webhook processing)
- Error rates (<1%)
- System uptime (>99.5%)
- Database connectivity
- External service connectivity (WAHA, Claude)

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check SUPABASE_URL and credentials
   - Verify Supabase project is active
   - Check network connectivity

2. **WhatsApp Messages Not Received**
   - Verify WAHA instance is running
   - Check WAHA_API_TOKEN validity
   - Ensure webhook URL is configured in WAHA

3. **AI Responses Slow**
   - Check ANTHROPIC_API_KEY validity
   - Monitor API rate limits
   - Consider response caching

4. **Session State Issues**
   - Check Redis connection if using
   - Verify session expiration settings
   - Review session state JSON structure

### Log Levels

```bash
# Development
export LOG_LEVEL=DEBUG

# Production
export LOG_LEVEL=INFO
```

## Support

- Issues: GitHub Issues
- Documentation: `/docs` directory
- API Reference: `/docs/api.md`