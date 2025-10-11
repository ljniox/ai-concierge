# Implementation Plan: Automatic Account Creation Based on Phone Number

**Branch**: `003-sur-la-base` | **Date**: 2025-01-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-sur-la-base/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Automatic account creation system for catechism parents contacting via WhatsApp or Telegram. The system validates phone numbers against the existing catechism database, creates user accounts automatically, assigns parent roles, and enables immediate interaction with the enrollment system. Multi-channel support with webhook security, session management, and GDPR compliance.

## Technical Context

**Language/Version**: Python 3.11+ (per constitution requirement)
**Primary Dependencies**: FastAPI (async web framework), WAHA SDK (WhatsApp), python-telegram-bot (Telegram), python-phonenumbers (phone validation), python-jose (JWT), Supabase client (database)
**Storage**: Supabase (PostgreSQL with RLS) + Redis (caching) per constitution
**Testing**: pytest (unit), httpx (integration), contract tests for external APIs
**Target Platform**: Linux server (containerized deployment)
**Project Type**: web (backend API service with webhook endpoints)
**Performance Goals**: <2s account creation (NFR-001), 100+ concurrent users (NFR-002), 99.9% uptime (NFR-003)
**Constraints**: Async-only (constitution), no ORM abstractions (constitution), environment-based configuration, <5s webhook response per constitution
**Scale/Scope**: 100+ concurrent parents, WhatsApp + Telegram channels, automatic account creation workflow

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Type Safety & Error Resilience
- Python 3.11+ with type hints required for all functions
- Comprehensive error handling with structured logging
- Async-only pattern prevents blocking calls

### ✅ Multi-Channel Architecture
- WhatsApp integration via WAHA SDK
- Telegram integration via python-telegram-bot
- Unified message normalization through standardized webhook handlers

### ✅ Service-Oriented Orchestration
- Account creation as independent service
- Session management service for conversation state
- Audit logging service for compliance tracking

### ✅ Session State Management
- Supabase (primary) + Redis (caching) for session persistence
- Configurable session timeout (default: 30 minutes)
- Session handoff preserves conversation history

### ✅ Security & Authentication
- Environment variables for all secrets (constitution requirement)
- Webhook signature verification for WhatsApp (FR-013)
- JWT tokens for platform authentication (FR-015)
- Supabase RLS policies for database security

### ✅ Testing Discipline
- pytest for unit tests (>80% coverage required)
- Integration tests for multi-service workflows
- Contract tests for external APIs (WAHA, Supabase)

### ✅ Observability & Monitoring
- Structured JSON logging throughout
- Request ID, user identifier, execution time tracking
- Health check endpoints for all dependencies
- Performance metrics (latency, error rates, active sessions)

### ✅ Data Privacy & GDPR Compliance
- Phone number masking in logs (NFR-005)
- User consent documentation and tracking
- Configurable data retention (6 months per NFR-004)
- Audit logs for all data access (FR-010)

**GATE STATUS**: ✅ PASSED - All constitutional requirements satisfied

## Project Structure

### Documentation (this feature)

```
specs/003-sur-la-base/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── openapi.yaml     # API contract specification
│   └── webhook-schemas.yaml # Webhook event schemas
├── checklists/          # Quality validation checklists
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── models/              # Data models and schemas
│   ├── account.py       # User account models
│   ├── session.py       # Session management models
│   └── base.py          # Base database models
├── services/            # Business logic services
│   ├── account_service.py      # Account creation service
│   ├── session_service.py      # Session management service
│   ├── audit_service.py        # Audit logging service
│   └── messaging_service.py    # Message handling service
├── handlers/            # Webhook handlers for different platforms
│   ├── whatsapp_webhook.py     # WhatsApp webhook processing
│   └── telegram_webhook.py     # Telegram webhook processing
├── api/                 # API endpoints and routing
│   └── v1/              # API v1 endpoints
├── middleware/          # Request/response middleware
│   ├── auth.py          # Authentication middleware
│   └── rate_limiting.py # Rate limiting middleware
├── utils/               # Utility functions
│   ├── phone_validator.py       # Phone number validation
│   ├── audit_logger.py          # Audit logging utilities
│   ├── exceptions.py            # Custom exception classes
│   └── logging.py               # Logging configuration
└── database/            # Database related code
    └── migrations/      # Database migration scripts

tests/
├── unit/                # Unit tests for individual components
├── integration/         # Integration tests for service workflows
└── contract/            # Contract tests for external APIs
```

**Structure Decision**: Single web backend API service following existing codebase structure. The feature extends the current FastAPI application with new webhook handlers, services, and models while maintaining the established directory organization.

