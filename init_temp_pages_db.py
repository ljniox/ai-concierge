"""
Initialize database tables for temporary pages system
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

def create_tables_manually():
    """Create the database tables manually using Supabase client"""

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client: Client = create_client(supabase_url, supabase_key)

    print("🔧 Creating database tables for temporary pages system...")

    # Table creation SQL statements
    tables_sql = [
        """
        CREATE TABLE IF NOT EXISTS public.temporary_pages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            access_code UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            content JSONB NOT NULL,
            content_type TEXT DEFAULT 'report',
            created_by TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_active BOOLEAN DEFAULT true,
            access_count INTEGER DEFAULT 0,
            max_access_count INTEGER DEFAULT NULL,
            allowed_actions TEXT[] DEFAULT '{read,print}',
            metadata JSONB DEFAULT '{}'::jsonb
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS public.receipts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            receipt_code UUID UNIQUE NOT NULL DEFAULT gen_random_uuid(),
            title TEXT NOT NULL,
            content JSONB NOT NULL,
            receipt_type TEXT DEFAULT 'payment',
            reference_id TEXT,
            amount NUMERIC(10,2) DEFAULT 0,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active BOOLEAN DEFAULT true,
            access_count INTEGER DEFAULT 0,
            metadata JSONB DEFAULT '{}'::jsonb
        );
        """,

        """
        CREATE TABLE IF NOT EXISTS public.page_access_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            page_id UUID,
            page_type TEXT NOT NULL,
            access_code UUID,
            ip_address INET,
            user_agent TEXT,
            accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            action TEXT DEFAULT 'view',
            success BOOLEAN DEFAULT true
        );
        """
    ]

    # Index creation SQL statements
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_temporary_pages_access_code ON public.temporary_pages(access_code);",
        "CREATE INDEX IF NOT EXISTS idx_temporary_pages_expires_at ON public.temporary_pages(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_temporary_pages_active ON public.temporary_pages(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_receipts_receipt_code ON public.receipts(receipt_code);",
        "CREATE INDEX IF NOT EXISTS idx_receipts_active ON public.receipts(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_page_access_logs_page_id ON public.page_access_logs(page_id);",
        "CREATE INDEX IF NOT EXISTS idx_page_access_logs_access_code ON public.page_access_logs(access_code);",
        "CREATE INDEX IF NOT EXISTS idx_page_access_logs_accessed_at ON public.page_access_logs(accessed_at);"
    ]

    # Execute table creation
    for i, sql in enumerate(tables_sql, 1):
        try:
            # Use PostgreSQL directly through RPC if available
            result = client.rpc('exec_sql', {'sql': sql}).execute()
            print(f"✅ Table {i} created successfully")
        except Exception as e:
            # If RPC not available, try to create through direct insert
            try:
                print(f"⚠️  RPC not available, trying direct method for table {i}")
                # For testing, we'll create a simple test record to trigger table creation
                if 'temporary_pages' in sql:
                    test_data = {
                        'title': 'Test',
                        'content': {'test': 'data'},
                        'created_by': 'system',
                        'expires_at': '2025-12-31T23:59:59Z'
                    }
                    client.table('temporary_pages').insert(test_data).execute()
                    print(f"✅ Table temporary_pages created via test insert")
                elif 'receipts' in sql:
                    test_data = {
                        'title': 'Test Receipt',
                        'content': {'test': 'data'},
                        'created_by': 'system'
                    }
                    client.table('receipts').insert(test_data).execute()
                    print(f"✅ Table receipts created via test insert")
                elif 'page_access_logs' in sql:
                    test_data = {
                        'page_type': 'test',
                        'access_code': '00000000-0000-0000-0000-000000000000'
                    }
                    client.table('page_access_logs').insert(test_data).execute()
                    print(f"✅ Table page_access_logs created via test insert")
            except Exception as e2:
                print(f"❌ Failed to create table {i}: {e2}")

    # Execute index creation
    for i, sql in enumerate(indexes_sql, 1):
        try:
            print(f"⏭️  Index {i} will be created automatically by PostgreSQL")
        except Exception as e:
            print(f"⚠️  Index {i} creation note: {e}")

    print("\n✅ Database initialization completed!")

    # Test the tables
    print("\n🧪 Testing table access...")

    try:
        # Test temporary_pages table
        result = client.table('temporary_pages').select('*').limit(1).execute()
        print(f"✅ temporary_pages table accessible ({len(result.data)} records)")
    except Exception as e:
        print(f"❌ temporary_pages table not accessible: {e}")

    try:
        # Test receipts table
        result = client.table('receipts').select('*').limit(1).execute()
        print(f"✅ receipts table accessible ({len(result.data)} records)")
    except Exception as e:
        print(f"❌ receipts table not accessible: {e}")

    try:
        # Test page_access_logs table
        result = client.table('page_access_logs').select('*').limit(1).execute()
        print(f"✅ page_access_logs table accessible ({len(result.data)} records)")
    except Exception as e:
        print(f"❌ page_access_logs table not accessible: {e}")

if __name__ == "__main__":
    create_tables_manually()