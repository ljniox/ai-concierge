# Agent Setup Guide - SDB (Service Diocésain de la Catéchèse)

## Quick Start for New Agents

This guide provides everything needed to work with SDB data sources in a new session or with another agent.

## Required Setup

### MCP Servers Configuration

The project includes MCP (Model Context Protocol) servers for enhanced functionality:

**Firecrawl MCP Server:**
- **Purpose**: Web scraping and content extraction
- **Configuration**: `mcp_config.json`
- **API Key**: Stored in `FIRECRAWL_API_KEY` environment variable

To use MCP servers, ensure the configuration is loaded in your Claude Code session.

### WhatsApp AI Concierge Service

**Production Technology Stack:**
- **Backend**: FastAPI (Python) for webhook and API endpoints
- **WhatsApp Integration**: WAHA SDK for WhatsApp Business API
- **Database**: Supabase (PostgreSQL) for session and service management
- **AI Orchestration**: Claude SDK with glm-4.5 model
- **Caching**: Redis for session state
- **Deployment**: Docker with container networking

**Key Endpoints:**
- `/api/v1/webhook` - WhatsApp message handling
- `/api/v1/orchestrate` - AI response orchestration
- `/api/v1/sessions/*` - Session management
- `/health` - System health monitoring

**Core Services:**
- **RENSEIGNEMENT** - General information service
- **CATECHESE** - Catechism service with code_parent authentication
- **CONTACT_HUMAIN** - Human agent handoff service

**Container Architecture:**
- `ai-concierge-app-1` - Main application container
- `waha-core` - WhatsApp API integration
- `redis` - Session caching
- Fixed container networking with service discovery

### 1. Environment Configuration (.env file)

Create a `.env` file in the working directory:

```bash
# Baserow Settings
BASEROW_URL=https://sdbaserow.3xperts.tech
BASEROW_AUTH_KEY=q80kPF01T0zp9gXehV5bYennCIGrqQwk

# Supabase Settings
SUPABASE_URL=https://ixzpejqzxvxpnkbznqnj.supabase.co
SUPABASE_PASSWORD=puqrE3-ziqwem-pufpoc
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml4enBlanF6eHZ4cG5rYnpucW5qIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc3MDg1MjgsImV4cCI6MjA3MzI4NDUyOH0.uOLdQu-Lub8UjzqEreLHRMqLWKAsS-c521W_8pvSYb4
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml4enBlanF6eHZ4cG5rYnpucW5qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzcwODUyOCwiZXhwIjoyMDczMjg0NTI4fQ.Jki6OqWq0f1Svd2u2m8Zt3xbust-fSlRlSMcWvnsOz4

# WhatsApp AI Concierge Production Settings
WEBHOOK_URL=http://ai-concierge-app-1:8000/api/v1/webhook
CONCIERGE_API_URL=http://ai-concierge-app-1:8000
WAHA_BASE_URL=https://waha-core.niox.ovh
WAHA_API_TOKEN=28C5435535C2487DAFBD1164B9CD4E34
ANTHROPIC_AUTH_TOKEN=0ee8c49b8ea94d7e84bf747d4286fecd.SNHHi7BSHuxTofkf
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_MODEL=glm-4.5
REDIS_URL=redis://redis:6379/0
```

### 2. Rclone Configuration

The rclone drive "sdb" is already configured. To use it:

```bash
# Verify rclone is available
rclone --version

# Check if sdb remote is configured
rclone ls sdb:

# If not configured, set it up:
rclone config
# Follow prompts to add Google Drive remote named "sdb"
```

## Available Data Sources

### 1. Baserow Database API

**Base URL:** https://sdbaserow.3xperts.tech

**Authentication:** Token-based (using BASEROW_AUTH_KEY)

