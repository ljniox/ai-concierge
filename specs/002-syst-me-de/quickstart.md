# Quickstart: Enrollment Management System

**Feature**: Système de Gestion de Profils et Inscriptions avec SQLite
**Branch**: `002-syst-me-de`
**Date**: 2025-10-11

## Overview

This quickstart guide provides step-by-step instructions for developers to set up, run, and test the enrollment management system locally.

---

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- Access to existing `/home/ubuntu/ai-concierge/sdb_cate.sqlite` database (509 students, 341 parents)

---

## Setup

### 1. Clone and Navigate to Project

```bash
cd /home/ubuntu/ai-concierge
git checkout 002-syst-me-de
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Additional dependencies for this feature
pip install \
  easyocr==1.7.0 \
  aiosqlite==0.19.0 \
  bcrypt==4.1.2 \
  minio==7.2.3 \
  pydantic==2.5.3
```

### 4. Environment Configuration

Create or update `.env` file with new enrollment-specific variables:

```bash
# Existing variables (keep these)
SUPABASE_URL=https://ixzpejqzxvxpnkbznqnj.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
REDIS_URL=redis://redis:6379/0
WAHA_BASE_URL=https://waha-core.niox.ovh
WAHA_API_TOKEN=28C5435535C2487DAFBD1164B9CD4E34
ANTHROPIC_MODEL=glm-4.5
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_AUTH_TOKEN=0ee8c49b8ea94d7e84bf747d4286fecd.SNHHi7BSHuxTofkf

# NEW: Enrollment system settings
SQLITE_DB_PATH=/home/ubuntu/ai-concierge/sdb_cate.sqlite
SQLITE_TEMP_PAGES_DB=./data/temp_pages_system.db
SQLITE_CORE_DB=./data/core_system.db

# NEW: MinIO settings (if not already configured)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=sdb-catechese
MINIO_SECURE=false

# NEW: OCR settings
OCR_CONFIDENCE_THRESHOLD=0.70
OCR_MAX_RETRY_COUNT=3
OCR_TIMEOUT_SECONDS=30

# NEW: Enrollment settings
INSCRIPTION_DEFAULT_MONTANT=15000
CODE_PARENT_LENGTH=8
TEMP_PAGE_EXPIRATION_DAYS=7
```

### 5. Database Migration

Run migration to add new tables to existing `sdb_cate.sqlite`:

```bash
python src/database/migration_runner.py \
  --db=/home/ubuntu/ai-concierge/sdb_cate.sqlite \
  --migration=src/database/migrations/add_enrollment_tables_v1.0.0.sql
```

Expected output:
```
Migration: add_enrollment_tables_v1.0.0
Tables to create: inscriptions, documents, paiements, profil_utilisateurs, action_logs
✓ Table 'inscriptions' created
✓ Table 'documents' created
✓ Table 'paiements' created
✓ Table 'profil_utilisateurs' created
✓ Table 'action_logs' created
✓ Indexes created (15 indexes)
✓ Triggers created (3 triggers)
Migration completed successfully
```

### 6. Initialize New Databases

```bash
python src/database/sqlite_manager.py init
```

This creates:
- `data/temp_pages_system.db` (empty, ready for temporary pages)
- `data/core_system.db` (with application registry)

### 7. Start MinIO (Document Storage)

```bash
docker-compose up -d minio
```

Create bucket:
```bash
docker exec -it minio mc mb local/sdb-catechese
docker exec -it minio mc anonymous set download local/sdb-catechese
```

---

## Running the System

### Development Mode

```bash
# Start FastAPI with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Mode

```bash
docker-compose up -d ai-concierge-app
```

### Verify Services

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "supabase": "connected",
    "redis": "connected",
    "sqlite_catechese": "connected",
    "sqlite_temp_pages": "connected",
    "sqlite_core": "connected",
    "minio": "connected",
    "waha": "connected"
  }
}
```

---

## Testing

### Unit Tests

