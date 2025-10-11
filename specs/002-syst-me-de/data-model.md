# Data Model: Enrollment Management System

**Feature**: Système de Gestion de Profils et Inscriptions avec SQLite
**Branch**: `002-syst-me-de`
**Date**: 2025-10-11

## Overview

This document defines the data model for the multi-profile enrollment management system. The architecture uses the existing `sdb_cate.sqlite` database with new tables added, plus two additional SQLite databases for application isolation:

- **sdb_cate.sqlite** (EXISTING): Core catechism data with 509 students, 341 parents, 819 enrollments, 15 classes - NEW tables will be added for enhanced enrollment features
- **temp_pages_system.db** (NEW): Temporary secure pages for document collection
- **core_system.db** (NEW): System configuration and application metadata

### Existing Database Structure

The `sdb_cate.sqlite` database (located at `/home/ubuntu/ai-concierge/sdb_cate.sqlite`) contains:
- **catechumenes_2** (509 records): Student information with Code_Parent linkage
- **parents_2** (341 records): Parent contact information with Code_Parent identifier
- **inscriptions_16** (819 records): Historical enrollment records with payment tracking
- **classes** (15 records): Class definitions
- **notes**: Student grades and assessments
- **extraitdebapteme**: Baptism certificate references
- **mouvements_de_caisse**: Cash movement tracking
- **utilisateurs** (3 records): System users
- **annee_inscription**, **periodes**, **types_notes**: Reference tables
- **recus_numeros**: Receipt number tracking

### Migration Strategy

**Approach**: Extend existing database with new normalized tables while preserving legacy data for historical reference.

**New Tables to Add** (to sdb_cate.sqlite):
- `documents`: Document metadata and OCR results (FR-002-006, FR-010)
- `paiements`: Enhanced payment tracking with Mobile Money support (FR-011-020)
- `profil_utilisateurs`: Role-based user profiles (FR-021-032)
- `action_logs`: Audit trail for GDPR compliance (FR-051-055)

**Legacy Tables**:
- Keep existing tables as read-only for historical queries
- New enrollment flows use new tables
- Data synchronization layer maps between old/new schemas

---

## Database: sdb_cate.sqlite (EXISTING + NEW TABLES)

### Existing Legacy Tables (Read-Only Reference)

#### Table: catechumenes_2 (EXISTING - 509 records)

**Purpose**: Historical student records

| Column | Type | Description |
|--------|------|-------------|
| ID_Catechumene | TEXT | UUID identifier |
| Nom | TEXT | Last name |
| Prenoms | TEXT | First name(s) |
| Ann_e_de_naissance | TEXT | Birth year |
| Code_Parent | TEXT | Parent identifier (links to parents_2) |
| Baptisee | TEXT | Baptized status: "oui"/"non" |
| LieuBapteme | TEXT | Baptism location |
| Extrait_de_Naissance_Fourni | TEXT | Birth certificate provided |
| Extrait_De_Bapteme_Fourni | TEXT | Baptism certificate provided: "oui"/"non" |
| Attestation_De_Transfert_Fournie | TEXT | Transfer attestation provided: "oui"/"non" |
| Extrait_Naissance | TEXT | Birth certificate file reference |
| Extrait_Bapteme | TEXT | Baptism certificate file reference |
| Attestation_Transfert | TEXT | Transfer attestation file reference |
| Commentaire | TEXT | Comments/notes |
| operateur | TEXT | Data entry operator |
| id | TEXT | Sequential ID |

#### Table: parents_2 (EXISTING - 341 records)

**Purpose**: Parent contact information

| Column | Type | Description |
|--------|------|-------------|
| Code_Parent | TEXT | Unique parent code (e.g., "1de90", "57704") |
| Nom | TEXT | Last name |
| Prenoms | TEXT | First name(s) |
| T_l_phone | TEXT | Primary phone number |
| T_l_phone_2 | TEXT | Secondary phone number |
| Email | TEXT | Email address |
| Actif | TEXT | Active status: "True"/"False" |
| id | TEXT | Sequential ID |

#### Table: inscriptions_16 (EXISTING - 819 records)

**Purpose**: Historical enrollment records

