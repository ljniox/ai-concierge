"""
Direct setup using Supabase Management API with access token
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def setup_via_management_api():
    """Setup using Supabase Management API"""

    print("🚀 Setting up via Supabase Management API")
    print("=" * 50)

    # Configuration
    access_token = "sbp_9a140c9b81cc934009e9a7328da8a5bb0fddf57f"
    supabase_url = os.getenv('SUPABASE_URL')
    project_ref = "ixzpejqzxvxpnkbznqnj"

    if not supabase_url:
        print("❌ SUPABASE_URL not found in .env")
        return False

    print(f"📋 Project Reference: {project_ref}")
    print(f"🔗 Supabase URL: {supabase_url}")

    # Management API endpoints
    base_url = "https://api.supabase.com"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Test API access
    print("\n🔐 Testing API access...")
    try:
        response = requests.get(
            f"{base_url}/v1/projects/{project_ref}",
            headers=headers
        )

        if response.status_code == 200:
            print("✅ API access successful")
            project_info = response.json()
            print(f"📋 Project: {project_info.get('name', 'Unknown')}")
        else:
            print(f"❌ API access failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

    # Try to create tables using SQL RPC
    print("\n🔧 Creating tables via SQL execution...")

    # SQL for creating tables
    sql_statements = [
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

    # Use the postgres endpoint to execute SQL
    postgres_url = f"https://api.supabase.com/v1/projects/{project_ref}/postgres/query"

    for i, sql in enumerate(sql_statements, 1):
        print(f"\n📝 Executing SQL statement {i}/{len(sql_statements)}...")

        try:
            response = requests.post(
                postgres_url,
                headers=headers,
                json={"query": sql}
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Statement {i} executed successfully")
                print(f"   Result: {result}")
            else:
                print(f"❌ Statement {i} failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error executing statement {i}: {e}")
            return False

    return True

def test_tables():
    """Test if tables were created"""

    print("\n🧪 Testing table creation...")

    from supabase import create_client, Client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing credentials for testing")
        return False

    client: Client = create_client(supabase_url, supabase_key)

    tables = ['temporary_pages', 'receipts', 'page_access_logs']
    working_tables = 0

    for table in tables:
        try:
            result = client.table(table).select('*').limit(1).execute()
            print(f"✅ {table}: Working")
            working_tables += 1
        except Exception as e:
            print(f"❌ {table}: Failed - {e}")

    return working_tables == 3

def create_test_data():
    """Create some test data to verify functionality"""

    print("\n🧪 Creating test data...")

    from supabase import create_client, Client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    client: Client = create_client(supabase_url, supabase_key)

    # Test temporary page
    try:
        test_page = {
            'title': 'Test Temporary Page',
            'content': {'test': True, 'created_at': '2025-09-27T19:00:00Z'},
            'created_by': 'setup_script',
            'expires_at': '2025-12-31T23:59:59Z'
        }

        result = client.table('temporary_pages').insert(test_page).execute()
        if result.data:
            print("✅ Test temporary page created")
            return True
        else:
            print("❌ Failed to create test temporary page")
            return False
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return False

def main():
    """Main function"""
    print("Direct Temporary Pages Setup with Access Token")
    print("Using Supabase Management API to create tables")
    print()

    try:
        # Setup via management API
        setup_success = setup_via_management_api()

        if setup_success:
            # Test the tables
            test_success = test_tables()

            if test_success:
                print(f"\n🎉 Tables created successfully!")

                # Create test data
                data_success = create_test_data()

                if data_success:
                    print(f"\n✅ System is fully functional!")
                    print(f"\n📋 You can now test the system:")
                    print(f"   python3 test_temp_pages_system.py")
                else:
                    print(f"\n⚠️  Tables created but test failed")
            else:
                print(f"\n❌ Tables may not have been created properly")
        else:
            print(f"\n❌ Setup failed")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()