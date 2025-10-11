# Feature Specification: Automatic Account Creation Based on Phone Number

**Feature Branch**: `003-sur-la-base`
**Created**: 2025-10-11
**Updated**: 2025-01-25
**Status**: Updated - Critical Issues Resolved
**Input**: User description: "Sur la base du numéro qui contacte le service FFG à travers Telegram ou WhatsApp, créer un compte si le numéro appartient à la base de données des parents de la catéchèse. Cela permet de pouvoir déjà interagir avec le service. Permettre aussi de cumuler rôle de parent et rôle système. Le superadmin aussi doit être défini pour qu'il puisse permettre de faire des opérations."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Account Creation for Registered Parents (Priority: P1)

When a parent who is already in the catechism database contacts the service for the first time via Telegram or WhatsApp, the system automatically creates a user account using their phone number, allowing them to immediately start interacting with the enrollment system without manual registration.

**Why this priority**: This eliminates friction for existing parents and enables immediate service access, which is critical for user adoption and satisfaction.

**Independent Test**: Can be tested by having a known parent phone number send a message to the bot and verifying automatic account creation and immediate system interaction capability.

**Acceptance Scenarios**:

1. **Given** a parent from the catechism database contacts the service for the first time via Telegram/WhatsApp, **When** their phone number is recognized, **Then** an account is automatically created and a welcome message is sent with available options.

2. **Given** an existing parent tries to interact with the service without an account, **When** their phone number matches the database, **Then** they receive immediate access to appropriate parent functions.

---

### User Story 2 - Role Management and System Admin Setup (Priority: P1)

The system allows users to have multiple roles (parent + system roles) and includes a super admin who can perform administrative operations and manage other users.

**Why this priority**: Role management is essential for proper system governance and administrative control over the catechism enrollment process.

**Independent Test**: Can be tested by creating accounts with multiple role assignments and verifying that users can access both parent and system functions appropriately.

**Acceptance Scenarios**:

1. **Given** a super admin account exists, **When** they log into the system, **Then** they have access to administrative functions and user management capabilities.

2. **Given** a parent user also has system privileges, **When** they interact with the system, **Then** they can access both parent-specific functions and their assigned system administrative functions.

---

### User Story 3 - Phone Number Recognition and Validation (Priority: P2)

The system validates phone numbers against the existing parent database to determine if automatic account creation should occur, handling international format variations and ensuring accurate matching.

**Why this priority**: Accurate phone number recognition is crucial for the automatic account creation feature to work reliably.

**Independent Test**: Can be tested by attempting account creation with various phone number formats and verifying correct database matching and account creation.

**Acceptance Scenarios**:

1. **Given** a contact message is received, **When** the phone number is processed, **Then** it correctly matches against the parent database regardless of format variations.

2. **Given** a phone number is not found in the database, **When** account creation is attempted, **Then** appropriate guidance is provided for manual registration.

---

### Edge Cases

- What happens when a parent is already registered but with a different phone number?
- How does system handle international phone number formats (+221, 00221, etc.)?
- What happens when multiple parents share the same phone number?
- How does system handle contacts from numbers not in the parent database?
- What happens if automatic account creation fails midway through the process?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically detect phone numbers from incoming Telegram and WhatsApp messages
- **FR-002**: System MUST validate detected phone numbers against the existing catechism parent database
- **FR-003**: System MUST automatically create user accounts for recognized parents without manual intervention
- **FR-004**: System MUST support multiple role assignments per user (parent role + system roles)
- **FR-005**: System MUST define and maintain super admin privileges for system administration
- **FR-006**: System MUST send appropriate welcome messages to newly created accounts
- **FR-007**: System MUST handle phone number format variations (international codes, spaces, dashes)
- **FR-008**: System MUST provide guidance for unrecognized phone numbers to complete manual registration
- **FR-009**: System MUST prevent duplicate account creation for existing users
- **FR-010**: System MUST log all automatic account creation events for audit purposes
- **FR-011**: System MUST allow super admin to manage user roles and permissions
- **FR-012**: System MUST validate that parent accounts correspond to actual catechism database entries
- **FR-013**: System MUST verify webhook authenticity through signature validation for security
- **FR-014**: System MUST process account creation requests with proper validation and error handling
- **FR-015**: System MUST generate and validate platform-specific authentication tokens for secure sessions

### Non-Functional Requirements

- **NFR-001**: System MUST complete account creation process within 2 seconds of phone number validation
- **NFR-002**: System MUST support 100+ concurrent user account creation requests without performance degradation
- **NFR-003**: System MUST maintain 99.9% uptime availability during business hours
- **NFR-004**: System MUST retain audit logs for 6 months with secure storage and controlled access
- **NFR-005**: System MUST mask phone numbers in logs and user interfaces for privacy compliance
- **NFR-006**: System MUST handle webhook processing timeouts with proper retry mechanisms
- **NFR-007**: System MUST validate all input data with proper sanitization to prevent injection attacks

### Key Entities

- **User Account**: Represents system access credentials linked to parent database entry, contains phone number, roles, and system permissions
- **Parent Record**: Database entry from catechism system containing parent information and phone numbers
- **Role Assignment**: Links users to specific system functions and privileges (parent, super admin, system roles)
- **Contact Session**: Represents individual interaction via Telegram or WhatsApp with automatic account association
- **Account Creation Request**: Contains phone number, platform details, user consent, and metadata for processing account creation
- **Platform Authentication Token**: Security token generated for specific platform sessions (Telegram/WhatsApp) with expiration and validation properties
- **Webhook Event**: Incoming message or interaction from platform requiring authentication and processing

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of recognized parents can access the system within 30 seconds of first contact
- **SC-002**: 100% of automatic account creations complete without manual intervention
- **SC-003**: 90% reduction in manual registration support requests
- **SC-004**: System maintains 99.9% accuracy in phone number recognition and database matching
- **SC-005**: All super admin operations complete successfully within 5 seconds
- **SC-006**: Zero duplicate accounts created for existing users
- **SC-007**: 100% of new users receive appropriate welcome messages and guidance
- **SC-008**: System supports 10+ different international phone number formats without failures