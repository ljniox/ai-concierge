"""
Database utilities for Supabase connection and operations
"""

from typing import Optional, Dict, Any
from src.utils.config import get_settings
import structlog

logger = structlog.get_logger()

# Global Supabase client
_supabase_client = None

def get_supabase_client():
    """Get Supabase client instance"""
    global _supabase_client

    if _supabase_client is None:
        try:
            from supabase import create_client
            settings = get_settings()

            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )

            logger.info("supabase_client_initialized")
        except Exception as e:
            logger.error("supabase_client_initialization_failed", error=str(e))
            raise

    return _supabase_client

async def test_connection() -> Dict[str, Any]:
    """Test Supabase connection"""
    try:
        client = get_supabase_client()

        # Simple test query
        result = client.table("sessions").select("count", count="exact").limit(1).execute()

        return {
            "success": True,
            "message": "Supabase connection successful",
            "count": result.count if hasattr(result, 'count') else 0
        }
    except Exception as e:
        logger.error("supabase_connection_test_failed", error=str(e))
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }

def close_supabase_client():
    """Close Supabase client connection"""
    global _supabase_client
    _supabase_client = None
    logger.info("supabase_client_closed")