```bash
# Run all enrollment tests
pytest tests/unit/test_enrollment_service.py -v

# Run OCR tests
pytest tests/unit/test_ocr_service.py -v

# Run with coverage
pytest tests/unit/ --cov=src/services --cov-report=html
```

### Integration Tests

```bash
# Full enrollment flow (requires test fixtures)
pytest tests/integration/test_enrollment_flow.py -v

# Payment validation flow
pytest tests/integration/test_payment_validation_flow.py -v
```

### Manual API Testing

#### 1. Create Test Parent Profile

```bash
curl -X POST http://localhost:8000/api/v1/profiles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "nom": "Test",
    "prenom": "Parent",
    "role": "parent",
    "telephone": "+221770000001",
    "canal_prefere": "whatsapp",
    "code_parent": "test123"
  }'
```

#### 2. Authenticate as Parent

```bash
curl -X POST http://localhost:8000/api/v1/auth/code-parent \
  -H "Content-Type: application/json" \
  -d '{
    "telephone": "+221770000001",
    "code_parent": "CAT-TEST"
  }'

# Save the access_token from response
export PARENT_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### 3. Create Enrollment

```bash
curl -X POST http://localhost:8000/api/v1/enrollments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -d '{
    "nom_enfant": "DIALLO",
    "prenom_enfant": "Amadou",
    "date_naissance": "2015-03-12",
    "lieu_naissance": "Dakar",
    "annee_catechetique": "2025-2026",
    "montant_total": 15000
  }'

# Save inscription_id from response
export INSCRIPTION_ID="550e8400-e29b-41d4-a716-446655440000"
```

#### 4. Upload Birth Certificate

```bash
curl -X POST "http://localhost:8000/api/v1/enrollments/$INSCRIPTION_ID/documents" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -F "file=@tests/fixtures/sample_birth_certificate.pdf" \
  -F "type_document=extrait_naissance"

# Response includes OCR status
{
  "id": "...",
  "statut_ocr": "en_cours",
  "confiance_ocr": null
}
```

#### 5. Check OCR Results

```bash
# Poll for OCR completion (takes 5-10 seconds)
curl "http://localhost:8000/api/v1/documents/$DOCUMENT_ID" \
  -H "Authorization: Bearer $PARENT_TOKEN"

# When statut_ocr = "succes":
{
  "id": "...",
  "statut_ocr": "succes",
  "confiance_ocr": 0.92,
  "donnees_extraites": {
    "nom": "DIALLO",
    "prenom": "Amadou",
    "date_naissance": "12/03/2015",
    "lieu_naissance": "Dakar"
  },
  "valide_par_parent": false
}
```

#### 6. Validate OCR Data

```bash
curl -X POST "http://localhost:8000/api/v1/documents/$DOCUMENT_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -d '{
    "donnees_validees": {
      "nom": "DIALLO",
      "prenom": "Amadou",
      "date_naissance": "2015-03-12",
      "lieu_naissance": "Dakar"
    }
  }'
```

#### 7. Submit Payment

```bash
# Upload Mobile Money screenshot first
curl -X POST "http://localhost:8000/api/v1/enrollments/$INSCRIPTION_ID/documents" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -F "file=@tests/fixtures/sample_mobile_money_receipt.png" \
  -F "type_document=preuve_paiement"

# Submit payment with proof
curl -X POST "http://localhost:8000/api/v1/enrollments/$INSCRIPTION_ID/payments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $PARENT_TOKEN" \
  -d '{
    "montant": 15000,
    "mode_paiement": "orange_money",
    "reference": "TX-12345678",
    "preuve_document_id": "...(document_id from upload)"
  }'
```

#### 8. Treasurer Validates Payment

```bash
# Get pending payments (as treasurer)
curl http://localhost:8000/api/v1/payments/pending \
  -H "Authorization: Bearer $TREASURER_TOKEN"

# Validate payment
curl -X POST "http://localhost:8000/api/v1/payments/$PAIEMENT_ID/validate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TREASURER_TOKEN" \
  -d '{
    "action": "valider"
  }'

