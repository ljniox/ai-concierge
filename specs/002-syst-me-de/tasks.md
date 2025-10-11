# Tasks: Système de Gestion de Profils et Inscriptions avec SQLite

**Input**: Design documents from `/home/ubuntu/ai-concierge/specs/002-syst-me-de/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/enrollment-api.yaml ✅

**Tests**: Not explicitly requested in specification - tasks focus on implementation

**Organization**: Tasks grouped by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1=P1 MVP Enrollment, US2=P1 MVP Payment, US3=P2 Profiles, US4=P2 SQLite, US5=P3 Catechist, US6=P4 Future)
- Paths use `src/` convention per plan.md (single FastAPI project structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency installation

- [ ] T001 Install Python dependencies: `pip install easyocr==1.7.0 aiosqlite==0.19.0 bcrypt==4.1.2 minio==7.2.3`
- [ ] T002 [P] Update `.env` with enrollment-specific variables per quickstart.md (SQLITE_DB_PATH, OCR settings, MinIO config)
- [ ] T003 [P] Create directory structure: `src/database/`, `src/database/migrations/`, `src/models/`, `data/`, `tests/fixtures/`
- [ ] T004 [P] Start MinIO container and create `sdb-catechese` bucket per quickstart.md

**Checkpoint**: Environment configured, dependencies installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [ ] T005 Create SQL migration script `src/database/migrations/add_enrollment_tables_v1.0.0.sql` with 5 new tables (inscriptions, documents, paiements, profil_utilisateurs, action_logs) per data-model.md
- [ ] T006 Create `src/database/sqlite_manager.py` - SQLite connection manager with WAL mode, connection pooling (pool size: 20), multi-database support (sdb_cate.sqlite, temp_pages_system.db, core_system.db)
- [ ] T007 Create `src/database/migration_runner.py` - Migration script executor with transaction rollback on error
- [ ] T008 Run migration on existing `sdb_cate.sqlite` to add new tables alongside legacy tables (catechumenes_2, parents_2, inscriptions_16)
- [ ] T009 [P] Create temp_pages_schema.sql and initialize `data/temp_pages_system.db`
- [ ] T010 [P] Create core_schema.sql and initialize `data/core_system.db` with applications registry

### Base Models (Shared Across Stories)

- [ ] T011 [P] Create `src/models/base.py` - Pydantic base model with UUID generation, timestamp fields, from_db/to_db serialization helpers
- [ ] T012 [P] Create `src/models/legacy.py` - Read-only Pydantic models for existing tables (Catechumene, Parent, InscriptionLegacy) per data-model.md existing schema

### Authentication & Authorization Framework

- [ ] T013 Create `src/services/auth_service.py` - JWT token generation/validation, bcrypt password hashing (work factor 12)
- [ ] T014 Implement code parent authentication endpoint `/api/v1/auth/code-parent` in `src/api/v1/auth.py` per contracts (FR-032)
- [ ] T015 Create `src/middleware/permissions.py` - Permission checking middleware with role-based access control (13 roles per FR-022)
- [ ] T016 Create `src/utils/rate_limiter.py` - Redis-based rate limiting for code parent validation (5 attempts/hour per research.md)

### Audit Logging Infrastructure

- [ ] T017 Create `src/services/audit_service.py` - Action logging service writing to action_logs table (FR-051-055)
- [ ] T018 Implement log retention policy enforcement (2-year retention, anonymization after 2 years per FR-054-055)

### Error Handling & Validation

- [ ] T019 Create `src/utils/exceptions.py` - Custom exception classes (ValidationError, OCRError, AuthenticationError, PermissionError)
- [ ] T020 [P] Create `src/utils/validators.py` - Common validators (phone E.164 format, document size ≤10MB, file formats per FR-002)

**Checkpoint**: Foundation complete - database migrated, auth framework ready, logging infrastructure operational

---

## Phase 3: User Story 1 - Inscription Parent avec Documents et OCR (Priority: P1) 🎯 MVP

**Goal**: Enable parents to enroll students via WhatsApp/Telegram with automatic OCR document extraction

**Independent Test**: Parent creates complete enrollment from WhatsApp with 3 document uploads → OCR extracts data → parent validates → inscription generated with status "En attente de paiement"

**Endpoints**:
- POST /api/v1/enrollments (create)
- GET /api/v1/enrollments (list)
- GET /api/v1/enrollments/{id} (details)
- PATCH /api/v1/enrollments/{id} (update)
- POST /api/v1/enrollments/{id}/documents (upload)
- GET /api/v1/enrollments/{id}/documents (list docs)
- GET /api/v1/documents/{id} (OCR results)
- POST /api/v1/documents/{id} (validate OCR)

### Models for US1

- [ ] T021 [P] [US1] Create `src/models/enrollment.py` - Inscription model with fields per data-model.md (numero_unique, parent_id, nom_enfant, prenom_enfant, date_naissance, lieu_naissance, statut enum, montant_total/paye/restant, legacy link fields)
- [ ] T022 [P] [US1] Create `src/models/document.py` - Document model (inscription_id, type_document enum, fichier_path, format, statut_ocr enum, donnees_extraites JSON, donnees_validees JSON, confiance_ocr, valide_par_parent)

### OCR Service for US1

- [ ] T023 [US1] Create `src/services/ocr_service.py` - EasyOCR integration with French language support per research.md decision
- [ ] T024 [US1] Implement OCR preprocessing in `src/utils/ocr_utils.py` - Image enhancement (contrast, rotation correction, noise reduction)
- [ ] T025 [US1] Implement birth certificate OCR extraction - Extract nom, prénom, date_naissance, lieu_naissance (FR-003)
- [ ] T026 [US1] Implement baptism certificate OCR extraction - Extract date_bapteme, paroisse, nom_pretre (FR-004)
- [ ] T027 [US1] Implement transfer attestation OCR extraction - Extract paroisse_origine, annee_catechisme_precedente (FR-005)
- [ ] T028 [US1] Implement OCR confidence scoring and fallback to manual entry when confidence < 70% per research.md
- [ ] T029 [US1] Create async OCR worker `src/services/ocr_worker.py` - Background processing with status updates (en_attente → en_cours → succes/echec)

### Document Storage for US1

- [ ] T030 [US1] Create `src/services/document_service.py` - Document upload/download with MinIO integration
- [ ] T031 [US1] Implement MinIO hierarchical storage pattern: `{year}/{inscription_id}/{type}.{ext}` per research.md
- [ ] T032 [US1] Implement document validation (size ≤ 10MB, formats: PDF/JPG/PNG/HEIC per FR-002)
- [ ] T033 [US1] Generate pre-signed MinIO URLs (1-hour expiration) for document download

### Enrollment Service for US1

- [ ] T034 [US1] Create `src/services/enrollment_service.py` - Core enrollment orchestration
- [ ] T035 [US1] Implement create enrollment with numero_unique generation "CAT-YYYY-XXXX" (FR-007)
- [ ] T036 [US1] Implement duplicate detection via nom+prénom+date_naissance (FR-009)
- [ ] T037 [US1] Implement re-enrollment flow with data pre-fill from legacy catechumenes_2 table (FR-008)
- [ ] T038 [US1] Implement inscription state transitions (brouillon → en_attente_paiement → paiement_partiel → active → annulee)
- [ ] T039 [US1] Link new inscriptions to legacy parents via legacy_code_parent field per data-model.md migration notes

### API Endpoints for US1

- [ ] T040 [US1] Create `src/api/v1/enrollment.py` - POST /enrollments endpoint with CreateEnrollmentRequest validation
- [ ] T041 [US1] Implement GET /enrollments with pagination (limit/offset) and filters (annee, statut, classe_id)
- [ ] T042 [US1] Implement GET /enrollments/{id} returning InscriptionDetailed with documents and classe
- [ ] T043 [US1] Implement PATCH /enrollments/{id} for updating niveau, classe_id, statut
- [ ] T044 [US1] Implement POST /enrollments/{id}/documents - Multipart file upload with type_document validation
- [ ] T045 [US1] Implement GET /enrollments/{id}/documents - List all documents for enrollment
- [ ] T046 [US1] Implement GET /documents/{id} - Return DocumentWithOCR including OCR results and download URL
- [ ] T047 [US1] Implement POST /documents/{id} - Parent validates/corrects OCR data, sets valide_par_parent=true

### WhatsApp/Telegram Integration for US1

- [ ] T048 [US1] Create `src/orchestration/enrollment_orchestrator.py` - Conversational enrollment flow handler
- [ ] T049 [US1] Implement guided form steps in `src/orchestration/catechese_orchestrator.py` - Multi-step enrollment conversation
- [ ] T050 [US1] Handle document uploads from WhatsApp/Telegram messages, save to MinIO, trigger OCR
- [ ] T051 [US1] Present OCR results to parent via message with validation prompt (FR-006)
- [ ] T052 [US1] Implement session state persistence for multi-step enrollment (Redis + Supabase per constitution)

**Checkpoint**: User Story 1 complete - Parents can enroll via WhatsApp/Telegram with OCR document processing

---

## Phase 4: User Story 2 - Gestion des Paiements avec Validation (Priority: P1) 🎯 MVP

**Goal**: Enable parents to submit payments (cash/Mobile Money/receipt) and treasurers to validate them

**Independent Test**: Create inscription "En attente de paiement" → parent uploads Mobile Money screenshot → OCR extracts transaction details → treasurer validates → inscription status changes to "active"

**Endpoints**:
- POST /api/v1/enrollments/{id}/payments (submit)
- GET /api/v1/enrollments/{id}/payments (list for enrollment)
- GET /api/v1/payments/pending (treasurer queue)
- POST /api/v1/payments/{id}/validate (treasurer action)

### Models for US2

- [ ] T053 [P] [US2] Create `src/models/payment.py` - Paiement model (inscription_id, montant, mode_paiement enum [cash, orange_money, wave, free_money, recu_papier], reference, statut enum [en_attente_validation, valide, rejete], validateur_id, motif_rejet, metadata JSON)

### Mobile Money OCR for US2

- [ ] T054 [US2] Implement Mobile Money screenshot OCR in `src/services/ocr_service.py` - Template matching per research.md decision
- [ ] T055 [US2] Implement operator detection (Orange Money, Wave, Free Money) via color detection per research.md
- [ ] T056 [US2] Extract transaction details per operator template: reference, montant, date/heure (FR-057)
- [ ] T057 [US2] Implement regex validation patterns for transaction IDs per research.md (Orange: TX-\d{8}, Wave: [A-Z0-9]{12}, Free: FM-\d{8})

### Payment Service for US2

- [ ] T058 [US2] Create `src/services/payment_service.py` - Payment submission and validation orchestration
- [ ] T059 [US2] Implement payment submission with proof document linking (FR-012)
- [ ] T060 [US2] Implement partial payment support with solde_restant calculation (FR-018)
- [ ] T061 [US2] Generate QR code/reference for cash payments (FR-017)
- [ ] T062 [US2] Implement treasurer notification on new payment submission (FR-013)
- [ ] T063 [US2] Implement payment validation workflow - update inscription.statut to "active" when sum(paiements.montant WHERE statut='valide') = montant_total
- [ ] T064 [US2] Implement payment rejection with parent notification including motif_rejet (FR-015)
- [ ] T065 [US2] Record cash payment entries with sacristain/secretaire as validateur (FR-020)

### API Endpoints for US2

- [ ] T066 [US2] Create `src/api/v1/payments.py` - POST /enrollments/{id}/payments with SubmitPaymentRequest
- [ ] T067 [US2] Implement GET /enrollments/{id}/payments - List all payments for enrollment
- [ ] T068 [US2] Implement GET /payments/pending - Treasurer view with filters (mode_paiement, from_date, to_date) returning PaiementPending with parent info
- [ ] T069 [US2] Implement POST /payments/{id}/validate - Treasurer validates or rejects with motif_rejet
- [ ] T070 [US2] Add permission checks - Only tresorier_bureau/tresorier_adjoint_bureau can validate payments (FR-028)

### Payment Confirmation for US2

- [ ] T071 [US2] Implement parent confirmation message after payment validation (FR-019)
- [ ] T072 [US2] Include inscription summary in confirmation: numero_unique, nom_enfant, montant_paye, classe_assignee

**Checkpoint**: User Story 2 complete - Full payment workflow from submission to treasurer validation operational

---

## Phase 5: User Story 3 - Système de Profils et Permissions (Priority: P2)

**Goal**: Implement 13 user roles with specific permissions and role-based access control

**Independent Test**: Super Admin creates profiles for each role → verify each role accesses only authorized endpoints → unauthorized attempts logged in action_logs

**Endpoints**:
- POST /api/v1/profiles (create)
- GET /api/v1/profiles/{id} (details)
- PATCH /api/v1/profiles/{id} (update)

### Models for US3

- [ ] T073 [P] [US3] Create `src/models/profile.py` - ProfilUtilisateur model (user_id, nom, prenom, role enum [13 roles per FR-022], telephone, code_parent_hash, permissions JSON, actif, derniere_connexion)
- [ ] T074 [P] [US3] Define permission schema structure in `src/models/permissions.py` - JSON schema with inscriptions/paiements/profils/classes/rapports sections per data-model.md

### Permission System for US3

- [ ] T075 [US3] Implement role permission matrix in `src/services/profile_service.py` - Map each of 13 roles to permissions (FR-023-029)
- [ ] T076 [US3] Implement Sacristain permissions: create inscriptions, view inscriptions, view public info (FR-023)
- [ ] T077 [US3] Implement Secrétaire du Curé permissions: Sacristain permissions + receipt number entry (FR-024)
- [ ] T078 [US3] Implement Parent permissions: view own inscriptions, submit payments, view children's notes (FR-025)
- [ ] T079 [US3] Implement Curé permissions: read/write access to all modules (FR-026)
- [ ] T080 [US3] Implement Président/Secrétaire Général permissions: same as Curé (FR-027)
- [ ] T081 [US3] Implement Trésorier permissions: view/validate payments, generate reports (FR-028)
- [ ] T082 [US3] Implement Catéchiste permissions: view assigned class, search students, mark attendance (FR-029)
- [ ] T083 [US3] Implement permission checking in middleware - verify permissions JSON for each request
- [ ] T084 [US3] Log unauthorized access attempts in action_logs table (FR-030)

### Profile Management for US3

- [ ] T085 [US3] Create `src/services/profile_service.py` - Profile CRUD operations
- [ ] T086 [US3] Implement profile creation with automatic permission assignment based on role
- [ ] T087 [US3] Generate code_parent for parent profiles - 8-char format "CAT-XXXX", bcrypt hash storage (research.md)
- [ ] T088 [US3] Implement profile update with immediate permission changes (FR-031)
- [ ] T089 [US3] Implement profile deactivation (actif=false) without deletion

### API Endpoints for US3

- [ ] T090 [US3] Implement POST /api/v1/profiles in `src/api/v1/profiles.py` - Super Admin only, with CreateProfileRequest
- [ ] T091 [US3] Implement GET /api/v1/profiles/{id} - User can view own profile, admin can view all
- [ ] T092 [US3] Implement PATCH /api/v1/profiles/{id} - Super Admin can update role/permissions/actif

**Checkpoint**: User Story 3 complete - Role-based access control operational with 13 roles

---

## Phase 6: User Story 4 - Infrastructure SQLite Multi-Applications (Priority: P2)

**Goal**: Formalize multi-database architecture with application registry and backup/restore capabilities

**Independent Test**: Create data in each database → verify isolation → add test application with new DB → verify no cross-contamination → test selective restore

**Note**: Database structure already created in Phase 2 (Foundational) - this phase adds management capabilities

### Application Registry for US4

- [ ] T093 [US4] Populate core_system.db applications table with initial entries: sdb_cate (existing), temp_pages_system, core_system
- [ ] T094 [US4] Create `src/services/application_service.py` - Application registration and metadata management
- [ ] T095 [US4] Implement new application registration workflow - create new `{app_name}_app.db` file (FR-035)
- [ ] T096 [US4] Track database metrics: file size, last migration, last backup timestamp in applications table

### Backup & Restore for US4

- [ ] T097 [US4] Implement automatic backup in `src/database/sqlite_manager.py` - Daily backups with 30-day rotation (FR-038)
- [ ] T098 [US4] Generate timestamped backup files: `sdb_cate_YYYY-MM-DD_HH-MM-SS.sqlite`
- [ ] T099 [US4] Implement selective restore per database (FR-039)
- [ ] T100 [US4] Create backup verification - test restore on copy before confirming backup success

### Database Isolation Verification for US4

- [ ] T101 [US4] Implement cross-database reference validation in application layer - enforce referential integrity for user_id, inscription_id (FR-040)
- [ ] T102 [US4] Create isolation test suite - verify no data leakage between databases (FR-034)

**Checkpoint**: User Story 4 complete - Multi-database architecture formalized with backup/restore

---

## Phase 7: User Story 5 - Pages Temporaires pour Collecte de Documents (Priority: P2.5)

**Goal**: Staff can generate temporary secure URLs for document collection with 7-day expiration

**Independent Test**: Secrétaire creates temp page → parent accesses via code → uploads documents → secrétaire receives notification

**Endpoints**:
- POST /api/v1/temp-pages (create)
- GET /api/v1/temp-pages/{code} (access)

### Models for US5 (Temp Pages)

- [ ] T103 [P] [US5] Create `src/models/temp_page.py` - PageTemporaire model (page_id, code_acces 8-char, url_complete, utilisateur_associe_id, createur_id, objet enum, expires_at, statut enum, documents_collectes array)

### Temp Page Service for US5

- [ ] T104 [US5] Create `src/services/temp_page_service.py` - Temporary page generation and validation
- [ ] T105 [US5] Generate 8-character alphanumeric codes excluding ambiguous chars (0, O, 1, I, L) per data-model.md
- [ ] T106 [US5] Create URL format: `https://catechese.sdb.sn/temp/{code_acces}` (FR-041)
- [ ] T107 [US5] Set 7-day expiration by default, configurable via parameter (FR-043)
- [ ] T108 [US5] Implement auto-expiration background job - mark pages as "expiree" where expires_at < NOW
- [ ] T109 [US5] Implement single-use enforcement - mark as "utilisee" after first document submission (FR-043)
- [ ] T110 [US5] Notify creator (secrétaire/sacristain) when parent submits documents (FR-045)