| Column | Type | Description |
|--------|------|-------------|
| ID_Inscription | TEXT | Unique inscription identifier |
| ID_Catechumene | TEXT | FK to catechumenes_2 |
| Annee_Inscription | TEXT | Enrollment year |
| ID_AnneeInscription | TEXT | Reference to annee_inscription |
| ClasseCourante | TEXT | Current class name |
| ID_ClasseCourante | TEXT | FK to classes |
| Groupe | TEXT | Group identifier |
| Paye | TEXT | Payment status |
| Montant | TEXT | Amount paid |
| Moyen_Paiement | TEXT | Payment method |
| Choix_Paiement | TEXT | Payment choice |
| Infos_Paiement | TEXT | Payment information |
| Etat | TEXT | Enrollment state |
| DateInscription | TEXT | Inscription date |
| Commentaire | TEXT | Comments |
| ParoisseAnneePrecedente | TEXT | Previous parish |
| AnneePrecedente | TEXT | Previous year |
| Annee_Suivante | TEXT | Next year |
| Livre_Remis | TEXT | Book delivered status |
| Note_Finale | TEXT | Final grade |
| Resultat_Final | TEXT | Final result |
| Absennces | TEXT | Absences count |
| Mouvements_de_caisse | TEXT | Cash movements |
| AttestationDeTransfert | TEXT | Transfer attestation |
| ReconCheck | TEXT | Reconciliation check |
| ReconOP | TEXT | Reconciliation operation |
| action | TEXT | Action performed |
| sms | TEXT | SMS notifications |
| operateur | TEXT | Operator |
| Nom | TEXT | Student name |
| Prenoms | TEXT | Student first names |
| id | TEXT | Sequential ID |

#### Table: classes (EXISTING - 15 records)

**Purpose**: Class definitions

| Column | Type | Description |
|--------|------|-------------|
| Nom | TEXT | Class name |
| court | TEXT | Short name |
| Ordre | TEXT | Display order |
| Actif | TEXT | Active status |
| Inscriptions___ID_AnneeSuivante | TEXT | Next year inscription link |
| id | TEXT | Sequential ID |

#### Table: mouvements_de_caisse (EXISTING)

**Purpose**: Cash movement tracking

| Column | Type | Description |
|--------|------|-------------|
| Type | TEXT | Movement type: "Entrée"/"Sortie" |
| Cat_gorie | TEXT | Category |
| Montant | TEXT | Amount |
| Date | TEXT | Transaction date |
| Description | TEXT | Description |
| Inscription | TEXT | Related inscription |
| Pi_ce_justificative | TEXT | Receipt document |
| Type_de_justificatif | TEXT | Receipt type |
| Nom | TEXT | Payee/Payer name |
| id | TEXT | Sequential ID |

#### Table: utilisateurs (EXISTING - 3 records)

**Purpose**: System users (legacy)

| Column | Type | Description |
|--------|------|-------------|
| Pr_noms_et_Nom | TEXT | Full name |
| Code_Parent | TEXT | Parent code (if applicable) |
| Mot_de_Passe | TEXT | Password |
| Courriel | TEXT | Email |
| Actif | TEXT | Active status |
| Liste_d_roulante | TEXT | Dropdown list |
| SMS_Messages | TEXT | SMS messages |
| SMS_Campaigns | TEXT | SMS campaigns |
| SMS_Templates | TEXT | SMS templates |
| SystemActivityLog | TEXT | Activity log |
| SystemActivityLog___CancelledBy | TEXT | Log cancellation |
| id | TEXT | Sequential ID |

---

### NEW TABLES (To be added to sdb_cate.sqlite)

### Entity: Inscription (NEW - Enhanced Enrollment)

Represents new enrollment applications with OCR document processing and structured payment tracking.

