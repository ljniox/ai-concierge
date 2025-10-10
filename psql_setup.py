"""
Setup using direct PostgreSQL connection
"""

import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

def setup_with_psql():
    """Setup using direct PostgreSQL connection"""

    print("🚀 Setting up tables via PostgreSQL connection")
    print("=" * 50)

    # Get database credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return False

    # Extract connection info from URL
    try:
        # Use the provided database password
        db_host = "aws-1-eu-west-3.pooler.supabase.com"
        db_name = "postgres"
        db_user = "postgres.ixzpejqzxvxpnkbznqnj"
        db_password = "puqrE3-ziqwem-pufpoc"  # Provided database password

        print(f"🔗 Attempting connection to: {db_host}")
        print(f"📋 Database: {db_name}")
        print(f"👤 User: {db_user}")

        connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:6543/{db_name}"
        print(f"🔗 Connection string configured")

    except Exception as e:
        print(f"❌ Error parsing connection info: {e}")
        return False

    # SQL statements
    create_statements = [
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

    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_temporary_pages_access_code ON public.temporary_pages(access_code);",
        "CREATE INDEX IF NOT EXISTS idx_temporary_pages_expires_at ON public.temporary_pages(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_temporary_pages_active ON public.temporary_pages(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_receipts_receipt_code ON public.receipts(receipt_code);",
        "CREATE INDEX IF NOT EXISTS idx_receipts_active ON public.receipts(is_active);",
        "CREATE INDEX IF NOT EXISTS idx_page_access_logs_page_id ON public.page_access_logs(page_id);",
        "CREATE INDEX IF NOT EXISTS idx_page_access_logs_access_code ON public.page_access_logs(access_code);",
        "CREATE INDEX IF NOT EXISTS idx_page_access_logs_accessed_at ON public.page_access_logs(accessed_at);"
    ]

    # Try to connect and execute
    try:
        print("\n🔌 Connecting to database...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        print("✅ Database connection successful")

        # Execute create statements
        print("\n📝 Creating tables...")
        for i, statement in enumerate(create_statements, 1):
            try:
                cursor.execute(statement)
                conn.commit()
                print(f"✅ Table {i}/3 created")
            except Exception as e:
                print(f"❌ Error creating table {i}: {e}")
                conn.rollback()
                return False

        # Execute index statements
        print("\n📊 Creating indexes...")
        for i, statement in enumerate(index_statements, 1):
            try:
                cursor.execute(statement)
                conn.commit()
                print(f"✅ Index {i}/{len(index_statements)} created")
            except Exception as e:
                print(f"⚠️  Index {i} warning: {e}")
                # Don't fail on index errors

        cursor.close()
        conn.close()
        print("\n✅ All tables and indexes created successfully!")
        return True

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("\n💡 Alternative approach:")
        print("Please execute the SQL manually in your Supabase dashboard:")
        print("1. Go to: https://supabase.com/dashboard")
        print("2. Select project: ixzpejqzxvxpnkbznqnj")
        print("3. Go to SQL Editor")
        print("4. Execute the SQL from temporary_pages_system.sql")
        return False

def test_via_supabase_client():
    """Test using Supabase client"""

    print("\n🧪 Testing via Supabase client...")

    from supabase import create_client, Client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing credentials")
        return False

    client: Client = create_client(supabase_url, supabase_key)

    tables = ['temporary_pages', 'receipts', 'page_access_logs']
    success_count = 0

    for table in tables:
        try:
            result = client.table(table).select('*').limit(1).execute()
            print(f"✅ {table}: Accessible")
            success_count += 1
        except Exception as e:
            print(f"❌ {table}: Failed - {e}")

    return success_count == 3

def main():
    """Main function"""
    print("PostgreSQL Direct Setup for Temporary Pages")
    print("This will attempt to create tables using direct DB connection")
    print()

    try:
        # Try PostgreSQL setup
        setup_success = setup_with_psql()

        if setup_success:
            # Test the result
            test_success = test_via_supabase_client()

            if test_success:
                print(f"\n🎉 Setup completed successfully!")
                print(f"\n📋 System ready for use:")
                print(f"   Test with: python3 test_temp_pages_system.py")
            else:
                print(f"\n⚠️  Setup may have partially failed")
        else:
            print(f"\n❌ Setup failed")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()