### API Endpoints for US5

- [ ] T111 [US5] Create `src/api/v1/temp_pages.py` - POST /temp-pages endpoint for staff (sacristain, secrétaire roles only)
- [ ] T112 [US5] Implement GET /temp-pages/{code} - Public endpoint (no auth) with code validation
- [ ] T113 [US5] Link temp page document uploads to inscriptions via documents_collectes array

**Checkpoint**: User Story 5 complete - Temporary secure document collection pages operational

---

## Phase 8: User Story 6 - Consultation Catéchiste (Priority: P3)

**Goal**: Catechists can view assigned class roster, search students, and mark attendance

**Independent Test**: Assign class to catechist → catechist views class roster → searches for student → marks attendance

**Note**: Requires Classe model and catechist assignment workflow

### Models for US6

- [ ] T114 [P] [US6] Create `src/models/classe.py` - Classe model (classe_id, annee_catechetique, niveau enum, catechiste_id, catechiste_adjoint_id, capacite_max, effectif_actuel, horaire, salle, statut)

### Class Management for US6

- [ ] T115 [US6] Create `src/services/classe_service.py` - Class creation and assignment
- [ ] T116 [US6] Implement catechist assignment - link catechiste_id to profil_utilisateurs.user_id WHERE role='catechiste'
- [ ] T117 [US6] Auto-update effectif_actuel via SQL trigger when inscription.classe_id changes (per data-model.md)
- [ ] T118 [US6] Enforce capacity constraint: effectif_actuel ≤ capacite_max