**Table**: `inscriptions`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT PRIMARY KEY | UUID | Unique inscription identifier |
| numero_unique | TEXT UNIQUE NOT NULL | "CAT-YYYY-XXXX" | Human-readable inscription number (FR-007) |
| parent_id | TEXT NOT NULL | FK → profil_utilisateurs.user_id | Enrolling parent |
| legacy_code_parent | TEXT | FK → parents_2.Code_Parent | Link to legacy parent data (migration) |
| legacy_catechumene_id | TEXT | FK → catechumenes_2.ID_Catechumene | Link to legacy student (re-enrollment) |
| nom_enfant | TEXT NOT NULL | | Student last name |
| prenom_enfant | TEXT NOT NULL | | Student first name |
| date_naissance | DATE NOT NULL | | Birth date |
| lieu_naissance | TEXT NOT NULL | | Birth place |
| date_bapteme | DATE | | Baptism date (null if not baptized) |
| paroisse_bapteme | TEXT | | Baptism parish |
| nom_pretre_bapteme | TEXT | | Baptizing priest name |
| paroisse_origine | TEXT | | Origin parish (for transfers, FR-005) |
| annee_catechisme_precedente | TEXT | | Previous catechism year (for transfers) |
| annee_catechetique | TEXT NOT NULL | "2025-2026" | Enrollment year |
| niveau | TEXT | | Level: éveil, CE1, CE2, CM1, CM2, confirmation |
| classe_id | TEXT | FK → classes.id | Assigned class (null until placement) |
| statut | TEXT NOT NULL | ENUM | Status: brouillon, en_attente_paiement, paiement_partiel, active, annulee (FR-240) |
| montant_total | REAL NOT NULL | > 0 | Total enrollment fee |
| montant_paye | REAL DEFAULT 0 | >= 0 | Amount paid so far |
| solde_restant | REAL GENERATED | montant_total - montant_paye | Remaining balance (FR-018) |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Creation timestamp |
| updated_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Last modification timestamp |
| created_by | TEXT NOT NULL | FK → profil_utilisateurs.user_id | Creator (parent or staff) |
| validated_by | TEXT | FK → profil_utilisateurs.user_id | Validator (staff member, null until validated) |
| validated_at | TIMESTAMP | | Validation timestamp |

**Indexes**:
- `idx_inscriptions_parent` ON (parent_id)
- `idx_inscriptions_numero` ON (numero_unique)
- `idx_inscriptions_statut` ON (statut)
- `idx_inscriptions_annee` ON (annee_catechetique)
- `idx_inscriptions_legacy_parent` ON (legacy_code_parent)
- `idx_inscriptions_legacy_catechumene` ON (legacy_catechumene_id)

**Migration Notes**:
- `legacy_code_parent`: Links new inscriptions to existing parent records in `parents_2`
- `legacy_catechumene_id`: Links re-enrollments to historical student data in `catechumenes_2`
- For new parents not in `parents_2`: Create entry in `profil_utilisateurs` with generated `code_parent_hash`

**State Transitions**:
```
brouillon → en_attente_paiement → active
           ↓                     ↓
           └─────→ annulee ←─────┘
                    ↓
              paiement_partiel → active
```

---

### Entity: Document

Represents uploaded documents (birth certificates, baptism certificates, payment proofs).

