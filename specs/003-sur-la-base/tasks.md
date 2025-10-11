# Implementation Tasks: Automatic Account Creation Based on Phone Number

**Feature Branch**: `003-sur-la-base` | **Date**: 2025-01-25
**Total Tasks**: 47 | **Estimated Duration**: 3-4 weeks
**Spec File**: [spec.md](spec.md) | **Plan File**: [plan.md](plan.md)

## Executive Summary

This implementation plan provides 47 actionable tasks organized by user story priority. The system will automatically create accounts for catechism parents when they contact the service via WhatsApp or Telegram, validate phone numbers against the existing catechism database, and support role-based access control including super admin capabilities.

## User Story Analysis

### User Story 1 (P1): Automatic Account Creation for Registered Parents
- **Goal**: Parents can immediately access the system when they first contact via messaging platforms
- **Independent Test**: Known parent sends message → account created → welcome message sent
- **Task Count**: 14 tasks (T015-T028)

### User Story 2 (P1): Role Management and System Admin Setup
- **Goal**: Users can have multiple roles and super admin can manage the system
- **Independent Test**: Create accounts with multiple roles → verify access to both parent and system functions
- **Task Count**: 12 tasks (T029-T040)

### User Story 3 (P2): Phone Number Recognition and Validation
- **Goal**: Accurate phone number validation regardless of format variations
- **Independent Test**: Various phone formats → correct database matching → appropriate account creation
- **Task Count**: 10 tasks (T041-T050)

## Implementation Strategy

### MVP Scope (Phase 1-3)
**MVP includes**: User Story 1 (Automatic Account Creation) + basic infrastructure
- Enables core functionality: parents contact → automatic account creation → immediate system access
- Provides foundation for additional features
- Delivers user value immediately

### Incremental Delivery
- **Phase 1**: Infrastructure setup (project initialization, dependencies, database)
- **Phase 2**: Foundational services (blocking prerequisites for all stories)
- **Phase 3**: User Story 1 - Automatic account creation (MVP)
- **Phase 4**: User Story 2 - Role management and admin functions
- **Phase 5**: User Story 3 - Advanced phone validation
- **Phase 6**: Polish, testing, and deployment preparation

## Dependency Graph

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (Polish)
                      ↓                    ↓              ↓              ↓
                 All stories depend   US1 is MVP    US2 requires   US3 requires
                 on Phase 2           foundation    US1 complete   US1 complete