### Student Search for US6

- [ ] T119 [US6] Implement student search in `src/services/enrollment_service.py` - Search by nom, prenom, numero_unique (FR-046)
- [ ] T120 [US6] Implement search result highlighting and relevance sorting (FR-047)
- [ ] T121 [US6] Implement catechist scope filtering - default to assigned class, optional "search all" with permission (FR-048)

### Attendance Tracking for US6

- [ ] T122 [US6] Create `src/models/attendance.py` - Attendance model (attendance_id, inscription_id, date, statut enum [present, absent, retard], catechiste_id, timestamp)
- [ ] T123 [US6] Create `src/services/attendance_service.py` - Attendance marking and history
- [ ] T124 [US6] Implement bulk attendance marking for entire class

### API Endpoints for US6

- [ ] T125 [US6] Create `src/api/v1/classes.py` - GET /classes endpoint for listing
- [ ] T126 [US6] Implement GET /classes/{id}/roster - Return list of students with inscription status
- [ ] T127 [US6] Implement GET /classes/{id}/attendance - Attendance history for class
- [ ] T128 [US6] Implement POST /attendance - Catechist marks attendance for students

**Checkpoint**: User Story 6 complete - Catechist consultation and attendance tracking operational

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories and deployment readiness

### Documentation & Deployment

