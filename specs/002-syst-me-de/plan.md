# Implementation Plan: Système de Gestion de Profils et Inscriptions avec SQLite

**Branch**: `002-syst-me-de` | **Date**: 2025-10-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-syst-me-de/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements a multi-profile enrollment management system for the SDB catechism program with three core components: (1) parent enrollment with OCR document extraction from birth certificates, baptism certificates, and transfer attestations, (2) Mobile Money payment validation workflow with screenshot proof and treasurer approval, and (3) SQLite multi-database architecture (`catechese_app.db`, `temp_pages_system.db`, `core_system.db`) to support modular application growth. The system manages 13 user profiles with role-based permissions and provides temporary secure URLs for document collection. Technical approach leverages Python OCR libraries for document extraction, hybrid manual+automated payment validation, and SQLite as the single source of truth for all enrollment and catechism data (excluding Baserow integration from original spec).

## Technical Context

**Language/Version**: Python 3.11+ (consistent with existing FastAPI backend)
**Primary Dependencies**: FastAPI, Supabase Python client, Redis, WAHA SDK, python-telegram-bot, NEEDS CLARIFICATION: OCR library (pytesseract vs. EasyOCR vs. cloud OCR)
**Storage**: SQLite 3.40+ (sdb_cate.sqlite EXISTING + new tables, temp_pages_system.db NEW, core_system.db NEW), Supabase/PostgreSQL (sessions, logs), MinIO (document files)
**Testing**: pytest (existing standard), pytest-asyncio for async tests, NEEDS CLARIFICATION: OCR testing strategy (fixture documents vs. mock OCR results)
**Target Platform**: Linux server (Docker containers), existing deployment on Oracle Cloud
**Project Type**: Backend API extension (extends existing FastAPI application)
**Performance Goals**: < 5 seconds p95 for message handling (constitution requirement), < 3 seconds for inscription creation, OCR processing < 10 seconds per document
**Constraints**: Document upload max 10MB (spec FR-002), 7-day expiration for temporary pages (FR-043), 2-year audit log retention (FR-054)
**Scale/Scope**: ~500-1000 students per enrollment period, 13 user profile types, 59 functional requirements, 3 separate SQLite databases

**Architecture Change from Spec**: Baserow integration (FR-036, FR-037) will be excluded. All catechism data (catéchumènes, parents, notes, classes) will be stored exclusively in SQLite. The existing `/home/ubuntu/ai-concierge/sdb_cate.sqlite` database (509 students, 341 parents, 819 enrollments) will be extended with new tables for enhanced enrollment features while preserving historical data.

**Key Technical Unknowns (to be resolved in Phase 0 research)**:
- OCR Library Selection: Need to compare pytesseract (Tesseract wrapper), EasyOCR (deep learning), Azure/Google Cloud OCR (paid APIs) for French document extraction accuracy
- SQLite Concurrency: Multi-database write concurrency strategy (WAL mode, connection pooling, lock timeout configuration)
- Document Storage Architecture: MinIO integration pattern for document lifecycle (upload → OCR → archive), folder structure per year/student
- Payment Screenshot OCR: Mobile Money receipt format variations across operators (Orange Money, Wave, Free Money), OCR reliability for transaction IDs
- SQLite Historical Data: Strategy for migrating existing catechism data (if needed) or starting fresh with new enrollment system

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Type Safety & Error Resilience ✅ PASS
- **Compliance**: All new services MUST use Python type hints (existing codebase standard)
- **Evidence**: Spec requires comprehensive error handling for OCR failures (FR-003-005), document type detection errors, payment validation rejections (FR-015)
- **Implementation**: OCR service will return `Result[ExtractedData, OCRError]` types, document upload validation with typed exceptions

### II. Multi-Channel Architecture ✅ PASS
- **Compliance**: Feature integrates with existing WhatsApp (WAHA) and Telegram channels
- **Evidence**: Spec FR-001 requires enrollment via "WhatsApp ou Telegram", FR-032 uses "WhatsApp/Telegram verified account" for authentication
- **Implementation**: Enrollment service will use existing `InteractionService` abstraction, no channel-specific logic in business layer

