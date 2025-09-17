# Feature Specification: WhatsApp AI Concierge Service

**Feature Branch**: `001-projet-concierge-ia`
**Created**: 2025-09-16
**Status**: Draft
**Input**: User description: "Projet : Concierge IA WhatsApp (via WAHA)

Objectif (WHAT/WHY) :
- Offrir un concierge IA mult-services sur WhatsApp qui accueille, identifie l'exp�diteur, route vers le bon service, orchestre les �changes et produit un artefact final (r�ponse, lien, document, ticket).
- R�duire la charge humaine en automatisant les demandes fr�quentes tout en gardant un handoff humain fluide quand n�cessaire.

Acteurs & r�les :
- Utilisateur WhatsApp (client, partenaire, invit�)
- Admin de service ; Super Admin (supervision multi-services)
- Assistant IA orchestrateur (post-routage)
- WAHA (passerelle WhatsApp) ; Backend FastAPI ; Supabase (donn�es) ; LLM (Claude SDK) ; embeddings (GLM, �volution pgvector)

Capacit�s m�tier (haut niveau) :
- Identification exp�diteur d�s r�ception
- Base num�ros + r�les par service (client/admin/autres)
- Routage direct selon profil & service
- Reprise de session si existante ; arr�t explicitement possible
- Si non identifi� apr�s accueil/mots-cl�s � branchement direct � l'assistant IA
- Contexte par service : prompts syst�me + prompts sp�cifiques
- Orchestration IA : collecte d'infos (1 ou N �tapes), validation, production du r�sultat attendu
- Chaque service d�crit par : d�clencheur, type de d�clencheur, traitement (humain/IA), artefact de sortie
- Identifiants intrins�ques suppl�mentaires (ex. "code_parent" pour Cat�ch�se)
- Service "Renseignement" avec infos (start_date, expiry_date); sans expiry � toujours servir ; expir� � archiver
- Admin Ops par service : alimenter contenus/r�gles/sources, d�l�gations Super Admin

Contraintes & port�e initiale :
- Locale : Africa/Dakar (horaires, handoff humain)
- S�curit� : cl�s en variables d'environnement, HTTPS via reverse proxy
- V1 : MVP robuste des flux WhatsApp � WAHA � Webhook � Orchestration IA � Supabase
- V2+ : recherche s�mantique (pgvector), analytics d'usage, governance plus fine"

## Execution Flow (main)
```
1. Parse user description from Input
   � User description successfully parsed
2. Extract key concepts from description
   � Identified: WhatsApp AI concierge, multi-service routing, user identification, session management, human handoff
3. For each unclear aspect:
   � [NEEDS CLARIFICATION: Specific service types beyond "Cat�ch�se"?]
   � [NEEDS CLARIFICATION: What constitutes "demandes fr�quentes" for automation?]
   � [NEEDS CLARIFICATION: Handoff criteria and process for human intervention?]
   � [NEEDS CLARIFICATION: Success metrics for "r�duire la charge humaine"?]
4. Fill User Scenarios & Testing section
   � User scenarios defined based on WhatsApp interaction flow
5. Generate Functional Requirements
   � Requirements created focusing on user experience and business outcomes
6. Identify Key Entities (if data involved)
   � User, Service, Session, Conversation entities identified
7. Run Review Checklist
   � Multiple [NEEDS CLARIFICATION] markers present - spec has uncertainties
8. Return: SUCCESS (spec ready for planning with clarifications needed)
```

---

## � Quick Guidelines
-  Focus on WHAT users need and WHY
- L Avoid HOW to implement (no tech stack, APIs, code structure)
- =e Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
A WhatsApp user sends a message to the concierge service, receives personalized greeting, gets identified and routed to the appropriate service, interacts with an AI assistant that collects necessary information, and receives a final artifact (answer, link, document, or ticket) - with seamless human handoff when needed.

### Acceptance Scenarios
1. **Given** a new WhatsApp user sends a message, **When** the message is received, **Then** the system MUST send a personalized welcome message and attempt to identify the user
2. **Given** an identified user with service access, **When** they request a service, **Then** the system MUST route them to the appropriate service context with relevant session history
3. **Given** an unidentified user after welcome interaction, **When** they provide service keywords, **Then** the system MUST connect them directly to the AI assistant for orchestration
4. **Given** a user in active session, **When** they request to stop, **Then** the system MUST terminate the session and confirm closure
5. **Given** an AI assistant handling complex requests, **When** human intervention is needed, **Then** the system MUST enable smooth handoff to human agent with full context