- [ ] T129 [P] Update `CLAUDE.md` with enrollment system usage instructions
- [ ] T130 [P] Create `README_ENROLLMENT.md` - Feature overview, architecture diagram, deployment guide
- [ ] T131 [P] Generate API documentation from OpenAPI spec: `redoc-cli bundle contracts/enrollment-api.yaml -o docs/api.html`
- [ ] T132 Validate quickstart.md instructions - run through full setup on clean environment

### Performance Optimization

- [ ] T133 Add database indexes per data-model.md - 15 indexes across inscriptions, documents, paiements, profil_utilisateurs
- [ ] T134 Implement database connection pooling verification - ensure 20 connections per database
- [ ] T135 Optimize OCR processing - implement image caching to avoid re-processing same documents

### Security Hardening

- [ ] T136 Run security audit on auth endpoints - verify rate limiting, bcrypt work factor, JWT expiration
- [ ] T137 Implement SQL injection prevention - parameterized queries throughout
- [ ] T138 Add HTTPS enforcement in production - reject HTTP requests

### Monitoring & Observability

- [ ] T139 Add enrollment-specific metrics: OCR success rate, payment validation time, inscription completion rate
- [ ] T140 Implement health check extensions in `/health` endpoint - check SQLite databases, MinIO, OCR worker status
- [ ] T141 Create Grafana dashboard config for enrollment metrics