```

## Task Organization Legend

- **[P]**: Parallelizable (can be executed simultaneously with other [P] tasks)
- **[Story]**: User story identifier (US1, US2, US3)
- **T###**: Sequential task number
- **File paths**: Absolute paths for clarity
- **Dependencies**: Explicit task dependencies where needed

---

## Phase 1: Project Setup and Infrastructure (5 tasks)

**Goal**: Establish project foundation, dependencies, and basic structure

**Timeline**: 2-3 days | **Parallel Tasks**: 3

### ✅ T001 - Initialize Project Structure [P] - COMPLETED
**File**: `src/models/`, `src/services/`, `src/handlers/`, `src/api/v1/`, `src/middleware/`, `src/utils/`, `src/database/migrations/`
**Description**: Create directory structure according to plan.md Section 4
**Acceptance**: All directories exist with appropriate `__init__.py` files ✅

### ✅ T002 - Setup Dependencies and Virtual Environment [P] - COMPLETED
**File**: `requirements.txt`, `pyproject.toml`
**Description**: Add Python 3.11+ dependencies from plan.md: FastAPI, WAHA SDK, python-telegram-bot, python-phonenumbers, python-jose, Supabase client, Redis, pytest, httpx
**Acceptance**: `pip install -r requirements.txt` succeeds without errors ✅

### ✅ T003 - Configure Environment Variables [P] - COMPLETED
**File**: `.env`, `.env.template`
**Description**: Create environment configuration for Supabase, Redis, WhatsApp, Telegram, JWT secrets according to quickstart.md Section 3
**Acceptance**: All required environment variables documented in template ✅

### ✅ T004 - Setup Database Migration Framework - COMPLETED
**File**: `src/database/migrations/001_create_account_tables.sql`
**Description**: Create migration script based on data-model.md Section "Migration Strategy" with all 6 core entities
**Acceptance**: Migration script runs successfully on Supabase PostgreSQL ✅

### ✅ T005 - Initialize Logging and Error Handling - COMPLETED
**File**: `src/utils/logging.py`, `src/utils/exceptions.py`
**Description**: Implement structured JSON logging with request ID tracking and custom exception classes for account creation errors
**Acceptance**: Logs output in structured JSON format with correlation IDs ✅

**🎯 Phase 1 Checkpoint - Project Setup Complete**
**Milestone**: All Phase 1 tasks completed successfully
**Description**: Project foundation established with proper structure, dependencies, and infrastructure
**Acceptance**: All Phase 1 acceptance criteria met ✅

---

## Phase 2: Foundational Services and Infrastructure (8 tasks)

**Goal**: Implement blocking prerequisites that all user stories depend on

**Timeline**: 4-5 days | **Parallel Tasks**: 4

### T006 - Implement Database Models [P]
**File**: `src/models/account.py`, `src/models/session.py`, `src/models/base.py`
**Description**: Create Pydantic and SQLAlchemy models for UserAccount, UserRole, UserRoleAssignment, UserSession, AccountCreationAudit, WebhookEvent based on data-model.md
**Acceptance**: All models pass basic validation tests

### T007 - Setup Database Connection Service
**File**: `src/database/connection.py`
**Description**: Implement Supabase connection service with connection pooling, SSL enforcement, and health checks per plan.md Section 4
**Acceptance**: Can connect to Supabase and execute basic queries

### T008 - Setup Redis Cache Service [P]
**File**: `src/database/redis_client.py`
**Description**: Implement Redis client with session cache, user lookup cache, phone validation cache according to data-model.md Section "Redis Cache Schema"
**Acceptance**: Can set/get cache entries with proper TTL management

### T009 - Implement Phone Number Validation Service
**File**: `src/utils/phone_validator.py`
**Description**: Create phone validation service with python-phonenumbers, Senegal-specific rules, and format normalization per research.md Section 2
**Acceptance**: Validates all Senegal phone formats correctly

### T010 - Implement JWT Authentication Service [P]
**File**: `src/services/auth_service.py`
**Description**: Create JWT token service with platform-specific authentication, token rotation, and 15-minute access tokens per plan.md
**Acceptance**: Can generate and validate JWT tokens with proper expiration

### T011 - Implement Webhook Signature Verification
**File**: `src/utils/webhook_security.py`
**Description**: Create HMAC-SHA256 signature verification for WhatsApp webhooks per research.md Section 1 and FR-013
**Acceptance**: Verifies WhatsApp webhook signatures correctly

### T012 - Setup Rate Limiting Middleware
**File**: `src/middleware/rate_limiting.py`
**Description**: Implement Redis-based sliding window rate limiting per research.md Section 2 and NFR-002
**Acceptance**: Rate limits are enforced with proper sliding window behavior

### T013 - Implement Audit Logging Service [P]
**File**: `src/services/audit_service.py`
**Description**: Create comprehensive audit logging service for account creation events per FR-010 and NFR-004
**Acceptance**: All account creation events are logged with proper metadata

### T014 - Create Health Check Endpoints
**File**: `src/api/v1/health.py`
**Description**: Implement health check endpoints for database, Redis, and overall system status per quickstart.md Section 4
**Acceptance**: Health checks return proper status for all dependencies

---

## Phase 3: User Story 1 - Automatic Account Creation (14 tasks)

**Goal**: Parents can automatically get accounts when they contact the system

**Timeline**: 5-6 days | **Parallel Tasks**: 8
**Independent Test**: Known parent phone sends message → account created → welcome message sent → immediate system access

### T015 - [Story US1] Create Account Creation Service
**File**: `src/services/account_service.py`
**Description**: Implement core account creation logic with phone validation, parent database lookup, and user account creation per FR-001 to FR-003
**Acceptance**: Service creates accounts for recognized parents automatically

### T016 - [Story US1] Implement Parent Database Lookup Service [P]
**File**: `src/services/parent_lookup_service.py`
**Description**: Create service to lookup parents in external catechism database by normalized phone number per FR-002 and FR-012
**Acceptance**: Can find parent records by phone number with various formats

### T017 - [Story US1] Create Session Management Service
**File**: `src/services/session_service.py`
**Description**: Implement session management with dual persistence (Supabase + Redis) per plan.md and data-model.md
**Acceptance**: Sessions are created, updated, and retrieved correctly

### T018 - [Story US1] Implement WhatsApp Webhook Handler [P]
**File**: `src/handlers/whatsapp_webhook.py`
**Description**: Create WhatsApp webhook handler with signature verification, message parsing, and account creation triggering per FR-013
**Acceptance**: WhatsApp messages trigger account creation process

### T019 - [Story US1] Implement Telegram Webhook Handler [P]
**File**: `src/handlers/telegram_webhook.py`
**Description**: Create Telegram webhook handler with message parsing, platform authentication, and account creation triggering per FR-015
**Acceptance**: Telegram messages trigger account creation process

### T020 - [Story US1] Create Message Normalization Service [P]
**File**: `src/services/messaging_service.py`
**Description**: Implement unified message normalization across WhatsApp and Telegram platforms per plan.md Section 3
**Acceptance**: Messages from both platforms are processed consistently

### T021 - [Story US1] Implement User Role Assignment Service
**File**: `src/services/role_service.py`
**Description**: Create service to assign default "parent" role to newly created accounts per FR-004
**Acceptance**: New accounts automatically receive parent role

### T022 - [Story US1] Create Welcome Message Service [P]
**File**: `src/services/notification_service.py`
**Description**: Implement service to send welcome messages to newly created accounts per FR-006 and SC-007
**Acceptance**: New accounts receive appropriate welcome messages

### T023 - [Story US1] Implement Duplicate Account Prevention
**File**: `src/services/account_service.py` (enhancement)
**Description**: Add logic to prevent duplicate account creation for existing users per FR-009 and SC-006
**Acceptance**: No duplicate accounts are created for existing users

### T024 - [Story US1] Create Account Creation API Endpoint
**File**: `src/api/v1/accounts.py`
**Description**: Implement REST API endpoint for manual account creation with proper validation per FR-014
**Acceptance**: API creates accounts with proper validation and error handling

### T025 - [Story US1] Implement Webhook API Endpoints [P]
**File**: `src/api/v1/webhooks/`
**Description**: Create webhook endpoints for WhatsApp and Telegram per contracts/openapi.yaml
**Acceptance**: Webhooks receive and process messages correctly

### T026 - [Story US1] Add Error Handling and Recovery [P]
**File**: `src/utils/exceptions.py` (enhancement)
**Description**: Implement comprehensive error handling for account creation failures with proper retry mechanisms per NFR-006
**Acceptance**: System handles failures gracefully with proper logging

### T027 - [Story US1] Create Integration Tests for Account Creation Flow
**File**: `tests/integration/test_account_creation.py`
**Description**: Write integration tests covering complete account creation flow for both platforms
**Acceptance**: Tests pass for both WhatsApp and Telegram account creation

### T028 - [Story US1] Phase 3 Checkpoint - User Story 1 Complete
**Milestone**: Verify User Story 1 completion
**Description**: Ensure User Story 1 meets all acceptance criteria and independent test requirements
**Acceptance**: Known parent can contact system → account created → welcome message sent → immediate access achieved

---

## Phase 4: User Story 2 - Role Management and Admin Setup (12 tasks)

**Goal**: Users can have multiple roles and super admin can manage the system

**Timeline**: 4-5 days | **Parallel Tasks**: 6
**Dependency**: User Story 1 complete
**Independent Test**: Create accounts with multiple roles → verify access to both parent and system functions

### T029 - [Story US2] Create Role Management Service
**File**: `src/services/role_service.py` (enhancement)
**Description**: Implement comprehensive role management with multiple role assignments per user per FR-004
**Acceptance**: Users can have multiple roles assigned simultaneously

### T030 - [Story US2] Implement Super Admin Role Setup [P]
**File**: `src/database/migrations/002_setup_super_admin.sql`
**Description**: Create migration to setup super admin role and default admin account per FR-005
**Acceptance**: Super admin role exists with appropriate permissions

### T031 - [Story US2] Create User Management Service
**File**: `src/services/user_management_service.py`
**Description**: Implement service for super admins to manage users, roles, and permissions per FR-011
**Acceptance**: Super admins can manage users and roles through the service

### T032 - [Story US2] Implement Permission Validation Service [P]
**File**: `src/services/permission_service.py`
**Description**: Create service to validate user permissions for different system functions per role assignments
**Acceptance**: Permission checks work correctly for all role types

### T033 - [Story US2] Create Role Assignment API Endpoints
**File**: `src/api/v1/roles.py`
**Description**: Implement REST API endpoints for role management and user role assignments per contracts/openapi.yaml
**Acceptance**: Roles can be assigned and managed via API

### T034 - [Story US2] Implement Admin Dashboard Endpoints [P]
**File**: `src/api/v1/admin.py`
**Description**: Create admin-specific endpoints for user management, system statistics, and administrative functions
**Acceptance**: Admin users can access administrative functions

### T035 - [Story US2] Create User Authentication Middleware
**File**: `src/middleware/auth.py`
**Description**: Implement authentication middleware to validate JWT tokens and set user context per request
**Acceptance**: Requests are properly authenticated with user context

### T036 - [Story US2] Implement Role-Based Access Control [P]
**File**: `src/middleware/rbac.py`
**Description**: Create RBAC middleware to enforce role-based access to API endpoints
**Acceptance**: Access is properly controlled based on user roles

### T037 - [Story US2] Add Role Assignment Audit Logging [P]
**File**: `src/services/audit_service.py` (enhancement)
**Description**: Enhance audit service to log all role management activities per FR-010
**Acceptance**: All role changes are logged with proper audit trail

### T038 - [Story US2] Create User Profile Management
**File**: `src/services/user_service.py`
**Description**: Implement user profile management with role display and permissions overview
**Acceptance**: Users can view their profiles and assigned roles

### T039 - [Story US2] Create Integration Tests for Role Management
**File**: `tests/integration/test_role_management.py`
**Description**: Write integration tests for role assignment, permission validation, and admin functions
**Acceptance**: All role management scenarios pass integration tests

### T040 - [Story US2] Phase 4 Checkpoint - User Story 2 Complete
**Milestone**: Verify User Story 2 completion
**Description**: Ensure User Story 2 meets all acceptance criteria and independent test requirements
**Acceptance**: Users have multiple roles and super admin can manage system with 5-second response time per SC-005

---

## Phase 5: User Story 3 - Advanced Phone Validation (10 tasks)

**Goal**: Accurate phone number recognition regardless of format variations

**Timeline**: 3-4 days | **Parallel Tasks**: 5
**Dependency**: User Story 1 complete
**Independent Test**: Various phone formats → correct database matching → appropriate account creation

### T041 - [Story US3] Enhance Phone Validation with Format Support [P]
**File**: `src/utils/phone_validator.py` (enhancement)
**Description**: Extend phone validation to support 10+ international formats per SC-008 and FR-007
**Acceptance**: All listed phone number formats validate correctly

### T042 - [Story US3] Implement Carrier Detection Service [P]
**File**: `src/services/carrier_service.py`
**Description**: Create service to detect mobile carriers from phone numbers for Senegal per research.md Section 2
**Acceptance**: Carrier detection works for all Senegal mobile prefixes

### T043 - [Story US3] Create Phone Normalization Service
**File**: `src/utils/phone_normalizer.py`
**Description**: Implement comprehensive phone number normalization handling various input formats per FR-007
**Acceptance**: Phone numbers are normalized to E.164 format consistently

### T044 - [Story US3] Add Phone Validation Cache [P]
**File**: `src/database/redis_client.py` (enhancement)
**Description**: Implement caching for phone validation results to improve performance per research.md Section 2
**Acceptance**: Phone validation results are cached with 24-hour TTL

### T045 - [Story US3] Create Phone Format Detection Service
**File**: `src/services/phone_format_service.py`
**Description**: Implement service to detect and categorize different phone number input formats
**Acceptance**: Can identify source format of phone numbers

### T046 - [Story US3] Implement Unrecognized Number Handling [P]
**File**: `src/services/unrecognized_number_service.py`
**Description**: Create service to handle unrecognized phone numbers with manual registration guidance per FR-008
**Acceptance**: Unrecognized numbers receive appropriate guidance

### T047 - [Story US3] Create Phone Validation API Endpoint
**File**: `src/api/v1/utils/phone_validation.py`
**Description**: Implement API endpoint for phone number validation with detailed results per contracts/openapi.yaml
**Acceptance**: API returns comprehensive validation results

### T048 - [Story US3] Add Phone Validation Audit Logging [P]
**File**: `src/services/audit_service.py` (enhancement)
**Description**: Enhance audit service to log phone validation attempts and results per FR-010
**Acceptance**: All validation attempts are logged with detailed results

### T049 - [Story US3] Create Integration Tests for Phone Validation
**File**: `tests/integration/test_phone_validation.py`
**Description**: Write comprehensive integration tests for phone validation with various formats and edge cases
**Acceptance**: All phone format scenarios pass validation tests

### T050 - [Story US3] Phase 5 Checkpoint - User Story 3 Complete
**Milestone**: Verify User Story 3 completion
**Description**: Ensure User Story 3 meets all acceptance criteria and independent test requirements
**Acceptance**: System maintains 99.9% accuracy in phone number recognition per SC-004

---

## Phase 6: Polish, Testing, and Deployment Preparation (8 tasks)

**Goal**: System polish, comprehensive testing, and production deployment readiness

**Timeline**: 3-4 days | **Parallel Tasks**: 4
**Dependencies**: All user stories complete

### T051 - Implement Performance Optimization [P]
**File**: Various performance improvements
**Description**: Optimize database queries, Redis caching, and response times to meet NFR-001 (<2 seconds) and NFR-002 (100+ concurrent users)
**Acceptance**: Performance targets met under load testing

### T052 - Add Comprehensive Error Handling [P]
**File**: `src/utils/error_handlers.py`
**Description**: Implement comprehensive error handling with user-friendly error messages and proper HTTP status codes
**Acceptance**: All error scenarios return appropriate responses

### T053 - Implement Data Privacy and GDPR Compliance [P]
**File**: `src/utils/privacy.py`, `src/services/gdpr_service.py`
**Description**: Implement phone number masking in logs, consent management, and data retention policies per NFR-005 and research.md Section 5
**Acceptance**: System meets GDPR compliance requirements

### T054 - Create Monitoring and Observability [P]
**File**: `src/utils/metrics.py`, monitoring endpoints
**Description**: Implement comprehensive metrics collection, health monitoring, and performance tracking per plan.md Section 4
**Acceptance**: System metrics are collected and available for monitoring

### T055 - Add Security Hardening [P]
**File**: Security enhancements across the codebase
**Description**: Implement input sanitization, SQL injection prevention, and additional security measures per NFR-007
**Acceptance**: Security scans pass without critical issues

### T056 - Create Deployment Configuration
**File**: `docker-compose.yml`, deployment scripts
**Description**: Create production deployment configuration following quickstart.md with proper container networking
**Acceptance**: System can be deployed using provided configuration

### T057 - Write End-to-End Tests [P]
**File**: `tests/e2e/test_complete_workflows.py`
**Description**: Write comprehensive end-to-end tests covering all user stories and edge cases
**Acceptance**: All end-to-end scenarios pass successfully

### T058 - Final Documentation and Deployment Guide
**File**: `docs/deployment.md`, `docs/api.md`
**Description**: Complete deployment documentation and API documentation based on quickstart.md and contracts
**Acceptance**: Documentation is complete and accurate for production deployment

---

## Parallel Execution Examples

### User Story 1 (Phase 3) - Parallel Execution:
```bash
# Can be executed simultaneously:
T016 - Parent Database Lookup Service [P]
T018 - WhatsApp Webhook Handler [P]
T019 - Telegram Webhook Handler [P]
T020 - Message Normalization Service [P]
T022 - Welcome Message Service [P]