### Edge Cases
- What happens when user sends message outside business hours (Africa/Dakar timezone)?
- How does system handle users not in the phone number database?
- What happens when AI assistant cannot understand user request?
- How does system handle expired service information?
- What happens when multiple services match user keywords?

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST identify WhatsApp users immediately upon message receipt using phone number lookup
- **FR-002**: System MUST maintain a database of user phone numbers with associated roles (client/admin/other) per service
- **FR-003**: System MUST route users directly to appropriate service context based on their profile and requested service
- **FR-004**: System MUST resume existing sessions when available, providing conversation history context
- **FR-005**: System MUST allow users to explicitly stop/end current sessions
- **FR-006**: System MUST connect unidentified users directly to AI assistant after welcome and keyword interaction
- **FR-007**: System MUST provide service-specific context including system prompts and specialized prompts
- **FR-008**: System MUST orchestrate AI conversations to collect information in 1 or multiple steps
- **FR-009**: System MUST validate collected information before producing final artifacts
- **FR-010**: System MUST generate and deliver final artifacts (responses, links, documents, tickets)
- **FR-011**: System MUST define each service by: trigger, trigger type, processing method (human/AI), output artifact
- **FR-012**: System MUST support additional intrinsic identifiers per service (e.g., "code_parent" for Cat�ch�se)
- **FR-013**: System MUST provide "Renseignement" service with time-bound information (start_date, expiry_date)
- **FR-014**: System MUST always serve information without expiry dates and archive expired information
- **FR-015**: System MUST enable service administrators to manage content, rules, and sources
- **FR-016**: System MUST support Super Admin delegation and multi-service supervision

### Non-Functional Requirements
- **NFR-001**: System MUST operate in Africa/Dakar timezone for business hours and human handoff scheduling
- **NFR-002**: System MUST secure all API keys and credentials using environment variables
- **NFR-003**: System MUST support HTTPS communication via reverse proxy
- **NFR-004**: System MUST provide robust message handling for WhatsApp � WAHA � Webhook � Orchestration IA � Supabase flow
- **NFR-005**: System MUST maintain user session state across multiple interactions
- **NFR-006**: System MUST log all interactions for audit and improvement purposes

### Key Entities *(include if feature involves data)*
- **User**: WhatsApp user with phone number, role assignments, service access permissions, and session history
- **Service**: Available service type with triggers, processing methods, output artifacts, and admin configuration
- **Session**: Conversation context including history, current state, collected information, and routing decisions
- **Service Content**: Time-bound information for "Renseignement" service with start/end dates and archival status
- **Admin User**: Service administrators and Super Admins with delegated management permissions
- **Conversation Artifact**: Final outputs generated by the system (responses, links, documents, tickets)

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [ ] Review checklist passed

---

## Clarifications Needed

The following aspects require clarification before implementation:

1. **Service Types**: What specific services beyond "Cat�ch�se" should be supported in the initial MVP?
Service Types (MVP)
RENSEIGNEMENT (base d’infos time-bound)
CATECHESE (avec identifiant intrinsèque code_parent)
CONTACT_HUMAIN (handoff direct vers James/admin)
Ces trois suffisent pour le MVP. D’autres pourront être ajoutés ensuite.
Frequent Requests à automatiser
2. **Frequent Requests**: What types of "demandes fr�quentes" should be prioritized for automation?
Frequent Requests à automatiser
Infos pratiques (horaires, programmes, événements, lieux).
FAQ catéchèse (inscriptions, codes parents, horaires de cours).
Renseignements généraux (contacts, services disponibles, tarifs).
On automatise d’abord les questions récurrentes, à faible valeur ajoutée humaine.
3. **Handoff Process**: What are the specific criteria and process for human handoff? When should it be triggered?
Handoff Process (vers humain)
Déclenché si :
a) L’utilisateur tape explicitement “parler à James / agent / humain”.
b) L’IA ne comprend pas après 2 relances.
c) Demande hors des services disponibles (catch-all).
Process : message d’attente → transfert vers humain avec contexte (dernier échange, service en cours).
4. **Success Metrics**: How will "r�duire la charge humaine" be measured? What are the target metrics?
Success Metrics (réduction charge humaine)
% de demandes résolues automatiquement par IA.
Objectif MVP : 60% des interactions simples traitées sans handoff.
Temps moyen avant réponse initiale < 5s.
5. **Service Triggers**: What specific triggers and trigger types should be supported for each service?
Service Triggers (MVP)
Mot-clé (ex : “infos”, “catéchèse”, “aide”).
Numéro connu avec rôle préaffecté → routage direct.
Identifiant intrinsèque demandé (ex : code_parent) si nécessaire.
6. **AI Orchestration**: What are the specific steps and validation rules for information collection?
Service Triggers (MVP)
Mot-clé (ex : “infos”, “catéchèse”, “aide”).
Numéro connu avec rôle préaffecté → routage direct.
Identifiant intrinsèque demandé (ex : code_parent) si nécessaire.
7. **User Identification**: What methods beyond phone number lookup should be used for user identification?
AI Orchestration (collecte d’infos)
Étape 1 : charger contexte système + prompts du service.
Étape 2 : poser questions obligatoires (définies par service, ex : code_parent, sujet).
Étape 3 : validation (tous les champs requis fournis).
Étape 4 : produire artefact (réponse texte, lien, doc).