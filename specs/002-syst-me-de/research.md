# Technical Research: Enrollment Management System

**Feature**: Système de Gestion de Profils et Inscriptions avec SQLite
**Branch**: `002-syst-me-de`
**Date**: 2025-10-11

## Research Overview

This document consolidates technical decisions for the enrollment management system. Five key areas required research to resolve "NEEDS CLARIFICATION" items from Technical Context and address Constitution Check attention items.

---

## 1. OCR Library Selection for French Document Extraction

### Decision: EasyOCR with fallback to manual entry

### Rationale

**Evaluated Options**:
1. **pytesseract (Tesseract wrapper)**: Open-source, mature, supports French
2. **EasyOCR**: Deep learning-based, better accuracy for varied document quality, 80+ languages including French
3. **Cloud OCR (Google/Azure)**: Highest accuracy but introduces external dependency and cost

**Selection Criteria**:
- French language accuracy for official documents (birth certificates, baptism certificates)
- Offline capability (constitution: no external API dependencies for core features)
- Cost (free/open-source preferred)
- Performance (< 10 seconds per document from Technical Context)

**EasyOCR Advantages**:
- Deep learning models trained on diverse document types
- Better handling of handwritten text on certificates
- Built-in French language support with high accuracy
- No external API calls (self-contained)
- Active development and community support

**Implementation Strategy**:
- Primary: EasyOCR for automatic extraction (FR-003, FR-004, FR-005)
- Fallback: Manual data entry UI when OCR confidence < 70%
- Preprocessing: Image enhancement (contrast, rotation, noise reduction) before OCR
- User validation: Always present extracted data for parent confirmation (FR-006)

**Performance Expectations**:
- OCR processing: 5-8 seconds per page on standard hardware
- Target accuracy: > 85% for clean documents (SC-002)
- For poor quality scans: graceful degradation to manual entry

### Alternatives Considered

- **pytesseract rejected**: Lower accuracy on handwritten fields, requires separate French language pack installation, less robust with varied document quality
- **Cloud OCR rejected**: Violates constitution principle of no external dependencies for core features, introduces ongoing cost and latency

---

## 2. SQLite Concurrency Strategy for Multi-Database Architecture

### Decision: WAL mode with connection pooling and per-database locks

### Rationale

**Challenge**: Three separate SQLite databases (`catechese_app.db`, `temp_pages_system.db`, `core_system.db`) with concurrent read/write access from multiple WhatsApp/Telegram users during enrollment period.

**SQLite Concurrency Patterns**:
1. **Journal Mode (default)**: Locks entire database on write, not suitable for > 10 concurrent users
2. **WAL (Write-Ahead Logging)**: Allows concurrent reads during writes, better performance
3. **Connection Pooling**: Reuse connections to avoid overhead of repeated opens

**Selected Approach**:
```python
# WAL mode configuration per database
PRAGMA journal_mode=WAL
PRAGMA synchronous=NORMAL  # Balance safety vs. speed
PRAGMA busy_timeout=5000   # Wait up to 5s for locks
PRAGMA cache_size=-64000   # 64MB cache per connection
```

**Connection Pooling Strategy**:
- Use `aiosqlite` for async SQLite operations (constitution: async throughout)
- Pool size: 20 connections per database (sufficient for 500-1000 students per period)
- Timeout: 5 seconds for acquiring connection (aligns with < 5s p95 requirement)
- Transaction isolation: DEFERRED for reads, IMMEDIATE for writes

**Database Access Patterns**:
- `catechese_app.db`: High write concurrency during enrollment (inscriptions, documents, payments)
- `temp_pages_system.db`: Medium write concurrency (temporary page creation, document uploads)
- `core_system.db`: Low write concurrency (configuration changes, profile updates)

**Lock Management**:
- Per-database locks (no cross-database transactions, preserving isolation per FR-034)
- Retry logic: 3 attempts with exponential backoff for `SQLITE_BUSY` errors
- Deadlock prevention: Always acquire database locks in fixed order when needed