**Key Tables:**
- `Catechumenes` (ID: 575) - Student information
- `Inscriptions` (ID: 574) - Enrollment records  
- `Parents` (ID: 572) - Parent contact information
- `Notes` (ID: 576) - Student grades
- `Classes` (ID: 577) - Class information

### 2. Google Drive (via rclone)

**Remote Name:** `sdb`

**Key Directories:**
- `Annee 2024-2025/` - Current year documents
- `GESTION CATE APP/` - Management application files
- `Gestion Catechese DB/` - Database files

**File Types:**
- `EB - *.pdf/jpg` - Baptism certificates
- `attestation_catechese *.pdf` - Catechism certificates
- `CARNET-*.pdf` - Student booklets

## Common Operations

### Search Student Information

```bash
# Search in Baserow by name
source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
"https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true&search=StudentName"

# Get enrollment details
source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
"https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true&search=StudentID"
```

### Search Documents in Google Drive

```bash
# Find baptism certificates
rclone ls sdb: --include "EB *" --include "*.pdf" --include "*.jpg"

# Find catechism certificates  
rclone ls sdb: --include "attestation_catechese*"

# Search by student name
rclone ls sdb: --include "*StudentName*" --include "*.pdf"
```

### Download Files

```bash
# Download specific file
rclone copy sdb:"Annee 2024-2025/filename.pdf" ./

# Download all baptism certificates
rclone copy sdb:"Annee 2024-2025/EB - "*.pdf ./
```

## Student Data Workflow

### Complete Student Lookup

1. **Search Baserow for student**
   ```bash
   source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
   "https://sdbaserow.3xperts.tech/api/database/rows/table/575/?user_field_names=true&search=LastName"
   ```

2. **Get enrollment history**
   ```bash
   source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
   "https://sdbaserow.3xperts.tech/api/database/rows/table/574/?user_field_names=true&search=StudentUUID"
   ```

3. **Find parent information**
   ```bash
   source .env && curl -H "Authorization: Token $BASEROW_AUTH_KEY" \
   "https://sdbaserow.3xperts.tech/api/database/rows/table/572/?user_field_names=true&search=ParentCode"
   ```

4. **Locate documents**
   ```bash
   rclone ls sdb: --include "*StudentName*" --include "EB *"
   ```

## Generate Catechism Certificate

1. Collect all student information from Baserow
2. Verify baptism certificate exists in Google Drive
3. Check enrollment status and grades
4. Use template to generate certificate
5. Include all relevant data points

## File Naming Conventions

### Baptism Certificates
- Format: `EB - First Last Name.ext`
- Location: `Annee 2024-2025/`
- Extensions: .pdf, .jpg, .jpeg, .png

### Catechism Certificates  
- Format: `attestation_catechese First Last Name.pdf`
- Location: `Annee 2024-2025/`

### Student Booklets
- Format: `CARNET-Level_First Last Name.pdf`
- Location: `GESTION CATE APP/S_IMPRESSIONS/Partage/`

## Security Notes

- Never expose BASEROW_AUTH_KEY in logs or shared documents
- Use environment variables for all sensitive data
- Verify file permissions on .env file (chmod 600 .env)
- Regular rotation of API tokens recommended

## Troubleshooting

### Common Issues

**Token Authentication Failed**
- Verify .env file exists and has correct BASEROW_AUTH_KEY
- Check BASEROW_URL is correct
- Ensure token has proper permissions

**Rclone Remote Not Found**
- Run `rclone config` to set up "sdb" remote
- Choose Google Drive as storage type
- Follow OAuth authentication flow

**Empty Results from API**
- Check search parameters
- Verify table IDs are correct
- Ensure student data exists in database

### Getting Help

1. Check `SOURCES_DOCUMENTATION.md` for detailed API documentation
2. Verify all setup steps are completed
3. Test connectivity to both Baserow and Google Drive
4. Contact SDB administrator for credential issues

## Next Steps

