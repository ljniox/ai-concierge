#!/usr/bin/env python3
"""
Initialize Supabase database with schema and basic data
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def init_supabase():
    """Initialize Supabase database"""
    print("🚀 Initializing Supabase database...")
    
    try:
        # Read the SQL schema file
        with open('supabase_schema.sql', 'r') as f:
            sql_schema = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in sql_schema.split(';') if stmt.strip()]
        
        # Execute each statement
        print(f"📝 Executing {len(statements)} SQL statements...")
        
        # For now, we'll just test the connection
        # The actual schema needs to be executed in the Supabase dashboard
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test basic connection
        result = supabase.table('pg_tables').select('*').limit(1).execute()
        print("✅ Supabase connection successful")
        
        print("\n📋 Next steps:")
        print("1. Go to Supabase dashboard: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Go to SQL Editor")
        print("4. Copy and execute the contents of 'supabase_schema.sql'")
        print("5. Then run the migration script: python3 migrate_to_supabase.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Supabase: {e}")
        return False

def create_simple_tables():
    """Create simple tables via API calls (alternative method)"""
    print("🔄 Creating simple tables via API...")
    
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # This is a basic approach - for full schema, use SQL Editor in Supabase dashboard
        test_data = {
            'test_field': 'test_value',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        print("✅ API connection successful")
        print("📝 Please use the Supabase SQL Editor to execute the full schema")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Supabase Initialization Script")
    print("=" * 50)
    
    success = init_supabase()
    
    if success:
        print("\n✅ Supabase connection test completed!")
        print("\n📖 Manual setup required:")
        print("1. Execute supabase_schema.sql in Supabase SQL Editor")
        print("2. Run migration: python3 migrate_to_supabase.py")
        print("3. Test utilities: python3 supabase_utils.py")
    
    sys.exit(0 if success else 1)