### Alternatives Considered

- **PostgreSQL for all data rejected**: Spec explicitly requires SQLite multi-database architecture (FR-033), PostgreSQL doesn't provide same file-based isolation
- **Single SQLite database rejected**: Violates FR-034 requirement for application isolation, prevents future modular growth

---

## 3. Document Storage Architecture with MinIO

### Decision: Hierarchical storage with year/student partitioning and lifecycle policies

### Rationale

**Storage Requirements**:
- Document types: Birth certificates, baptism certificates, transfer attestations, payment screenshots (FR-002)
- File formats: PDF, JPG, PNG, HEIC up to 10MB each
- Scale: 500-1000 students × 3-4 documents = 1500-4000 documents per enrollment period
- Retention: Multi-year retention for audit (GDPR FR-054)

**MinIO Folder Structure**:
```
sdb-catechese/
├── 2025/
│   ├── CAT-2025-0001/
│   │   ├── birth_certificate.pdf
│   │   ├── baptism_certificate.jpg
│   │   └── payment_proof.png
│   ├── CAT-2025-0002/
│   │   └── ...
├── 2026/
│   └── ...
└── temp/
    └── uploads/  # Pending OCR processing
```

**Document Lifecycle**:
1. **Upload**: User uploads via WhatsApp/Telegram → temporary staging in `temp/uploads/`
2. **OCR Processing**: EasyOCR extracts data, enriches metadata
3. **Validation**: Parent confirms extracted data (FR-006)
4. **Archive**: Move to permanent path `{year}/{inscription_id}/{document_type}.{ext}`
5. **Retention**: MinIO lifecycle policy for automatic archival after 2 years (FR-054 compliance)

**MinIO Integration**:
- Use `minio` Python client (async-compatible)
- Pre-signed URLs (7-day expiration) for temporary page uploads (FR-041-043)
- Server-side encryption for GDPR compliance (Principle VIII)
- Automatic backup to S3-compatible storage (existing infrastructure)

**Metadata Storage**:
- Document records in SQLite `documents` table with MinIO path reference
- OCR extracted data stored as JSON in SQLite for fast queries
- MinIO metadata: Content-Type, upload timestamp, parent user_id

### Alternatives Considered

- **Local filesystem rejected**: No encryption at rest, harder to scale, no automatic lifecycle management
- **Supabase Storage rejected**: Adds dependency on Supabase for file storage, MinIO already deployed and provides better control

---

## 4. Mobile Money Payment Screenshot OCR

### Decision: Hybrid approach with template matching + OCR + manual validation

### Rationale

**Challenge**: Extract transaction details from Mobile Money screenshots across 3 operators (Orange Money, Wave, Free Money) with varying UI layouts and languages (FR-056, FR-057, FR-058).

**Mobile Money Receipt Variations**:
- **Orange Money**: Orange-branded, French UI, transaction ID format "TX-XXXXXXXX"
- **Wave**: Blue/white UI, Wolof/French, transaction ID format alphanumeric 12 chars
- **Free Money**: Red-branded, French UI, transaction ID format "FM-XXXXXXXX"

**Hybrid OCR Strategy**:
1. **Template Detection**: Identify operator from screen colors/logos
   - Orange Money: Orange color detection (RGB: 255, 102, 0)
   - Wave: Blue header detection (RGB: 0, 123, 255)
   - Free Money: Red color detection (RGB: 220, 20, 60)

2. **Region-Based OCR**: Extract specific regions based on operator template
   - Transaction ID: Top-right corner (Orange), center (Wave), top-left (Free)
   - Amount: Center-right for all operators
   - Date/Time: Bottom section for all operators

3. **Data Validation**: Regex patterns per operator
   ```python
   PATTERNS = {
       "orange": r"TX-\d{8}",
       "wave": r"[A-Z0-9]{12}",
       "free": r"FM-\d{8}"
   }
   ```