### Data Migration & Legacy Integration

- [ ] T142 Create CSV import script `scripts/import_legacy_data.py` per research.md - Import 509 students, 341 parents from existing sdb_cate.sqlite legacy tables
- [ ] T143 Implement legacy parent lookup - query parents_2 by Code_Parent when creating new inscriptions
- [ ] T144 Create data migration validation report - verify all legacy data accessible via new API

### GDPR Compliance

- [ ] T145 Implement log anonymization job - run monthly to anonymize logs > 2 years old (FR-055)
- [ ] T146 Create GDPR data export endpoint - parent can request all their data as JSON
- [ ] T147 Implement data deletion workflow - parent can request account deletion with grace period

### Admin Notification System

- [ ] T148 Implement WAHA notification service per CLAUDE.md execution rule - send summary to admin (221765005555) after significant operations
- [ ] T149 Create execution logger per CLAUDE.md auto-save rule - save summaries to `execution_logs/` as markdown

**Checkpoint**: System production-ready with all polish tasks complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately
- **Foundational (Phase 2)**: Depends on Setup - **BLOCKS all user stories**
- **User Story 1 (Phase 3)**: Depends on Foundational completion - Can start in parallel with other stories
- **User Story 2 (Phase 4)**: Depends on Foundational completion - Can start in parallel with other stories
- **User Story 3 (Phase 5)**: Depends on Foundational completion - Can start in parallel with other stories
- **User Story 4 (Phase 6)**: Depends on Foundational completion - Extends database infrastructure
- **User Story 5 (Phase 7)**: Depends on Foundational completion - Can start in parallel
- **User Story 6 (Phase 8)**: Depends on Foundational completion + US1 (needs Inscription model)
- **Polish (Phase 9)**: Depends on desired user stories being complete

