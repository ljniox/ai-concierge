"""
Supabase Configuration for SDB
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

class SupabaseConfig:
    """Supabase configuration and client management"""
    
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.client = None
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
    
    def get_client(self) -> Client:
        """Get Supabase client instance"""
        if self.client is None:
            self.client = create_client(self.url, self.key)
        return self.client
    
    def get_anon_client(self) -> Client:
        """Get Supabase client with anon key for read operations"""
        return create_client(self.url, self.anon_key)

# Global instance
supabase_config = SupabaseConfig()

def get_supabase_client() -> Client:
    """Get Supabase client for write operations"""
    return supabase_config.get_client()

def get_supabase_anon_client() -> Client:
    """Get Supabase client for read operations"""
    return supabase_config.get_anon_client()

# Quick test functions
def test_connection():
    """Test Supabase connection"""
    try:
        client = get_supabase_client()
        result = client.table('catechumenes').select('count').limit(1).execute()
        print("✅ Supabase connection successful")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()