### III. Service-Oriented Orchestration ✅ PASS
- **Compliance**: Enrollment management fits into existing CATECHESE service
- **Evidence**: Spec focuses on catechism enrollment (FR-001-010), class management (FR-046-050), aligns with CATECHESE service domain
- **Implementation**: New `EnrollmentOrchestrationService` will be invoked via existing orchestration layer

### IV. Session State Management ✅ PASS
- **Compliance**: Multi-step enrollment workflow requires session persistence
- **Evidence**: Spec describes guided step-by-step forms (FR-001), document upload across multiple messages, payment submission as separate flow
- **Implementation**: Will use existing Supabase sessions + Redis caching, extend session schema with enrollment state machine (brouillon → en attente paiement → active)

### V. Security & Authentication ⚠️ ATTENTION REQUIRED
- **Compliance**: New authentication method (code parent from Baserow) must follow security principles
- **Evidence**: FR-032 requires hybrid authentication (WhatsApp/Telegram verified OR code parent for non-DB numbers)
- **Implementation**: Code parent validation MUST NOT leak credentials to logs, validation via secure Baserow API call, rate limiting on code verification attempts
- **Action**: Research secure code parent validation pattern in Phase 0

### VI. Testing Discipline ⚠️ ATTENTION REQUIRED
- **Compliance**: OCR and payment validation require comprehensive test coverage
- **Evidence**: Success criteria SC-002 requires ">85% OCR accuracy", SC-007 requires "95% payment submission success"
- **Challenge**: How to test OCR without large fixture document library, how to test Mobile Money screenshot variations
- **Action**: Research OCR testing strategies (mock vs. fixture vs. golden masters) in Phase 0

### VII. Observability & Monitoring ✅ PASS
- **Compliance**: Comprehensive audit logging required by spec
- **Evidence**: FR-051-055 mandate action logs with user_id, action_type, entity_type, timestamp, 2-year retention
- **Implementation**: Extend existing structured logging, add enrollment-specific metrics (OCR success rate, payment validation time, inscription completion rate)

### VIII. Data Privacy & GDPR Compliance ✅ PASS
- **Compliance**: Spec explicitly addresses GDPR requirements
- **Evidence**: FR-054 requires 2-year log retention, FR-055 mandates log anonymization after 2 years, spec mentions "conformité GDPR" in success criteria SC-015
- **Implementation**: Personal data (birth certificates, baptism certificates) in MinIO with encryption at rest, audit trail for all document access, data retention policy enforcement

### Technology Stack Compliance ✅ PASS
- **Mandatory Stack**: FastAPI backend ✅, Supabase database ✅, Redis caching ✅, WAHA/Telegram ✅, Docker ✅, MinIO storage ✅
- **New Additions**: SQLite (justified for multi-application isolation per spec FR-033-040), OCR library (required for FR-003-005), Baserow client (existing integration)
- **Prohibited Patterns**: No ORM violations (using direct SQLite + Supabase client), async throughout ✅, no hardcoded configs ✅

### Gate Status: ✅ PASS (Post-Design Re-evaluation)

**Phase 0 Research Completed**:
1. ✅ Security pattern for code parent validation (Principle V) - **RESOLVED**
   - Decision: bcrypt hashing (work factor 12) with Redis rate limiting (5 attempts/hour)
   - Implementation: Hashed codes in `profil_utilisateurs.code_parent_hash`, validation without logging actual codes
   - Documented in research.md §5

2. ✅ OCR testing strategy to achieve 80%+ coverage (Principle VI) - **RESOLVED**
   - Decision: Three-tier testing (mock unit tests, fixture integration tests, golden master regression)
   - Coverage: Unit tests (mocked) cover 80%+ of service logic, integration tests validate real OCR accuracy
   - Documented in research.md §6