### User Story Dependencies

```
Foundational (Phase 2) ────┬──→ US1 (P1 MVP) ──┐
                           ├──→ US2 (P1 MVP) ──┼──→ MVP Complete
                           ├──→ US3 (P2) ──────┘
                           ├──→ US4 (P2)
                           ├──→ US5 (P2.5)
                           └──→ US6 (P3) ──────→ Requires US1
```

- **US1 & US2**: Both P1 MVP - should be completed first, can work in parallel
- **US3, US4, US5**: All P2 - can work in parallel after Foundational
- **US6**: P3 - requires US1 Inscription model, can work after US1 complete

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Within Foundational Phase 2**:
- T009 (temp_pages_system.db) || T010 (core_system.db) - Different databases
- T011 (base.py) || T012 (legacy.py) - Different files
- T019 (exceptions.py) || T020 (validators.py) - Different files

**Within User Story 1**:
- T021 (enrollment.py) || T022 (document.py) - Different model files
- T025 (birth cert OCR) || T026 (baptism cert OCR) || T027 (transfer OCR) - Different OCR extractors

**Within User Story 2**:
- T055 (operator detection) || T056 (transaction extraction) - Different OCR components

**Cross-Story Parallelization** (after Foundational complete):
- Entire US1 team || Entire US2 team || Entire US3 team - Different feature domains

---

