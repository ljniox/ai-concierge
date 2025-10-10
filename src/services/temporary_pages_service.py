"""
Temporary Pages Service
For managing UUID-based temporary access pages and permanent receipts
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

class TemporaryPagesService:
    """Service for managing temporary pages and receipts"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def create_temporary_page(
        self,
        title: str,
        content: Dict[str, Any],
        content_type: str = "report",
        created_by: str = "system",
        expires_in_hours: int = 24,
        max_access_count: Optional[int] = None,
        allowed_actions: List[str] = None
    ) -> Optional[str]:
        """Create a temporary page with UUID access code"""
        try:
            if allowed_actions is None:
                allowed_actions = ["read", "print"]

            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)

            page_data = {
                "title": title,
                "content": content,
                "content_type": content_type,
                "created_by": created_by,
                "expires_at": expires_at.isoformat(),
                "max_access_count": max_access_count,
                "allowed_actions": allowed_actions
            }

            result = self.client.table("temporary_pages").insert(page_data).execute()

            if result.data:
                return result.data[0]["access_code"]
            return None

        except Exception as e:
            print(f"❌ Error creating temporary page: {e}")
            return None

    def get_temporary_page(self, access_code: str) -> Optional[Dict[str, Any]]:
        """Get temporary page by access code"""
        try:
            # Check if page exists and is valid
            result = (self.client.table("temporary_pages")
                      .select("*")
                      .eq("access_code", access_code)
                      .eq("is_active", True)
                      .execute())

            if not result.data:
                return None

            page = result.data[0]

            # Check expiration
            expires_at = datetime.fromisoformat(page["expires_at"].replace('Z', '+00:00'))
            if datetime.utcnow().replace(tzinfo=None) > expires_at.replace(tzinfo=None):
                return None

            # Check access count
            if page["max_access_count"] and page["access_count"] >= page["max_access_count"]:
                return None

            # Increment access count
            self.client.table("temporary_pages").update(
                {"access_count": page["access_count"] + 1}
            ).eq("access_code", access_code).execute()

            # Log access
            self._log_access(page["id"], "temporary", access_code, "view")

            return page

        except Exception as e:
            print(f"❌ Error getting temporary page: {e}")
            return None

    def create_receipt(
        self,
        title: str,
        content: Dict[str, Any],
        receipt_type: str = "payment",
        reference_id: Optional[str] = None,
        amount: float = 0.0,
        created_by: str = "system"
    ) -> Optional[str]:
        """Create a permanent receipt with UUID code"""
        try:
            receipt_data = {
                "title": title,
                "content": content,
                "receipt_type": receipt_type,
                "reference_id": reference_id,
                "amount": amount,
                "created_by": created_by
            }

            result = self.client.table("receipts").insert(receipt_data).execute()

            if result.data:
                return result.data[0]["receipt_code"]
            return None

        except Exception as e:
            print(f"❌ Error creating receipt: {e}")
            return None

    def get_receipt(self, receipt_code: str) -> Optional[Dict[str, Any]]:
        """Get receipt by code"""
        try:
            result = (self.client.table("receipts")
                      .select("*")
                      .eq("receipt_code", receipt_code)
                      .eq("is_active", True)
                      .execute())

            if not result.data:
                return None

            receipt = result.data[0]

            # Increment access count
            self.client.table("receipts").update(
                {"access_count": receipt["access_count"] + 1}
            ).eq("receipt_code", receipt_code).execute()

            # Log access
            self._log_access(receipt["id"], "receipt", receipt_code, "view")

            return receipt

        except Exception as e:
            print(f"❌ Error getting receipt: {e}")
            return None

    def cleanup_expired_pages(self) -> int:
        """Clean up expired temporary pages"""
        try:
            now = datetime.utcnow().isoformat()

            result = (self.client.table("temporary_pages")
                      .delete()
                      .lt("expires_at", now)
                      .execute())

            return len(result.data) if result.data else 0

        except Exception as e:
            print(f"❌ Error cleaning up expired pages: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            now = datetime.utcnow().isoformat()

            # Count active temporary pages
            active_temp = (self.client.table("temporary_pages")
                          .select("*", count="exact")
                          .eq("is_active", True)
                          .gt("expires_at", now)
                          .execute())

            # Count expired pages
            expired_temp = (self.client.table("temporary_pages")
                           .select("*", count="exact")
                           .or_(f"is_active.eq.False,expires_at.lt.{now}")
                           .execute())

            # Count receipts
            receipts = (self.client.table("receipts")
                       .select("*", count="exact")
                       .eq("is_active", True)
                       .execute())

            # Count access logs
            logs = (self.client.table("page_access_logs")
                   .select("*", count="exact")
                   .execute())

            return {
                "active_temporary_pages": active_temp.count if hasattr(active_temp, 'count') else 0,
                "expired_temporary_pages": expired_temp.count if hasattr(expired_temp, 'count') else 0,
                "total_receipts": receipts.count if hasattr(receipts, 'count') else 0,
                "total_access_logs": logs.count if hasattr(logs, 'count') else 0
            }

        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return {}

    def _log_access(self, page_id: str, page_type: str, access_code: str, action: str = "view") -> None:
        """Log page access (private method)"""
        try:
            log_data = {
                "page_id": page_id,
                "page_type": page_type,
                "access_code": access_code,
                "action": action,
                "success": True
            }

            self.client.table("page_access_logs").insert(log_data).execute()

        except Exception as e:
            print(f"⚠️  Failed to log access: {e}")

    def deactivate_page(self, access_code: str) -> bool:
        """Deactivate a temporary page"""
        try:
            result = (self.client.table("temporary_pages")
                      .update({"is_active": False})
                      .eq("access_code", access_code)
                      .execute())

            return bool(result.data)

        except Exception as e:
            print(f"❌ Error deactivating page: {e}")
            return False

    def get_page_access_logs(self, page_id: str) -> List[Dict[str, Any]]:
        """Get access logs for a specific page"""
        try:
            result = (self.client.table("page_access_logs")
                      .select("*")
                      .eq("page_id", page_id)
                      .order("accessed_at", desc=True)
                      .execute())

            return result.data if result.data else []

        except Exception as e:
            print(f"❌ Error getting access logs: {e}")
            return []

# Convenience functions
def get_temp_pages_service():
    """Get temporary pages service instance"""
    return TemporaryPagesService()

def create_shareable_link(access_code: str, base_url: str = None) -> str:
    """Create a shareable link for a temporary page"""
    if base_url is None:
        base_url = "http://localhost:8000"

    return f"{base_url}/view/{access_code}"

def create_receipt_link(receipt_code: str, base_url: str = None) -> str:
    """Create a shareable link for a receipt"""
    if base_url is None:
        base_url = "http://localhost:8000"

    return f"{base_url}/receipt/{receipt_code}"

if __name__ == "__main__":
    # Test the service
    print("🧪 Testing Temporary Pages Service...")

    service = get_temp_pages_service()

    # Test creating a temporary page
    sample_content = {
        "student_name": "Test Student",
        "class": "Test Class",
        "grades": [15.5, 16.0, 14.5],
        "generated_at": datetime.utcnow().isoformat()
    }

    access_code = service.create_temporary_page(
        title="Test Student Report",
        content=sample_content,
        content_type="student_report",
        expires_in_hours=1
    )

    if access_code:
        print(f"✅ Created temporary page: {access_code}")
        print(f"🔗 Shareable link: {create_shareable_link(access_code)}")

        # Test retrieving the page
        page = service.get_temporary_page(access_code)
        if page:
            print(f"✅ Successfully retrieved page: {page['title']}")
        else:
            print("❌ Failed to retrieve page")

    # Test creating a receipt
    receipt_content = {
        "student_name": "Test Student",
        "inscription_id": "TEST-001",
        "amount": 15000,
        "payment_date": datetime.utcnow().isoformat(),
        "payment_method": "Cash"
    }

    receipt_code = service.create_receipt(
        title="Payment Receipt - Test Student",
        content=receipt_content,
        receipt_type="payment",
        amount=15000,
        reference_id="TEST-001"
    )

    if receipt_code:
        print(f"✅ Created receipt: {receipt_code}")
        print(f"🔗 Receipt link: {create_receipt_link(receipt_code)}")

        # Test retrieving the receipt
        receipt = service.get_receipt(receipt_code)
        if receipt:
            print(f"✅ Successfully retrieved receipt: {receipt['title']}")
        else:
            print("❌ Failed to retrieve receipt")

    # Get statistics
    stats = service.get_statistics()
    print(f"📊 System statistics: {stats}")

    print("\n✅ Testing completed!")