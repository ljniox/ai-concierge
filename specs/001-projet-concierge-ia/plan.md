# Implementation Plan: WhatsApp AI Concierge Service

**Branch**: `001-projet-concierge-ia` | **Date**: 2025-09-16 | **Spec**: [/specs/001-projet-concierge-ia/spec.md](/specs/001-projet-concierge-ia/spec.md)
**Input**: Feature specification from `/specs/001-projet-concierge-ia/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Technical context filled with user-provided architecture details
   → Project Type detected: web (FastAPI backend + Supabase)
   → Structure Decision: Single project with backend focus
3. Fill the Constitution Check section based on the content of the constitution document.
   → Constitution template detected - minimal constraints to apply
4. Evaluate Constitution Check section below
   → No violations detected for web backend project
   → Progress Tracking: Initial Constitution Check complete
5. Execute Phase 0 → research.md
   → All NEEDS CLARIFICATION resolved from user clarifications
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file
   → Design artifacts generated based on user requirements
7. Re-evaluate Constitution Check section
   → No new violations detected
   → Progress Tracking: Post-Design Constitution Check complete
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
   → Task generation strategy documented
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
WhatsApp AI Concierge Service providing multi-service routing through WhatsApp with AI orchestration. The system will identify users, route to appropriate services (RENSEIGNEMENT, CATECHESE, CONTACT_HUMAIN), maintain session state, and generate final artifacts with human handoff capabilities.

## Technical Context
**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, WAHA SDK, Supabase Client, Claude SDK
**Storage**: Supabase (PostgreSQL) - services, sessions, interactions, artifacts, infos tables
**Testing**: pytest, FastAPI TestClient
**Target Platform**: Linux server (Docker)
**Project Type**: web (backend API + webhook)
**Performance Goals**: <5s initial response time, 60% automation rate for simple interactions
**Constraints**: HTTPS via reverse proxy, environment variables for secrets, Africa/Dakar timezone
**Scale/Scope**: MVP supporting 3 core services, WhatsApp integration, session management

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Constitution Template Detected**: The constitution file is a template with placeholder content. No specific constitutional constraints apply beyond standard software development practices.

- [ ] Library-First principle: Not applicable (web service project)
- [ ] CLI Interface: Not applicable (web service project)
- [ ] Test-First: Will be enforced during implementation
- [ ] Integration Testing: Required for webhook, WhatsApp, and Supabase integrations

**Result**: PASS - No constitutional violations detected for this project type

## Project Structure

### Documentation (this feature)
```
specs/001-projet-concierge-ia/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Single project (DEFAULT)
src/
├── models/             # Data models and schemas
├── services/           # Business logic services
├── api/                # FastAPI endpoints and webhooks
├── orchestration/      # AI orchestration logic
└── utils/              # Utilities and helpers

tests/
├── contract/           # Contract tests for API endpoints
├── integration/        # Integration tests for external services
└── unit/               # Unit tests for business logic
```

**Structure Decision**: Single project with backend API focus, appropriate for FastAPI web service

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - All technical unknowns resolved from user-provided architecture details
   - WAHA integration patterns research
   - Supabase schema design best practices
   - Claude SDK orchestration patterns

2. **Generate and dispatch research agents**:
   ```
   Task: "Research WAHA WhatsApp integration patterns for AI concierge"
   Task: "Find best practices for session management in WhatsApp bots"
   Task: "Research Supabase schema design for multi-service routing"
   Task: "Evaluate Claude SDK patterns for conversational AI orchestration"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all technical decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P]
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation
- Dependency order: Models before services before API endpoints
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No constitutional violations detected - no complexity tracking required

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*