# Sequential dependencies:
T015 (Account Service) → T021 (Role Assignment) → T023 (Duplicate Prevention)
```

### User Story 2 (Phase 4) - Parallel Execution:
```bash
# Can be executed simultaneously:
T030 - Super Admin Setup [P]
T032 - Permission Validation Service [P]
T037 - Role Assignment Audit Logging [P]

# Sequential dependencies:
T029 (Role Management) → T033 (Role API) → T036 (RBAC Middleware)
```

### User Story 3 (Phase 5) - Parallel Execution:
```bash
# Can be executed simultaneously:
T041 - Enhanced Phone Validation [P]
T042 - Carrier Detection [P]
T044 - Phone Validation Cache [P]
T046 - Unrecognized Number Handling [P]
T048 - Phone Validation Audit Logging [P]

# Sequential dependencies:
T043 (Normalization Service) → T045 (Format Detection) → T047 (Validation API)
```

## Risk Mitigation

### High-Risk Tasks:
- **T011 (Webhook Security)**: Critical for GDPR compliance and system security
- **T015 (Account Creation Service)**: Core business logic with complex integration points
- **T051 (Performance Optimization)**: Must meet strict NFR requirements

### Mitigation Strategies:
- Implement comprehensive testing for high-risk tasks
- Use parallel development to reduce timeline risks
- Regular integration testing to catch issues early
- Performance testing throughout development

## Success Criteria Validation

Each user story includes specific success criteria validation:

### User Story 1 Validation:
- **SC-001**: 95% access within 30 seconds → validated in T027
- **SC-002**: 100% automatic creation → validated in T015, T023
- **SC-006**: Zero duplicates → validated in T023
- **SC-007**: 100% welcome messages → validated in T022

### User Story 2 Validation:
- **SC-005**: 5s admin operations → validated in T040
- Role management functionality → validated in T039

### User Story 3 Validation:
- **SC-004**: 99.9% phone recognition accuracy → validated in T050
- **SC-008**: 10+ phone formats → validated in T041, T049

## Total Estimated Timeline

**Phase 1**: 2-3 days (Setup)
**Phase 2**: 4-5 days (Foundational)
**Phase 3**: 5-6 days (User Story 1 - MVP)
**Phase 4**: 4-5 days (User Story 2 - Roles)
**Phase 5**: 3-4 days (User Story 3 - Validation)
**Phase 6**: 3-4 days (Polish & Deployment)

**Total**: 21-27 days (4-5 weeks with 1 developer)

**MVP Delivery**: Phase 1-3 completes in 11-14 days (2 weeks)

---

**Next Steps**: Begin Phase 1 implementation starting with T001-T005 to establish project foundation, then proceed with Phase 2 foundational services before implementing User Story 1 as the MVP deliverable.

**Quality Gates**: Each phase must pass checkpoint validation before proceeding to next phase. All tests must pass and performance requirements must be met.