**Table**: `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT PRIMARY KEY | UUID | Document identifier |
| inscription_id | TEXT NOT NULL | FK → inscriptions.id | Associated inscription |
| type_document | TEXT NOT NULL | ENUM | Type: extrait_naissance, extrait_bapteme, attestation_transfert, preuve_paiement (FR-010) |
| fichier_path | TEXT NOT NULL | | MinIO file path: {year}/{inscription_id}/{type}.{ext} |
| format | TEXT NOT NULL | | File format: pdf, jpg, png, heic (FR-002) |
| taille_bytes | INTEGER NOT NULL | <= 10485760 | File size (max 10MB per FR-002) |
| uploaded_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Upload timestamp |
| statut_ocr | TEXT NOT NULL | ENUM | OCR status: en_attente, en_cours, succes, echec, manuel (FR-010) |
| donnees_extraites | TEXT | JSON | OCR extracted data (raw) |
| donnees_validees | TEXT | JSON | User-validated data (FR-006) |
| confiance_ocr | REAL | 0.0-1.0 | OCR confidence score |
| valide_par_parent | BOOLEAN DEFAULT FALSE | | Parent confirmed data (FR-006) |
| validated_at | TIMESTAMP | | Parent validation timestamp |
| error_message | TEXT | | OCR error message if statut_ocr = echec |

**Indexes**:
- `idx_documents_inscription` ON (inscription_id)
- `idx_documents_type` ON (type_document)
- `idx_documents_statut_ocr` ON (statut_ocr)

**Validation Rules**:
- At least one `extrait_naissance` required per inscription (FR-003)
- At least one `extrait_bapteme` or attestation_transfert required (FR-004, FR-005)
- `preuve_paiement` required when submitting payment (FR-012)

---

### Entity: Paiement

Represents payment transactions for enrollments.

**Table**: `paiements`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT PRIMARY KEY | UUID | Payment identifier |
| inscription_id | TEXT NOT NULL | FK → inscriptions.id | Associated inscription |
| montant | REAL NOT NULL | > 0 | Payment amount |
| mode_paiement | TEXT NOT NULL | ENUM | Mode: cash, orange_money, wave, free_money, recu_papier (FR-011, FR-056) |
| reference | TEXT | | Transaction ID or receipt number (FR-016) |
| preuve_document_id | TEXT | FK → documents.id | Payment proof document (screenshot or receipt) |
| statut | TEXT NOT NULL | ENUM | Status: en_attente_validation, valide, rejete (FR-015) |
| soumis_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Submission timestamp |
| valide_at | TIMESTAMP | | Validation/rejection timestamp |
| validateur_id | TEXT | FK → profil_utilisateurs.user_id | Treasurer who validated (FR-015) |
| motif_rejet | TEXT | | Rejection reason if statut = rejete (FR-015) |
| metadata | TEXT | JSON | Additional data: operator, point_vente, etc. (FR-016) |

**Indexes**:
- `idx_paiements_inscription` ON (inscription_id)
- `idx_paiements_statut` ON (statut)
- `idx_paiements_validateur` ON (validateur_id)
- `idx_paiements_date` ON (soumis_at)

**Validation Rules**:
- Total payments per inscription cannot exceed `inscriptions.montant_total`
- At least one `valide` payment required for inscription.statut = active

---

### Entity: ProfilUtilisateur

Represents system users with role-based permissions.

**Table**: `profil_utilisateurs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | TEXT PRIMARY KEY | UUID | User identifier |
| nom | TEXT NOT NULL | | Last name |
| prenom | TEXT NOT NULL | | First name |
| role | TEXT NOT NULL | ENUM | Role: super_admin, sacristain, cure, secretaire_cure, president_bureau, secretaire_bureau, secretaire_adjoint_bureau, tresorier_bureau, tresorier_adjoint_bureau, responsable_organisation_bureau, charge_relations_exterieures_bureau, charge_relations_exterieures_adjoint_bureau, catechiste, parent (FR-021, FR-022) |
| telephone | TEXT UNIQUE NOT NULL | E.164 format | Phone number |
| email | TEXT | | Email address (optional) |
| canal_prefere | TEXT NOT NULL | ENUM | Preferred channel: whatsapp, telegram (FR-032) |
| identifiant_canal | TEXT NOT NULL | | WhatsApp/Telegram user ID |
| code_parent_hash | TEXT | bcrypt hash | Hashed parent code (null for non-parent roles, FR-032) |
| actif | BOOLEAN DEFAULT TRUE | | Account active status |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Account creation |
| derniere_connexion | TIMESTAMP | | Last login timestamp |
| permissions | TEXT NOT NULL | JSON | Role-specific permissions (FR-023-029) |
| metadata | TEXT | JSON | Additional profile data |

**Indexes**:
- `idx_profil_telephone` ON (telephone)
- `idx_profil_role` ON (role)
- `idx_profil_canal` ON (identifiant_canal)

**Permission Schema** (JSON):
```json
{
  "inscriptions": {
    "create": true,
    "read": "own",  // "all", "own", "none"
    "update": "own",
    "delete": false
  },
  "paiements": {
    "submit": true,
    "validate": false,
    "view_all": false
  },
  "profils": {
    "manage": false,
    "view": "none"
  },
  "classes": {
    "view_assigned": true,
    "view_all": false,
    "manage": false
  },
  "rapports": {
    "generate": false,
    "view": false
  }
}
```

