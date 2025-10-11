<!--
===================================================================================
Sync Impact Report - Constitution Update
===================================================================================
Version: 1.0.0 → 1.0.0 (Initial ratification)
Modified Principles: None (initial creation)
Added Sections: All sections added for initial constitution
Removed Sections: None
Templates Requiring Updates:
  - ✅ plan-template.md: Constitution Check section aligns with principles
  - ✅ spec-template.md: Requirements structure supports all principles
  - ✅ tasks-template.md: Task organization reflects principle-driven development
Follow-up TODOs: None - all placeholders filled
===================================================================================
-->

# Gust-IA AI Concierge Constitution

## Core Principles

### I. Type Safety & Error Resilience

Python type hints MUST be used throughout the codebase. Every function, method, and class MUST have explicit type annotations for parameters and return values. Comprehensive error handling MUST be implemented with structured logging at appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL). No silent failures allowed—all exceptions MUST be caught, logged, and handled gracefully.

**Rationale**: Type safety prevents runtime errors and improves code maintainability. Explicit error handling ensures system reliability and facilitates debugging in production environments where user interactions are critical.

### II. Multi-Channel Architecture

The system MUST support multiple messaging channels (WhatsApp via WAHA, Telegram) through a unified interface. Each channel integration MUST be implemented as an independent service with standardized message normalization. Channel-specific logic MUST NOT leak into business logic layers.

**Rationale**: Multi-channel support is a core requirement for the SDB (Service Diocésain de la Catéchèse) use case. Clean separation ensures scalability and allows adding new channels (e.g., web chat, SMS) without refactoring core services.

### III. Service-Oriented Orchestration

All AI interactions MUST be orchestrated through a central service layer. The system supports three primary services: RENSEIGNEMENT (general information), CATECHESE (catechism management), and CONTACT_HUMAIN (human agent handoff). Service routing MUST be transparent and deterministic based on conversation context.

**Rationale**: Clear service boundaries enable independent development, testing, and monitoring of each use case. Orchestration ensures consistent user experience across different service types.

### IV. Session State Management

User sessions MUST maintain conversation state across interactions. Session data MUST be persisted in Supabase (primary) with Redis caching for performance. Session timeout MUST be configurable (default: 30 minutes). Session handoff between services MUST preserve conversation history.

**Rationale**: Stateful conversations are essential for natural AI interactions. Dual persistence (database + cache) balances reliability with sub-5-second response time requirements.

### V. Security & Authentication

All sensitive data (API keys, tokens, credentials) MUST be stored in environment variables, never in code. WhatsApp messages MUST be verified using webhook signatures. Database access MUST use Supabase RLS (Row Level Security) policies. JWT tokens MUST be used for internal service authentication.

**Rationale**: The system handles sensitive user data (parent codes, student information) requiring strict security controls. Environment-based secrets enable secure deployment across dev/staging/production.

### VI. Testing Discipline

Unit tests MUST cover all service logic. Integration tests MUST validate multi-service workflows. Contract tests MUST verify external API interactions (WAHA, Claude AI, Supabase). Test coverage MUST be maintained above 80%. Tests MUST use isolated fixtures—no shared state between tests.

**Rationale**: High test coverage prevents regressions in a complex multi-service system. Contract tests protect against breaking changes in third-party APIs.

### VII. Observability & Monitoring

Structured JSON logging MUST be used throughout. All API requests MUST log: request ID, user identifier, service type, execution time, and status. Health check endpoints MUST expose service status for all critical dependencies (database, Redis, AI provider, WAHA). Metrics MUST track: request latency (p50, p95, p99), error rates, and active sessions.

**Rationale**: Production debugging requires comprehensive observability. SLA compliance (sub-5-second responses) depends on real-time performance monitoring.

### VIII. Data Privacy & GDPR Compliance

Personal data (phone numbers, names, messages) MUST be handled per GDPR requirements. User consent MUST be documented. Data retention policies MUST be enforced (configurable retention period). Users MUST have the ability to request data deletion. Audit logs MUST track all data access.