## Parallel Example: MVP (US1 + US2)

```bash
# After Foundational Phase 2 completes, launch MVP stories in parallel:

# Developer A: User Story 1 (Enrollment)
Task Group A1: T021, T022 (models in parallel)
Task Group A2: T023-T029 (OCR service)
Task Group A3: T030-T033 (document storage)
Task Group A4: T034-T039 (enrollment service)
Task Group A5: T040-T047 (API endpoints)
Task Group A6: T048-T052 (WhatsApp integration)

# Developer B: User Story 2 (Payments)
Task Group B1: T053 (model)
Task Group B2: T054-T057 (Mobile Money OCR)
Task Group B3: T058-T065 (payment service)
Task Group B4: T066-T070 (API endpoints)
Task Group B5: T071-T072 (confirmations)

# Both stories integrate at shared touchpoints:
# - Inscription.statut (US1 creates, US2 updates)
# - Document.type_document='preuve_paiement' (US2 uses US1's document model)
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. ✅ Complete Phase 1: Setup (T001-T004)
2. ✅ Complete Phase 2: Foundational (T005-T020) - **CRITICAL BLOCKER**
3. ✅ Complete Phase 3: US1 Enrollment (T021-T052)
4. ✅ Complete Phase 4: US2 Payments (T053-T072)
5. **STOP and VALIDATE**: Test full enrollment+payment workflow end-to-end
6. Deploy MVP to production

**MVP Success Criteria**:
- SC-001: Parents complete enrollment in < 10 minutes ✓
- SC-002: OCR accuracy > 85% ✓
- SC-003: Payment validation < 2 minutes ✓
- SC-004: Process time reduced from 30min to 10min ✓

### Incremental Delivery

**After MVP**:
1. Add US3 (Profiles P2) → Test independently → Deploy
   - Enables proper role separation and security
2. Add US4 (SQLite P2) → Test independently → Deploy
   - Formalizes multi-app architecture for future growth
3. Add US5 (Temp Pages P2.5) → Test independently → Deploy
   - Adds convenience feature for document collection
4. Add US6 (Catechist P3) → Test independently → Deploy
   - Completes catechist workflow
5. Add US7+ (P4 Future modules) → Iterative releases

### Parallel Team Strategy

**With 3 developers after Foundational phase**:
- **Dev 1**: US1 (Enrollment) - Core MVP feature
- **Dev 2**: US2 (Payments) - Core MVP feature
- **Dev 3**: US3 (Profiles) - Can start in parallel, integrates later

**Stories complete independently, merge sequentially by priority**

---

## Task Count Summary

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 16 tasks ⚠️ **BLOCKS ALL STORIES**
- **Phase 3 (US1 Enrollment P1)**: 32 tasks 🎯 **MVP**
- **Phase 4 (US2 Payments P1)**: 20 tasks 🎯 **MVP**
- **Phase 5 (US3 Profiles P2)**: 20 tasks
- **Phase 6 (US4 SQLite P2)**: 10 tasks
- **Phase 7 (US5 Temp Pages P2.5)**: 11 tasks
- **Phase 8 (US6 Catechist P3)**: 15 tasks
- **Phase 9 (Polish)**: 21 tasks

**Total**: 149 tasks

**MVP Scope** (Phase 1+2+3+4): 72 tasks (48% of total)

**Parallel Opportunities**: 25+ tasks marked [P] enable significant parallelization

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label (US1-US6) maps task to user story for traceability
- Each user story is independently testable per spec acceptance scenarios
- Stop at any checkpoint to validate story independently
- Foundational phase (T005-T020) is critical path - prioritize completion
- MVP = US1 + US2 (enrollment + payment) delivers immediate value
- Constitution compliance embedded throughout (type hints, audit logging, GDPR, security)
- Legacy data integration preserves existing 509 students, 341 parents
- Tests not included per specification (no TDD requirement stated)

---

**Generated**: 2025-10-11
**Feature Branch**: `002-syst-me-de`
**Specification**: [spec.md](./spec.md) (6 user stories, 59 functional requirements)
**Implementation Plan**: [plan.md](./plan.md) (research decisions, architecture)
**Data Model**: [data-model.md](./data-model.md) (8 entities, legacy integration)
**API Contracts**: [contracts/enrollment-api.yaml](./contracts/enrollment-api.yaml) (18 endpoints, OpenAPI 3.0)