**Role Permission Matrix** (FR-023-029):
- **super_admin**: All permissions true
- **parent**: inscriptions (own only), paiements (submit only), notes (read own children)
- **tresorier_bureau**: paiements (validate), rapports (generate/view)
- **catechiste**: classes (view assigned), students (search), presences (mark)
- See spec FR-023-029 for complete role definitions

---

### Entity: Classe

Represents catechism class groupings.

**Table**: `classes`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| classe_id | TEXT PRIMARY KEY | UUID | Class identifier |
| annee_catechetique | TEXT NOT NULL | "2025-2026" | School year |
| niveau | TEXT NOT NULL | ENUM | Level: éveil, CE1, CE2, CM1, CM2, confirmation |
| catechiste_id | TEXT NOT NULL | FK → profil_utilisateurs.user_id WHERE role='catechiste' | Primary catechist |
| catechiste_adjoint_id | TEXT | FK → profil_utilisateurs.user_id WHERE role='catechiste' | Assistant catechist |
| capacite_max | INTEGER NOT NULL | > 0 | Maximum capacity |
| effectif_actuel | INTEGER DEFAULT 0 | >= 0 | Current enrollment count (computed) |
| horaire | TEXT | | Schedule: "Samedi 14h-16h" |
| salle | TEXT | | Room assignment |
| statut | TEXT DEFAULT 'ouverte' | ENUM | Status: ouverte, fermee, suspendue |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Creation timestamp |

**Indexes**:
- `idx_classes_annee_niveau` ON (annee_catechetique, niveau)
- `idx_classes_catechiste` ON (catechiste_id)

**Validation Rules**:
- `effectif_actuel` ≤ `capacite_max` (enforced by trigger)
- Only one catechiste with `role='catechiste'` can be assigned

---

### Entity: ActionLog

Audit trail for all system actions (GDPR compliance FR-051-055).