4. **Manual Validation**: Treasurer always validates via UI (FR-058, FR-059)
   - Pre-filled form with OCR extracted data
   - Side-by-side: screenshot + extracted fields
   - Treasurer corrects any errors before approval

**Confidence Scoring**:
- High confidence (>85%): Auto-fill treasurer validation form
- Medium confidence (60-85%): Flag for careful review
- Low confidence (<60%): Mark as "requires manual entry"

**Success Criteria**:
- OCR extraction success rate: Target 75% (lower than document OCR due to screenshot variability)
- Validation time: < 2 minutes per transaction (SC-003) with pre-filled data

### Alternatives Considered

- **Full API integration rejected**: Mobile Money operators don't provide public APIs for transaction verification, spec chose hybrid manual approach (FR-058)
- **Manual-only rejected**: Wastes treasurer time, defeats purpose of OCR automation

---

## 5. Security Pattern for Code Parent Validation

### Decision: Rate-limited Supabase lookup with bcrypt hashed codes

### Rationale

**Security Requirement**: FR-032 requires authentication via "code parent (depuis Baserow)" for phone numbers not in database. Constitution Principle V mandates no credential leaks.

**Architecture Change**: Since Baserow is excluded, code parent will be stored in SQLite `catechese_app.db` in `parents` table.

**Security Implementation**:
1. **Storage**: Parent codes hashed with bcrypt (work factor 12) in SQLite
   ```python
   import bcrypt
   hashed = bcrypt.hashpw(code.encode(), bcrypt.gensalt(rounds=12))
   ```

2. **Validation Flow**:
   - User provides code parent via WhatsApp/Telegram message
   - Backend validates hash match in SQLite
   - On success: Create session, link to parent profile
   - On failure: Increment failed attempt counter

3. **Rate Limiting**:
   - Redis-based rate limiting: 5 attempts per phone number per hour
   - After 5 failures: Temporary lockout (1 hour) + admin notification
   - Log all validation attempts (success/failure) in audit table (FR-051)

4. **Code Generation**:
   - 8-character alphanumeric codes (uppercase + digits, excluding ambiguous chars)
   - Format: `CAT-XXXX` (e.g., `CAT-7K9M`)
   - Collision-resistant: ~2.8 trillion combinations

5. **Code Distribution**:
   - Generated during first enrollment or by administrator
   - Sent to parent via SMS or printed on registration receipt
   - One code per parent (covers all their children)

**Logging Compliance**:
- Log validation attempts WITHOUT logging the actual code (Principle V)
- Log format: `{"event": "code_validation", "phone": "hash", "success": bool, "timestamp": "..."}`

### Alternatives Considered

- **Plain text codes rejected**: Violates Constitution Principle V (no credentials in logs/database)
- **JWT tokens rejected**: Over-engineered for simple parent code, adds complexity
- **OTP SMS rejected**: Adds external SMS provider dependency and cost, code parent is simpler for low-tech users

---

## 6. OCR Testing Strategy

### Decision: Three-tier testing approach (mock, fixture, golden master)

### Rationale

**Testing Challenge**: Achieve 80%+ test coverage (Constitution Principle VI) for OCR service without requiring live OCR in every test run.

**Three-Tier Strategy**:

### Tier 1: Unit Tests with Mocked OCR (Fast)
```python
@pytest.fixture
def mock_ocr_service():
    with patch('easyocr.Reader') as mock:
        mock.readtext.return_value = [
            (['John Doe'], 0.95),
            (['01/01/2020'], 0.89),
        ]
        yield mock
```
- Tests: Service logic, error handling, confidence scoring
- Coverage: Business logic paths (80% of LOC)
- Execution time: < 1 second per test

### Tier 2: Integration Tests with Fixture Documents (Slow)
```
tests/fixtures/
├── sample_birth_certificate.pdf      # Clean scan, high quality
├── sample_birth_certificate_poor.pdf # Low quality, tests fallback
├── sample_baptism_certificate.jpg    # JPEG format
└── sample_mobile_money_orange.png    # Orange Money screenshot
```
- Tests: Real OCR extraction, preprocessing pipeline, accuracy
- Coverage: OCR integration, format handling
- Execution time: 30-60 seconds per test (run in CI only)
- Validation: Assert extracted data matches known golden values

