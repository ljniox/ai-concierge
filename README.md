# WhatsApp AI Concierge Service

A multi-service WhatsApp concierge with AI orchestration, built with FastAPI, Supabase, and Claude AI.

## Features

- **Multi-Service Support**: Handles RENSEIGNEMENT, CATECHESE, and CONTACT_HUMAIN services
- **AI Orchestration**: Uses Claude AI for intelligent conversation routing
- **Session Management**: Maintains conversation state across interactions
- **WhatsApp Integration**: Built on WAHA for reliable WhatsApp messaging
- **Real-time Processing**: Sub-5 second response times with high availability
- **Human Handoff**: Seamless escalation to human agents when needed

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WhatsApp     │    │   FastAPI       │    │   Supabase      │
│   (WAHA)       │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Claude AI     │
                       │   Orchestration │
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Supabase account
- WAHA instance
- Claude API key

### Environment Setup

1. Copy the environment template:
   ```bash
   cp .env.template .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-key

   # WAHA Configuration
   WAHA_BASE_URL=https://your-waha-instance.com
   WAHA_API_TOKEN=your-waha-token

   # Claude AI Configuration
   ANTHROPIC_API_KEY=your-claude-api-key

   # Application Configuration
   SECRET_KEY=your-secret-key
   ENVIRONMENT=development
   ```

### Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Start the development server:
   ```bash
   uvicorn src.main:app --reload
   ```

### Docker Deployment

1. Build the image:
   ```bash
   docker build -t whatsapp-concierge .
   ```

2. Run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## API Documentation

Once running, access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:
```bash
# All tests
pytest

# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Contract tests only
pytest -m contract

# With coverage
pytest --cov=src
```

## Configuration

See `.env.template` for all available configuration options.

## Services

### RENSEIGNEMENT
Handles general inquiries and information requests.

### CATECHESE
Manages catechism-related questions and scheduling.

### CONTACT_HUMAIN
Provides human agent escalation and contact information.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is licensed under the MIT License.