**Table**: `action_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| log_id | TEXT PRIMARY KEY | UUID | Log entry identifier |
| user_id | TEXT NOT NULL | FK → profil_utilisateurs.user_id | Actor performing action |
| action_type | TEXT NOT NULL | ENUM | Action: create_inscription, modify_inscription, upload_document, validate_ocr, submit_paiement, validate_paiement, reject_paiement, modify_profil, access_data (FR-052) |
| entity_type | TEXT NOT NULL | ENUM | Entity: inscription, paiement, document, profil |
| entity_id | TEXT NOT NULL | | ID of affected entity |
| timestamp | TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL | | Action timestamp |
| ip_address | TEXT | | User IP address (anonymized after 2 years, FR-055) |
| user_agent | TEXT | | Channel: whatsapp, telegram |
| details | TEXT | JSON | Action context (anonymized after 2 years) |
| statut_action | TEXT NOT NULL | ENUM | Status: succes, echec |
| error_message | TEXT | | Error details if statut_action = echec |

**Indexes**:
- `idx_action_logs_user` ON (user_id)
- `idx_action_logs_timestamp` ON (timestamp)
- `idx_action_logs_entity` ON (entity_type, entity_id)

**Retention Policy** (FR-054, FR-055):
- Logs kept for 2 years minimum
- After 2 years: Anonymize `ip_address`, `user_agent`, `details` (replace with hash)
- Aggregated statistics preserved indefinitely

---

## Database: temp_pages_system.db

### Entity: PageTemporaire

Temporary secure URLs for document collection.

**Table**: `pages_temporaires`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| page_id | TEXT PRIMARY KEY | UUID | Page identifier |
| code_acces | TEXT UNIQUE NOT NULL | 8-char alphanumeric | Access code (FR-041) |
| url_complete | TEXT UNIQUE NOT NULL | | Full URL with code |
| utilisateur_associe_id | TEXT NOT NULL | Parent user_id | Target parent |
| createur_id | TEXT NOT NULL | Staff user_id | Page creator |
| objet | TEXT NOT NULL | ENUM | Purpose: inscription, documents_complementaires, autre (FR-042) |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL | | Creation timestamp |
| expires_at | TIMESTAMP NOT NULL | | Expiration (default: created_at + 7 days, FR-043) |
| premiere_utilisation_at | TIMESTAMP | | First access timestamp |
| statut | TEXT DEFAULT 'active' | ENUM | Status: active, utilisee, expiree, revoquee (FR-042) |
| documents_collectes | TEXT | JSON array | Collected document IDs (FR-042) |

**Indexes**:
- `idx_pages_code` ON (code_acces)
- `idx_pages_utilisateur` ON (utilisateur_associe_id)
- `idx_pages_statut` ON (statut, expires_at)

**Validation Rules**:
- Auto-expire pages where `expires_at < CURRENT_TIMESTAMP` (background job)
- Code format: [A-Z0-9]{8} excluding ambiguous chars (0, O, 1, I, L)

---

## Database: core_system.db

### Entity: ApplicationMetadata

System configuration and application registry.

**Table**: `applications`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| app_id | TEXT PRIMARY KEY | UUID | Application identifier |
| app_name | TEXT UNIQUE NOT NULL | | Application name: catechese_app, temp_pages_system, etc. |
| db_filename | TEXT UNIQUE NOT NULL | | Database filename: catechese_app.db |
| db_path | TEXT UNIQUE NOT NULL | | Full path to database file |
| version_schema | TEXT NOT NULL | Semantic versioning | Current schema version: "1.0.0" |
| created_at | TIMESTAMP DEFAULT CURRENT_TIMESTAMP | | Initial creation |
| derniere_migration_at | TIMESTAMP | | Last schema migration |
| taille_bytes | INTEGER | | Database file size (updated daily) |
| derniere_sauvegarde_at | TIMESTAMP | | Last backup timestamp (FR-038) |
| statut | TEXT DEFAULT 'active' | ENUM | Status: active, maintenance, archived (FR-039) |
| config | TEXT | JSON | Application-specific configuration |

**Indexes**:
- `idx_applications_name` ON (app_name)

**Purpose**: Enables multi-application management (FR-033-040), tracks backup status, facilitates selective restoration

---

## Relationships

### Cross-Database References

**Important**: SQLite does not support foreign keys across database files. References across databases are enforced at the application layer.

**Catechese ↔ Temp Pages**:
- `temp_pages_system.pages_temporaires.utilisateur_associe_id` references `sdb_cate.profil_utilisateurs.user_id`
- `temp_pages_system.pages_temporaires.documents_collectes` references `sdb_cate.documents.id`
- Enforced by: Application-level validation in `TempPageService`

**All Apps ↔ Core**:
- All applications registered in `core_system.applications`
- Enforced by: System initialization scripts

### Intra-Database References (sdb_cate.sqlite)

```
profil_utilisateurs (user_id)
    ↓ (parent_id)
inscriptions
    ↓ (inscription_id)
documents, paiements
    ↓
action_logs (entity_id)

classes (classe_id)
    ↓
inscriptions (classe_id)
    ↑
profil_utilisateurs (catechiste_id)
```

---

## Data Validation Rules

### Business Rules

1. **Enrollment Completion** (FR-007):
   - Inscription requires: nom_enfant, prenom_enfant, date_naissance, lieu_naissance
   - At least 1 document with type='extrait_naissance' and statut_ocr='succes'
   - At least 1 document with type='extrait_bapteme' OR type='attestation_transfert'

2. **Payment Validation** (FR-015):
   - Sum of `paiements.montant` WHERE `statut='valide'` must equal `inscriptions.montant_total` for inscription to become 'active'
   - Partial payments allowed (FR-018): `statut='paiement_partiel'` when 0 < sum < montant_total

3. **Profile Permissions** (FR-030):
   - Unauthorized access attempts logged in action_logs with statut_action='echec'
   - Permission checks before every sensitive operation

4. **Document Lifecycle** (FR-010):
   - Document `statut_ocr` progression: en_attente → en_cours → (succes | echec)
   - If echec and retry_count < 3: allow OCR retry
   - If echec and retry_count >= 3: force `statut_ocr='manuel'`

### Database Constraints

**Check Constraints**:
```sql
-- inscriptions
CHECK (montant_total > 0)
CHECK (montant_paye >= 0)
CHECK (statut IN ('brouillon', 'en_attente_paiement', 'paiement_partiel', 'active', 'annulee'))