**Phase 1 Design Completed**:
- ✅ data-model.md: Full entity definitions with legacy table integration (sdb_cate.sqlite existing + new tables)
- ✅ contracts/enrollment-api.yaml: OpenAPI 3.0 specification with 18 endpoints, role-based security
- ✅ quickstart.md: Developer onboarding guide with setup, testing, troubleshooting
- ✅ Agent context updated with new technology stack

**Final Constitution Compliance Status**:
- **Type Safety**: ✅ Pydantic models defined in data-model.md
- **Multi-Channel**: ✅ Reuses existing WAHA/Telegram infrastructure
- **Service Orchestration**: ✅ Enrollment fits into CATECHESE service domain
- **Session State**: ✅ Extends existing Supabase + Redis pattern
- **Security**: ✅ bcrypt + rate limiting + audit logs
- **Testing**: ✅ Three-tier strategy achieves > 80% coverage
- **Observability**: ✅ action_logs table + enrollment metrics
- **GDPR**: ✅ 2-year retention + anonymization in data model

**No complexity violations** - All new patterns justified by requirements

**Ready for Phase 2**: Implementation (task generation with `/speckit.tasks`)

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── models/
│   ├── enrollment.py          # NEW: Inscription, Document, Paiement models
│   ├── profile.py             # NEW: ProfilUtilisateur, permissions definitions
│   ├── classe.py              # NEW: Classe model
│   └── temp_page.py           # NEW: PageTemporaire model
├── services/
│   ├── enrollment_service.py  # NEW: Enrollment orchestration
│   ├── ocr_service.py         # NEW: Document OCR extraction
│   ├── document_service.py    # NEW: Document upload/storage/validation
│   ├── payment_service.py     # NEW: Payment submission and validation
│   ├── profile_service.py     # NEW: User profile and permission management
│   ├── temp_page_service.py   # NEW: Temporary page generation
│   └── audit_service.py       # NEW: Action logging (FR-051-055)
├── database/
│   ├── sqlite_manager.py      # NEW: Multi-DB connection manager
│   ├── catechese_schema.sql   # NEW: catechese_app.db schema
│   ├── temp_pages_schema.sql  # NEW: temp_pages_system.db schema
│   └── core_schema.sql        # NEW: core_system.db schema
├── api/
│   ├── v1/
│   │   ├── enrollment.py      # NEW: Enrollment endpoints
│   │   ├── payments.py        # NEW: Payment validation endpoints
│   │   ├── profiles.py        # NEW: Profile management endpoints
│   │   └── temp_pages.py      # NEW: Temporary page endpoints
│   └── webhooks.py            # MODIFY: Add enrollment handlers
├── orchestration/
│   └── catechese_orchestrator.py  # MODIFY: Add enrollment flows
└── utils/
    ├── ocr_utils.py           # NEW: OCR preprocessing helpers
    ├── document_validators.py # NEW: Document type detection
    └── execution_logger.py    # EXISTING: Summary logging

tests/
├── unit/
│   ├── test_enrollment_service.py
│   ├── test_ocr_service.py
│   ├── test_payment_service.py
│   ├── test_profile_service.py
│   └── test_sqlite_manager.py
├── integration/
│   ├── test_enrollment_flow.py
│   └── test_payment_validation_flow.py
├── contract/
│   └── test_minio_api.py
└── fixtures/
    ├── sample_birth_certificate.pdf
    ├── sample_baptism_certificate.jpg
    └── sample_mobile_money_receipt.png

data/
├── sdb_cate.sqlite            # EXISTING (509 students, 341 parents) + NEW tables
├── temp_pages_system.db       # NEW: Temporary pages and codes
└── core_system.db             # NEW: System configuration
```

**Structure Decision**: This follows the existing "Single project" FastAPI structure (Option 1) with backend services. The feature extends the current `src/` layout with new enrollment-specific modules while reusing existing infrastructure (api/, orchestration/, utils/). The existing `sdb_cate.sqlite` database will be extended with new tables, and two new SQLite databases (`temp_pages_system.db`, `core_system.db`) provide multi-application isolation as required by FR-033-040.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