# Check enrollment status (should now be "active")
curl "http://localhost:8000/api/v1/enrollments/$INSCRIPTION_ID" \
  -H "Authorization: Bearer $PARENT_TOKEN"
```

---

## Common Development Tasks

### Add New User Profile

```python
from src.services.profile_service import ProfileService
from src.models.profile import CreateProfileRequest

service = ProfileService()
profile = await service.create_profile(
    request=CreateProfileRequest(
        nom="Doe",
        prenom="John",
        role="catechiste",
        telephone="+221770000002",
        canal_prefere="telegram"
    )
)
print(f"Created profile: {profile.user_id}")
```

### Generate Temporary Page

```python
from src.services.temp_page_service import TempPageService

service = TempPageService()
page = await service.create_temp_page(
    utilisateur_associe_id="parent-user-id",
    objet="inscription",
    createur_id="staff-user-id",
    expiration_days=7
)
print(f"Page URL: {page.url_complete}")
print(f"Access code: {page.code_acces}")
```

### Query Legacy Data

```python
from src.database.sqlite_manager import SQLiteManager

manager = SQLiteManager()
conn = await manager.get_connection("catechese")

# Get legacy parent by Code_Parent
cursor = await conn.execute(
    "SELECT * FROM parents_2 WHERE Code_Parent = ?",
    ("57704",)
)
parent = await cursor.fetchone()

# Get legacy student data
cursor = await conn.execute(
    "SELECT * FROM catechumenes_2 WHERE Code_Parent = ?",
    ("57704",)
)
students = await cursor.fetchall()
```

### Run Database Backup

```bash
python src/database/sqlite_manager.py backup

# Output:
# Backup created: /home/ubuntu/ai-concierge/backups/sdb_cate_2025-10-11_14-30-00.sqlite
# Backup created: /home/ubuntu/ai-concierge/backups/temp_pages_2025-10-11_14-30-00.db
# Backup created: /home/ubuntu/ai-concierge/backups/core_2025-10-11_14-30-00.db
```

---

## Troubleshooting

### OCR Not Working

**Problem**: `statut_ocr` stays "en_attente"

**Solution**:
```bash
# Check OCR worker is running
ps aux | grep ocr_worker

# Restart worker
python src/services/ocr_worker.py &

# Check logs
tail -f logs/ocr_worker.log
```

### Database Locked Error

**Problem**: `sqlite3.OperationalError: database is locked`

**Solution**:
```bash
# Check WAL mode is enabled
python -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/ai-concierge/sdb_cate.sqlite')
print(conn.execute('PRAGMA journal_mode').fetchone())
# Should return: ('wal',)
"

# If not WAL, enable it
sqlite3 /home/ubuntu/ai-concierge/sdb_cate.sqlite "PRAGMA journal_mode=WAL;"
```

### MinIO Connection Failed

**Problem**: `ConnectionError: Unable to connect to MinIO`

**Solution**:
```bash
# Check MinIO is running
docker ps | grep minio

# Test connection
curl http://localhost:9000/minio/health/live

# Restart MinIO
docker-compose restart minio
```

### Legacy Data Not Found

**Problem**: Cannot find parent with Code_Parent

**Solution**:
```bash
# Verify legacy data still exists
python -c "
import sqlite3
conn = sqlite3.connect('/home/ubuntu/ai-concierge/sdb_cate.sqlite')
count = conn.execute('SELECT COUNT(*) FROM parents_2').fetchone()[0]
print(f'Parents in database: {count}')
"

# Should print: Parents in database: 341
```

---

## Next Steps

1. **Implement Tasks**: Generate implementation tasks with `/speckit.tasks`
2. **Begin Coding**: Start with Priority 1 (MVP) user stories
3. **Run Tests**: Maintain > 80% coverage per constitution
4. **Deploy**: Follow deployment gates in constitution

---

## Documentation Links

- [Feature Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Research Decisions](./research.md)
- [Data Model](./data-model.md)
- [API Contracts](./contracts/enrollment-api.yaml)
- [Constitution](./.specify/memory/constitution.md)

---

**Last Updated**: 2025-10-11