**Rationale**: The system processes personal data of students, parents, and catechism participants. GDPR compliance is legally mandatory for European deployments.

## Technology Stack Constraints

### Mandatory Stack

- **Backend Framework**: FastAPI (Python 3.11+) for async request handling
- **Database**: Supabase (PostgreSQL) with RLS policies enabled
- **Caching**: Redis 7+ for session state and rate limiting
- **AI Provider**: Multi-provider support (Claude via Anthropic SDK, Gemini, OpenRouter) with round-robin key rotation
- **Messaging Channels**: WAHA for WhatsApp, python-telegram-bot for Telegram
- **Container Orchestration**: Docker Compose for local development and deployment
- **File Storage**: MinIO for media files (images, documents, PDFs)

### Prohibited Patterns

- **No ORM abstractions** beyond Supabase client—direct SQL via stored procedures preferred for complex queries
- **No synchronous blocking calls** in API endpoints—all I/O operations MUST be async
- **No client-side state** for sensitive data—all state MUST be server-managed
- **No hardcoded configurations**—all environment-specific settings MUST be in .env files

**Rationale**: These constraints emerged from production learnings. FastAPI's async nature is essential for WhatsApp webhook latency requirements. Supabase RLS provides database-level security. Multi-provider AI support prevents vendor lock-in and enables cost optimization.

## Development Workflow

### Code Review Requirements

All code changes MUST:
- Pass automated linting (black, isort, mypy)
- Include type hints for new functions
- Update relevant tests if changing behavior
- Include docstrings for public APIs
- Document breaking changes in commit messages

Pull requests MUST:
- Reference a specification document (spec.md) or issue
- Include test evidence (screenshots, logs, test output)
- Pass CI pipeline (linting, type checking, tests)
- Receive approval from at least one maintainer
- Follow commit message convention: `type(scope): description`

### Deployment Gates

Production deployments MUST verify:
1. All tests pass (unit, integration, contract)
2. Database migrations are idempotent and reversible
3. Environment variables are validated against .env.template
4. Health check endpoint returns 200 OK
5. Critical paths tested via smoke tests (authentication, message handling, AI orchestration)
6. Rollback plan documented in deployment notes

### Quality Standards

- **Response Time**: 95th percentile < 5 seconds for WhatsApp message handling
- **Availability**: 99.5% uptime for webhook endpoints
- **Error Rate**: < 1% of requests result in unhandled exceptions
- **Test Coverage**: Maintained above 80% for services layer
- **Code Duplication**: Avoid copy-paste—extract shared logic to utilities

**Rationale**: Consistent review processes prevent bugs in production. Deployment gates ensure safe releases. Quality standards maintain user experience and system reliability.

## Governance

### Amendment Procedure

Constitution changes MUST:
1. Be proposed via pull request with rationale
2. Include impact analysis on existing codebase
3. Update dependent templates (plan-template.md, spec-template.md, tasks-template.md)
4. Receive approval from project maintainers
5. Include migration plan if breaking existing code
6. Increment version number per semantic versioning rules

### Versioning Policy

- **MAJOR** (X.0.0): Backward incompatible governance changes, principle removals, or redefinitions requiring codebase refactoring
- **MINOR** (x.Y.0): New principles added, sections expanded, or new constraints introduced
- **PATCH** (x.y.Z): Clarifications, wording improvements, typo fixes, or formatting changes

### Compliance Review

All feature specifications (spec.md) MUST include a "Constitution Compliance" section verifying:
- Type safety requirements satisfied
- Security principles followed
- Testing coverage adequate
- Observability instrumentation included
- Data privacy controls implemented

Project maintainers MUST review compliance quarterly and update this constitution to reflect evolved best practices.

### Runtime Development Guidance

For agent-specific development guidance, see `CLAUDE.md` which contains:
- SDB data source setup and configuration
- WhatsApp AI Concierge operational procedures
- Security protocols and execution rules
- Admin notification requirements
- Deployment architecture details

**Version**: 1.0.0 | **Ratified**: 2025-10-11 | **Last Amended**: 2025-10-11