### SDB Data Sources
1. ✅ Create .env file with credentials
2. ✅ Verify rclone "sdb" remote is configured
3. ✅ Test API access to Baserow
4. ✅ Test file access to Google Drive
5. ✅ Review available documentation
6. ✅ Begin working with student data

### WhatsApp AI Concierge Service
1. ✅ Feature specification complete (`/specs/001-projet-concierge-ia/spec.md`)
2. ✅ Implementation plan complete (`/specs/001-projet-concierge-ia/plan.md`)
3. ✅ Core implementation complete
4. ✅ Fixed API configuration with container networking
5. ✅ Service architecture documentation complete (`SERVICES_ARCHITECTURE.md`)
6. 🔄 Production deployment and monitoring

## Development Principles

### Code Quality
- **Type Safety**: Use Python type hints throughout
- **Error Handling**: Comprehensive error handling with proper logging
- **Testing**: Unit and integration tests for all components
- **Documentation**: Inline documentation and architectural diagrams

### Security Best Practices
- **Environment Variables**: All sensitive data in .env files
- **API Security**: JWT tokens and webhook verification
- **Database Security**: Supabase RLS policies and service keys
- **Container Security**: Non-root users and minimal base images

## Execution Rules

### Mandatory Reporting Rule
**📢 ADMIN NOTIFICATION REQUIRED**: After completing any significant operation, test, or code execution, you MUST send a summary report to the admin number `221765005555` via WAHA API. This includes but is not limited to:

- End-to-end testing completion
- System feature demonstrations
- Bug fixes and troubleshooting
- Performance optimizations
- Security updates
- Database operations
- Code deployments

**Summary Format**:
```
📋 Gust-IA Execution Summary

Operation: [Operation Name]
Status: [Success/Partial/Failed]
Duration: [Time taken]
Key Results: [Main outcomes]
Next Steps: [Follow-up actions]

🙏 Gust-IA - Service Diocésain de la Catéchèse
```

**Implementation**: Use the WAHA API endpoint to send the summary:
```bash
curl -X POST "${WAHA_BASE_URL}/api/sendText" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${WAHA_API_TOKEN}" \
  -d '{
    "session": "default",
    "chatId": "221765005555@c.us",
    "text": "[summary message]"
  }'
```

### Auto-Save Documentation Rule
**📄 AUTO-SAVE REQUIRED**: After sending the WAHA execution summary, you MUST also save the execution details as a markdown file for documentation purposes.

**Implementation**: Use the execution logger utility:
```python
from src.utils.execution_logger import save_execution_summary_auto, save_waha_summary_auto

# Option 1: Save structured summary
filepath = save_execution_summary_auto(
    operation="[Operation Name]",
    status="[Success/Partial/Failed]",
    duration="[Time taken]",
    key_results=["Result 1", "Result 2"],
    next_steps=["Next step 1", "Next step 2"],
    technical_details={"fix": "description", "impact": "high"}
)

# Option 2: Auto-save from WAHA summary text
filepath = save_waha_summary_auto(summary_text)
```

**File Format**: `yyyy-mm-dd_glm-summary-title.md`
- **Location**: `execution_logs/` directory
- **Content**: Structured markdown with timestamps, results, and technical details
- **Purpose**: Maintain audit trail and enable historical analysis

### Deployment Architecture
- **Container Networking**: Use service names instead of IPs
- **Health Monitoring**: Comprehensive health check endpoints
- **Log Management**: Structured logging with appropriate levels
- **Scalability**: Horizontal scaling with load balancing

### Monitoring & Operations
- **Health Checks**: `/health` endpoint for all services
- **Logging**: JSON-formatted logs with correlation IDs
- **Metrics**: Request latency, success rates, error tracking
- **Alerting**: Critical error notifications and SLA monitoring
- **Execution Summaries**: After each significant operation or test execution, send a summary report to admin number `221765005555` via WAHA API

---
*Last Updated: September 20, 2025*
*Version: 2.0 - Production Ready*