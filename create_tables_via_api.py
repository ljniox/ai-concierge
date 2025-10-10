"""
Create temporary pages tables using direct Supabase API calls
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

load_dotenv()

def create_tables_via_rpc():
    """Create tables using PostgreSQL RPC if available"""

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False

    print("🔧 Creating tables via direct SQL execution...")

    # SQL statements for table creation
    table_sql = {
        'temporary_pages': """
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
        'receipts': """
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
        'page_access_logs': """
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
    }

    client: Client = create_client(supabase_url, supabase_key)

    # Try to create a generic exec function first
    try:
        # Create a simple function to execute SQL
        create_exec_function = """
            CREATE OR REPLACE FUNCTION exec_sql(sql_text TEXT)
            RETURNS VOID
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            BEGIN
                EXECUTE sql_text;
            END;
            $$;
        """

        # Try to execute via RPC
        result = client.rpc('exec_sql', {'sql_text': create_exec_function}).execute()
        print("✅ Created exec_sql function")

        # Now create the tables
        for table_name, sql in table_sql.items():
            try:
                result = client.rpc('exec_sql', {'sql_text': sql}).execute()
                print(f"✅ Created table: {table_name}")
            except Exception as e:
                print(f"❌ Failed to create table {table_name}: {e}")

        # Test the tables
        print("\n🧪 Testing created tables...")
        for table_name in ['temporary_pages', 'receipts', 'page_access_logs']:
            try:
                result = client.table(table_name).select('*').limit(1).execute()
                print(f"✅ {table_name}: Accessible")
            except Exception as e:
                print(f"❌ {table_name}: Not accessible - {e}")

        return True

    except Exception as e:
        print(f"❌ RPC method failed: {e}")
        return False

def create_tables_via_http():
    """Alternative method using direct HTTP requests"""

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')

    if not all([supabase_url, supabase_key, supabase_anon_key]):
        print("❌ Missing Supabase credentials")
        return False

    print("🔧 Creating tables via HTTP API...")

    # Try to create tables by forcing schema cache refresh
    headers = {
        'apikey': supabase_anon_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }

    # Try to create the tables by inserting test data
    tables_to_create = [
        ('temporary_pages', {
            'title': 'Test Creation',
            'content': {'test': True},
            'created_by': 'system',
            'expires_at': '2025-12-31T23:59:59Z'
        }),
        ('receipts', {
            'title': 'Test Receipt',
            'content': {'test': True},
            'created_by': 'system'
        }),
        ('page_access_logs', {
            'page_type': 'test',
            'access_code': '00000000-0000-0000-0000-000000000000'
        })
    ]

    for table_name, test_data in tables_to_create:
        try:
            url = f"{supabase_url}/rest/v1/{table_name}"
            response = requests.post(url, headers=headers, json=test_data)

            if response.status_code == 201:
                print(f"✅ Table {table_name} created successfully")

                # Clean up test data
                try:
                    delete_url = f"{supabase_url}/rest/v1/{table_name}?title=eq.Test%20Creation"
                    requests.delete(delete_url, headers=headers)
                except:
                    pass
            else:
                print(f"❌ Failed to create table {table_name}: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"❌ Error creating table {table_name}: {e}")

    return True

def main():
    """Main function"""
    print("🚀 Temporary Pages Table Creation Tool")
    print("=" * 50)

    # Try RPC method first
    print("Method 1: RPC SQL Execution")
    rpc_success = create_tables_via_rpc()

    if not rpc_success:
        print("\nMethod 2: HTTP API")
        http_success = create_tables_via_http()

        if http_success:
            print("\n✅ Tables created successfully via HTTP method")
        else:
            print("\n❌ Both methods failed")
            print("\n📋 Manual Setup Required:")
            print("1. Go to your Supabase dashboard: https://supabase.com/dashboard")
            print("2. Select project: ixzpejqzxvxpnkbznqnj")
            print("3. Go to SQL Editor")
            print("4. Execute the SQL from temporary_pages_system.sql")
            return

    # Test final result
    print(f"\n🧪 Final Table Access Test:")

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client: Client = create_client(supabase_url, supabase_key)

    tables = ['temporary_pages', 'receipts', 'page_access_logs']
    working_tables = 0

    for table in tables:
        try:
            result = client.table(table).select('*').limit(1).execute()
            print(f"   ✅ {table}: Working")
            working_tables += 1
        except Exception as e:
            print(f"   ❌ {table}: Failed - {e}")

    if working_tables == 3:
        print(f"\n🎉 All tables created successfully!")
        print(f"\n📋 System ready for testing:")
        print(f"   Run: python3 test_temp_pages_system.py")
    else:
        print(f"\n⚠️  Only {working_tables}/3 tables working")
        print(f"   Manual setup may still be required")

if __name__ == "__main__":
    main()