### Tier 3: Golden Master Testing (Regression)
- Store expected OCR output for each fixture document
- Tests verify OCR output hasn't regressed across updates
- JSON format:
```json
{
  "birth_certificate": {
    "name": "John Doe",
    "date_of_birth": "01/01/2020",
    "confidence": 0.95
  }
}
```

**Test Organization**:
- Unit tests (mocked): Run on every commit
- Integration tests (fixtures): Run in CI pipeline
- Golden master tests: Run before releases

**Achieving 80% Coverage**:
- OCR service logic: 100% (mocked unit tests)
- Document validation: 100% (mocked unit tests)
- Enrollment flows: 90% (mocked OCR responses)
- Real OCR integration: Contract tests only (not counted in coverage)

### Alternatives Considered

- **Live OCR in all tests rejected**: Too slow (10s per test), CI would take hours
- **No fixture tests rejected**: Can't verify real OCR accuracy, violates SC-002 (>85% accuracy requirement)
- **Only mock tests rejected**: Wouldn't catch real OCR regressions or preprocessing bugs

---

## 7. SQLite Historical Data Strategy

### Decision: Start fresh, provide CSV import for legacy data

### Rationale

**Context**: Original spec (FR-036, FR-037) required Baserow integration for historical catechism data. With Baserow excluded, need strategy for existing data.

**Selected Approach**:
1. **Primary**: Start with empty database, new enrollments only
2. **Migration Tool**: CSV import script for administrators
   - Input: CSV export from Baserow (tables 575, 574, 572, 576, 577)
   - Output: Populated SQLite `catechese_app.db`
   - Mapping: Baserow IDs → SQLite UUIDs, preserve relationships
   - Validation: Data integrity checks before import

**CSV Import Format** (example for students):
```csv
nom,prenom,date_naissance,lieu_naissance,date_bapteme,paroisse_bapteme
Diallo,Amadou,2015-03-12,Dakar,2015-06-20,Paroisse Saint-Pierre
```

**Migration Script** (`scripts/import_legacy_data.py`):
- Validates CSV format and required columns
- Creates parent profiles with generated code_parent
- Links students to parents via relationships
- Imports historical enrollment records (read-only)
- Generates migration report (success count, errors, warnings)

**Deployment Strategy**:
1. Deploy new enrollment system (empty database)
2. Test with new enrollments for 1-2 weeks
3. If needed, run CSV import for historical data
4. Historical data marked as "imported" (not editable via enrollment flow)

### Alternatives Considered

- **Baserow API integration rejected**: User explicitly excluded Baserow from architecture
- **Manual re-entry rejected**: Too time-consuming for 500+ students
- **Supabase as historical data store rejected**: Would duplicate SQLite data, violates single source of truth

---

## Summary of Technical Decisions

| Decision Area | Selected Solution | Key Benefit |
|---------------|------------------|-------------|
| OCR Library | EasyOCR with manual fallback | High accuracy for French documents, offline |
| SQLite Concurrency | WAL mode + connection pooling | Supports 500-1000 concurrent users |
| Document Storage | MinIO hierarchical by year/student | Scalable, GDPR-compliant lifecycle |
| Payment OCR | Template matching + hybrid validation | Handles operator variations, treasurer validation |
| Code Parent Security | bcrypt hashing + rate limiting | Secure, no credential leaks |
| OCR Testing | Three-tier (mock/fixture/golden) | 80%+ coverage, fast CI |
| Historical Data | CSV import tool | Flexible, no Baserow dependency |

All decisions align with Constitution principles (Type Safety, Security, Testing, GDPR) and meet specification requirements.

**Next Phase**: Phase 1 Design (data-model.md, API contracts, quickstart.md)