-- documents
CHECK (taille_bytes <= 10485760)  -- 10MB max (FR-002)
CHECK (confiance_ocr BETWEEN 0.0 AND 1.0)

-- paiements
CHECK (montant > 0)
CHECK (mode_paiement IN ('cash', 'orange_money', 'wave', 'free_money', 'recu_papier'))

-- classes
CHECK (capacite_max > 0)
CHECK (effectif_actuel >= 0)
CHECK (effectif_actuel <= capacite_max)
```

**Triggers**:
```sql
-- Update inscription.updated_at on modification
CREATE TRIGGER inscriptions_updated_at
AFTER UPDATE ON inscriptions
BEGIN
  UPDATE inscriptions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update classe.effectif_actuel when inscription added/removed
CREATE TRIGGER update_classe_effectif
AFTER UPDATE OF classe_id, statut ON inscriptions
WHEN NEW.statut = 'active' AND NEW.classe_id IS NOT NULL
BEGIN
  UPDATE classes SET effectif_actuel = (
    SELECT COUNT(*) FROM inscriptions
    WHERE classe_id = NEW.classe_id AND statut = 'active'
  ) WHERE classe_id = NEW.classe_id;
END;

-- Auto-generate inscription.numero_unique
CREATE TRIGGER generate_numero_unique
AFTER INSERT ON inscriptions
WHEN NEW.numero_unique IS NULL
BEGIN
  UPDATE inscriptions SET numero_unique = (
    'CAT-' || strftime('%Y', 'now') || '-' ||
    printf('%04d', (SELECT COUNT(*) FROM inscriptions WHERE annee_catechetique = NEW.annee_catechetique))
  ) WHERE id = NEW.id;
END;
```

---

## Schema Migration Strategy

**Versioning**: Each database maintains schema version in `core_system.applications.version_schema`

**Migration Process**:
1. Create migration script: `migrations/catechese_app_v1.0.0_to_v1.1.0.sql`
2. Test migration on copy of production database
3. Apply migration with transaction rollback on error
4. Update `applications.version_schema` and `derniere_migration_at`
5. Create post-migration backup (FR-038)

**Backward Compatibility**: All migrations must be backward-compatible for 1 version (allow rollback)

---

## Performance Considerations

### Query Optimization

**Frequently Accessed Paths**:
- Parent viewing their inscriptions: Index on `inscriptions.parent_id`
- Treasurer validation queue: Index on `paiements.statut` + `soumis_at`
- Catechist class roster: Index on `inscriptions.classe_id` + `statut`

**Connection Pooling** (from research.md):
- Pool size: 20 connections per database
- WAL mode for concurrent read/write
- Timeout: 5 seconds for lock acquisition

### Data Archival

**Annual Archival Process**:
1. At end of catechism year (June): Export completed enrollments to archive database
2. Create archive: `sdb_cate_2024_2025_archive.sqlite`
3. Remove archived data from active `sdb_cate.sqlite`
4. Preserve logs for 2 years (GDPR FR-054)

---

## Next Steps

1. Generate SQL migration files for adding new tables to existing sdb_cate.sqlite:
   - `src/database/migrations/add_enrollment_tables_v1.0.0.sql` (inscriptions, documents, paiements, profil_utilisateurs, action_logs)
   - `src/database/temp_pages_schema.sql` (new database)
   - `src/database/core_schema.sql` (new database)

2. Implement Python models with Pydantic for type safety:
   - `src/models/enrollment.py` (Inscription, Document, Paiement)
   - `src/models/profile.py` (ProfilUtilisateur, legacy parent/student adapters)
   - `src/models/temp_page.py` (PageTemporaire)
   - `src/models/legacy.py` (Read-only models for catechumenes_2, parents_2, inscriptions_16)

3. Create database manager service:
   - `src/database/sqlite_manager.py` (connection pooling for 3 databases, WAL mode configuration)
   - `src/database/migration_runner.py` (apply migrations to sdb_cate.sqlite safely)

4. Generate API contracts from this data model (Phase 1 next task)
