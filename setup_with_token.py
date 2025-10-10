"""
Setup temporary pages tables using Supabase access token
"""

import os
import subprocess
import json
from dotenv import load_dotenv

load_dotenv()

def setup_with_cli_token():
    """Setup using Supabase CLI with access token"""

    print("🚀 Setting up Temporary Pages System with Access Token")
    print("=" * 60)

    # Your access token
    access_token = "sbp_9a140c9b81cc934009e9a7328da8a5bb0fddf57f"

    # Check if Supabase CLI is installed
    try:
        result = subprocess.run(['supabase', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Supabase CLI found: {result.stdout.strip()}")
        else:
            print("❌ Supabase CLI not found")
            print("Please install it first: npm install -g supabase")
            return False
    except FileNotFoundError:
        print("❌ Supabase CLI not found")
        print("Please install it first: npm install -g supabase")
        return False

    # Login with access token
    print("\n🔐 Logging in with access token...")
    try:
        login_result = subprocess.run([
            'supabase', 'login', '--token', access_token
        ], capture_output=True, text=True)

        if login_result.returncode == 0:
            print("✅ Successfully logged in to Supabase")
        else:
            print(f"❌ Login failed: {login_result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False

    # Check if we have project reference
    supabase_url = os.getenv('SUPABASE_URL')
    if not supabase_url:
        print("❌ SUPABASE_URL not found in .env file")
        return False

    # Extract project reference from URL
    try:
        project_ref = supabase_url.split('https://')[1].split('.supabase.co')[0]
        print(f"📋 Project reference: {project_ref}")
    except:
        print("❌ Could not extract project reference from SUPABASE_URL")
        return False

    # Try to link project (if not already linked)
    print("\n🔗 Linking project...")
    try:
        # Check if already linked
        if os.path.exists('supabase/config.toml'):
            print("ℹ️  Supabase project already linked")
        else:
            link_result = subprocess.run([
                'supabase', 'link', '--project-ref', project_ref
            ], capture_output=True, text=True)

            if link_result.returncode == 0:
                print("✅ Project linked successfully")
            else:
                print(f"⚠️  Link warning: {link_result.stderr}")
    except Exception as e:
        print(f"⚠️  Link error: {e}")

    # Create migration file
    print("\n📝 Creating migration file...")
    migration_content = """-- Create temporary pages system tables
-- Migration for temporary pages and receipts

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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_temporary_pages_access_code ON public.temporary_pages(access_code);
CREATE INDEX IF NOT EXISTS idx_temporary_pages_expires_at ON public.temporary_pages(expires_at);
CREATE INDEX IF NOT EXISTS idx_temporary_pages_active ON public.temporary_pages(is_active);
CREATE INDEX IF NOT EXISTS idx_receipts_receipt_code ON public.receipts(receipt_code);
CREATE INDEX IF NOT EXISTS idx_receipts_active ON public.receipts(is_active);
CREATE INDEX IF NOT EXISTS idx_page_access_logs_page_id ON public.page_access_logs(page_id);
CREATE INDEX IF NOT EXISTS idx_page_access_logs_access_code ON public.page_access_logs(access_code);
CREATE INDEX IF NOT EXISTS idx_page_access_logs_accessed_at ON public.page_access_logs(accessed_at);
"""

    # Write migration file
    try:
        os.makedirs('supabase/migrations', exist_ok=True)
        with open('supabase/migrations/20240927_temporary_pages_system.sql', 'w') as f:
            f.write(migration_content)
        print("✅ Migration file created: supabase/migrations/20240927_temporary_pages_system.sql")
    except Exception as e:
        print(f"❌ Failed to create migration file: {e}")
        return False

    # Push migration
    print("\n📤 Pushing migration to Supabase...")
    try:
        push_result = subprocess.run([
            'supabase', 'db', 'push'
        ], capture_output=True, text=True, cwd='.')

        if push_result.returncode == 0:
            print("✅ Migration pushed successfully!")
            print(f"Output: {push_result.stdout}")
        else:
            print(f"❌ Push failed: {push_result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Push error: {e}")
        return False

    return True

def test_tables_after_setup():
    """Test if tables were created successfully"""

    print("\n🧪 Testing tables after setup...")

    from supabase import create_client, Client

    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing credentials for testing")
        return

    client: Client = create_client(supabase_url, supabase_key)

    tables = ['temporary_pages', 'receipts', 'page_access_logs']
    success_count = 0

    for table in tables:
        try:
            result = client.table(table).select('*').limit(1).execute()
            print(f"✅ {table}: Working")
            success_count += 1
        except Exception as e:
            print(f"❌ {table}: Failed - {e}")

    if success_count == 3:
        print(f"\n🎉 All tables created successfully!")
        return True
    else:
        print(f"\n⚠️  Only {success_count}/3 tables working")
        return False

def main():
    """Main function"""
    print("Temporary Pages System Setup with Access Token")
    print("This will use the Supabase CLI to create the required tables")
    print()

    try:
        # Setup with CLI
        setup_success = setup_with_cli_token()

        if setup_success:
            # Test the results
            test_success = test_tables_after_setup()

            if test_success:
                print("\n🎉 Setup completed successfully!")
                print("\n📋 Next steps:")
                print("1. Test the system: python3 test_temp_pages_system.py")
                print("2. The temporary pages system is now ready to use")
            else:
                print("\n❌ Setup may have partially failed")
                print("Please check your Supabase dashboard for the tables")
        else:
            print("\n❌ Setup failed")
            print("\n📋 Alternative approach:")
            print("1. Go to your Supabase dashboard")
            print("2. Use SQL Editor")
            print("3. Execute the SQL from temporary_pages_system.sql")

    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()