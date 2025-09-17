# SDB Supabase Migration Guide

## Overview
This guide explains how to migrate the SDB database from Baserow to Supabase to take advantage of advanced features.

## Prerequisites

1. **Supabase Account**: You have access to the Supabase project at https://ixzpejqzxvxpnkbznqnj.supabase.co
2. **Environment Setup**: `.env` file configured with Supabase credentials
3. **Python Dependencies**: `python-dotenv`, `supabase`, `requests`

## Setup Steps

### Step 1: Execute Database Schema

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **SQL Editor** in the left sidebar
4. Click **New query**
5. Copy the contents of `supabase_schema.sql`
6. Paste and execute the SQL

### Step 2: Run Migration Script

```bash
# Install dependencies if needed
pip3 install python-dotenv supabase requests

# Run the migration
python3 migrate_to_supabase.py
```

### Step 3: Verify Migration

```bash
# Test the utilities
python3 supabase_utils.py

# Test connection
python3 supabase_config.py
```

## Files Created

### Configuration Files
- `.env` - Environment variables (updated with Supabase credentials)
- `supabase_config.py` - Supabase client configuration
- `AGENTS.md` - Updated agent guide with Supabase info

### Database Schema
- `supabase_schema.sql` - Complete PostgreSQL schema with:
  - Tables: catechumenes, parents, inscriptions, classes, annees_scolaires, notes, files
  - Functions: get_student_info, get_student_grades, search_students
  - Indexes and RLS policies
  - Helper functions and triggers

### Migration Scripts
- `migrate_to_supabase.py` - Data migration from Baserow to Supabase
- `init_supabase.py` - Database initialization script
- `supabase_utils.py` - Utility functions for common operations

## Supabase Features Enabled

### 1. Advanced Query Capabilities
- Full-text search on student names
- Complex joins and relationships
- Aggregation functions for statistics

### 2. PostgreSQL Functions
- `get_student_info()` - Complete student profile
- `get_student_grades()` - Grade history
- `search_students()` - Fuzzy search

### 3. Enhanced Security
- Row Level Security (RLS) policies
- Service role key for admin operations
- Anonymous key for read-only operations

### 4. Performance Optimizations
- Indexes on frequently queried fields
- Full-text search indexes
- Optimized joins

## Usage Examples

### Student Search
```python
from supabase_utils import get_sdb_client

sdb = get_sdb_client()
students = sdb.search_student("MANEL")
```

### Get Student Information
```python
student_info = sdb.get_student_info("student_id_here")
print(f"Student: {student_info['prenoms']} {student_info['nom']}")
```

### Add Grades
```python
success = sdb.add_grade(
    id_inscription="inscription_id",
    trimestre=1,
    note=15.5,
    annee_scolaire="2024-2025"
)
```

### Class Statistics
```python
stats = sdb.get_class_stats("class_id", "year_id")
print(f"Payment rate: {stats['payment_rate']}%")
```

## API Endpoints

### Read Operations (Anonymous Key)
- Search students
- Get student information
- Get grades history
- Get class lists

### Write Operations (Service Role Key)
- Create/Update inscriptions
- Add grades
- Update student information
- Manage parent data

## Migration Status

- ✅ Schema design
- ✅ Configuration files
- ✅ Utility functions
- ⏳ Database creation (manual step required)
- ⏳ Data migration
- ⏳ Testing and validation

## Benefits of Supabase Migration

1. **Performance**: Faster queries with proper indexing
2. **Scalability**: Handle more concurrent users
3. **Features**: Real-time subscriptions, webhooks
4. **Security**: Built-in authentication and RLS
5. **Maintenance**: Easier backups and management

## Troubleshooting

### Common Issues

**Connection Error**
- Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in .env
- Check network connectivity

**Table Not Found**
- Execute the schema in Supabase SQL Editor first
- Verify all tables were created successfully

**Migration Errors**
- Check Baserow API credentials
- Verify data formats and types
- Look for duplicate entries

### Getting Help

1. Check this guide and schema file
2. Verify all setup steps are completed
3. Test with the utility scripts
4. Contact administrator if issues persist

## Next Steps

1. ✅ Setup complete
2. ⏳ Execute schema in Supabase dashboard
3. ⏳ Run migration script
4. ⏳ Test all functionality
5. ⏳ Update applications to use Supabase API

---
*Created: $(date)*
*Version: 1.0*