# Tasks: WhatsApp AI Concierge Service

**Input**: Design documents from `/specs/001-projet-concierge-ia/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → Implementation plan loaded successfully
   → Extract: tech stack (FastAPI, WAHA, Supabase, Claude), libraries, structure
2. Load optional design documents:
   → data-model.md: Extract 9 entities → model tasks
   → contracts/api.yaml: Extract 6 endpoints → contract test + implementation tasks
   → research.md: Extract technical decisions → setup tasks
   → quickstart.md: Extract test scenarios → integration test tasks
3. Generate tasks by category:
   → Setup: project structure, dependencies, linting, Docker
   → Tests: 6 contract tests, 4 integration tests, 3 user story tests
   → Core: 9 model entities, 3 service contexts, 6 API endpoints
   → Integration: WhatsApp, Supabase, Redis, Claude, logging
   → Polish: unit tests, performance, docs, monitoring
4. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially (T001, T002...)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   → All 6 endpoints have tests ✓
   → All 9 entities have models ✓
   → All core services implemented ✓
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root
- Paths shown based on plan.md structure decision

## Phase 3.1: Setup
- [ ] T001 Create project structure: src/models/, src/services/, src/api/, src/orchestration/, src/utils/, tests/contract/, tests/integration/, tests/unit/
- [ ] T002 Initialize Python FastAPI project with dependencies (FastAPI, Supabase, Anthropic, WAHA SDK, Redis, Pydantic, Uvicorn)
- [ ] T003 [P] Configure linting (flake8, black), formatting (isort), and pre-commit hooks
- [ ] T004 Create Dockerfile and docker-compose.yml for development environment
- [ ] T005 Set up environment configuration (.env template, pydantic-settings)
- [ ] T006 Create requirements.txt and requirements-dev.txt

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T007 [P] Contract test POST /webhook in tests/contract/test_webhook_post.py
- [ ] T008 [P] Contract test POST /orchestrate in tests/contract/test_orchestrate_post.py
- [ ] T009 [P] Contract test GET /sessions/{id} in tests/contract/test_sessions_get.py
- [ ] T010 [P] Contract test PUT /sessions/{id} in tests/contract/test_sessions_put.py
- [ ] T011 [P] Contract test GET /admin/services in tests/contract/test_services_get.py
- [ ] T012 [P] Contract test GET /health in tests/contract/test_health_get.py
- [ ] T013 [P] Integration test WhatsApp message flow in tests/integration/test_whatsapp_flow.py
- [ ] T014 [P] Integration test session management in tests/integration/test_session_management.py
- [ ] T015 [P] Integration test service routing in tests/integration/test_service_routing.py
- [ ] T016 [P] Integration test AI orchestration in tests/integration/test_ai_orchestration.py
- [ ] T017 [P] Integration test human handoff in tests/integration/test_human_handoff.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
### Data Models
- [ ] T018 [P] User model in src/models/user.py (phone_number, name, is_active, timestamps)
- [ ] T019 [P] Service model in src/models/service.py (name, trigger_keywords, processing_type, etc.)
- [ ] T020 [P] Session model in src/models/session.py (user_id, service_id, status, state, metadata)
- [ ] T021 [P] Interaction model in src/models/interaction.py (session_id, message_type, content, media)
- [ ] T022 [P] Artifact model in src/models/artifact.py (session_id, service_id, type, content, file_url)
- [ ] T023 [P] User_Service model in src/models/user_service.py (user_id, service_id, role, intrinsic_id)
- [ ] T024 [P] Service_Context model in src/models/service_context.py (service_id, system_prompt, prompts)
- [ ] T025 [P] Service_Info model in src/models/service_info.py (service_id, title, content, time bounds)
- [ ] T026 [P] Media model in src/models/media.py (filename, file_path, mime_type, size)

### Service Layer
- [ ] T027 [P] UserService in src/services/user_service.py (CRUD, phone lookup, role management)
- [ ] T028 [P] ServiceService in src/services/service_service.py (service management, trigger matching)
- [ ] T029 [P] SessionService in src/services/session_service.py (session lifecycle, state management)
- [ ] T030 [P] InteractionService in src/services/interaction_service.py (message history, conversation flow)
- [ ] T031 [P] ArtifactService in src/services/artifact_service.py (artifact generation, storage)
- [ ] T032 [P] OrchestrationService in src/services/orchestration_service.py (AI coordination, prompt injection)

### API Endpoints
- [ ] T033 POST /webhook endpoint in src/api/webhook.py (WhatsApp message handling)
- [ ] T034 POST /orchestrate endpoint in src/api/orchestration.py (AI request processing)
- [ ] T035 GET /sessions/{id} endpoint in src/api/sessions.py (session retrieval)
- [ ] T036 PUT /sessions/{id} endpoint in src/api/sessions.py (session update)
- [ ] T037 GET /admin/services endpoint in src/api/admin.py (service management)
- [ ] T038 GET /health endpoint in src/api/health.py (system health check)

### Orchestration Logic
- [ ] T039 [P] Service router in src/orchestration/router.py (keyword matching, role-based routing)
- [ ] T040 [P] Session manager in src/orchestration/session_manager.py (conversation state, expiration)
- [ ] T041 [P] AI orchestrator in src/orchestration/ai_orchestrator.py (Claude integration, prompt management)
- [ ] T042 [P] Human handoff in src/orchestration/human_handoff.py (human agent transfer logic)

### Service Contexts
- [ ] T043 [P] RENSEIGNEMENT service context (general information prompts)
- [ ] T044 [P] CATECHESE service context (code_parent validation, catechism prompts)
- [ ] T045 [P] CONTACT_HUMAIN service context (human handoff prompts)

## Phase 3.4: Integration
- [ ] T046 Connect Supabase database to all models with proper connection pooling
- [ ] T047 Implement Redis caching for active sessions and frequently accessed data
- [ ] T048 Integrate WAHA SDK for WhatsApp message sending/receiving
- [ ] T049 Connect Claude SDK with proper error handling and rate limiting
- [ ] T050 Implement authentication middleware (JWT for admin endpoints)
- [ ] T051 Add request/response logging with correlation IDs
- [ ] T052 Configure error handling and exception management
- [ ] T053 Set up CORS and security headers for webhooks
- [ ] T054 Implement session expiration and cleanup logic
- [ ] T055 Add media upload/download handling for WhatsApp media messages

## Phase 3.5: Polish
- [ ] T056 [P] Unit tests for all models in tests/unit/test_models.py
- [ ] T057 [P] Unit tests for services in tests/unit/test_services.py
- [ ] T058 [P] Unit tests for orchestration logic in tests/unit/test_orchestration.py
- [ ] T059 Performance tests (<5s response time for webhook processing)
- [ ] T060 [P] Update CLAUDE.md with new service stack and endpoints
- [ ] T061 Create comprehensive API documentation
- [ ] T062 Add monitoring and metrics (Prometheus endpoints)
- [ ] T063 Implement structured logging with log levels
- [ ] T064 Add database migration scripts for Supabase schema
- [ ] T065 Create deployment configuration (Coolify, environment variables)
- [ ] T066 Write comprehensive test suite for quickstart scenarios
- [ ] T067 Add integration with existing SDB data sources (Baserow, Google Drive)

## Dependencies
- Tests (T007-T017) before implementation (T018-T055)
- Models (T018-T026) before services (T027-T032)
- Services (T027-T032) before endpoints (T033-T038)
- Core implementation (T018-T055) before integration (T046-T055)
- Integration (T046-T055) before polish (T056-T067)

## Parallel Execution Groups

### Group 1: Model Creation (can run together)
```
Task: "User model in src/models/user.py"
Task: "Service model in src/models/service.py"
Task: "Session model in src/models/session.py"
Task: "Interaction model in src/models/interaction.py"
Task: "Artifact model in src/models/artifact.py"
Task: "User_Service model in src/models/user_service.py"
Task: "Service_Context model in src/models/service_context.py"
Task: "Service_Info model in src/models/service_info.py"
Task: "Media model in src/models/media.py"
```

### Group 2: Service Layer (can run together)
```
Task: "UserService in src/services/user_service.py"
Task: "ServiceService in src/services/service_service.py"
Task: "SessionService in src/services/session_service.py"
Task: "InteractionService in src/services/interaction_service.py"
Task: "ArtifactService in src/services/artifact_service.py"
Task: "OrchestrationService in src/services/orchestration_service.py"
```

### Group 3: Contract Tests (can run together)
```
Task: "Contract test POST /webhook in tests/contract/test_webhook_post.py"
Task: "Contract test POST /orchestrate in tests/contract/test_orchestrate_post.py"
Task: "Contract test GET /sessions/{id} in tests/contract/test_sessions_get.py"
Task: "Contract test PUT /sessions/{id} in tests/contract/test_sessions_put.py"
Task: "Contract test GET /admin/services in tests/contract/test_services_get.py"
Task: "Contract test GET /health in tests/contract/test_health_get.py"
```

### Group 4: Integration Tests (can run together)
```
Task: "Integration test WhatsApp message flow in tests/integration/test_whatsapp_flow.py"
Task: "Integration test session management in tests/integration/test_session_management.py"
Task: "Integration test service routing in tests/integration/test_service_routing.py"
Task: "Integration test AI orchestration in tests/integration/test_ai_orchestration.py"
Task: "Integration test human handoff in tests/integration/test_human_handoff.py"
```

### Group 5: Orchestration Components (can run together)
```
Task: "Service router in src/orchestration/router.py"
Task: "Session manager in src/orchestration/session_manager.py"
Task: "AI orchestrator in src/orchestration/ai_orchestrator.py"
Task: "Human handoff in src/orchestration/human_handoff.py"
```

### Group 6: Service Contexts (can run together)
```
Task: "RENSEIGNEMENT service context (general information prompts)"
Task: "CATECHESE service context (code_parent validation, catechism prompts)"
Task: "CONTACT_HUMAIN service context (human handoff prompts)"
```

## Critical Path
The most critical dependency chain is:
T001 (setup) → T007-T017 (tests) → T018-T026 (models) → T027-T032 (services) → T033-T038 (endpoints) → T039-T042 (orchestration) → T046 (database integration) → T048 (WhatsApp integration) → T049 (Claude integration)

## Success Criteria
- All 67 tasks completed
- All tests pass (contract, integration, unit)
- WhatsApp webhook responds within 5 seconds
- 60% automation rate for simple interactions achieved
- All three core services (RENSEIGNEMENT, CATECHESE, CONTACT_HUMAIN) functional
- Human handoff process working correctly
- Database schema matches data-model.md exactly
- API endpoints match OpenAPI specification exactly

## Notes
- [P] tasks = different files, no dependencies
- Verify tests fail before implementing corresponding functionality
- Commit after each task for better tracking
- Focus on MVP functionality first (3 core services)
- Performance optimization can come after core functionality works
- Security (authentication, input validation) should be implemented early