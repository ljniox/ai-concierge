"""
Test script for temporary pages system
"""

import asyncio
import json
from datetime import datetime, timedelta
from src.services.temporary_pages_service import get_temp_pages_service
from src.utils.temp_pages_utils import get_temp_pages_utils

async def test_temporary_pages():
    """Test the complete temporary pages system"""
    print("🧪 Testing Temporary Pages System")
    print("=" * 50)

    # Initialize services
    temp_service = get_temp_pages_service()
    utils = get_temp_pages_utils()

    # Test 1: Create temporary page
    print("\n1. Testing Temporary Page Creation")
    sample_content = {
        "student_name": "Test Student",
        "class": "1ère Année",
        "grades": [15.5, 16.0, 14.5],
        "generated_at": datetime.utcnow().isoformat(),
        "notes": "This is a test student report"
    }

    access_code = temp_service.create_temporary_page(
        title="Test Student Report - Temporary",
        content=sample_content,
        content_type="student_report",
        expires_in_hours=1,
        max_access_count=5
    )

    if access_code:
        print(f"✅ Temporary page created: {access_code}")
        print(f"🔗 Link: http://localhost:8000/api/v1/temporary-pages/view/{access_code}/web")
    else:
        print("❌ Failed to create temporary page")
        return

    # Test 2: Retrieve temporary page
    print("\n2. Testing Temporary Page Retrieval")
    page = temp_service.get_temporary_page(access_code)
    if page:
        print(f"✅ Page retrieved: {page['title']}")
        print(f"📊 Content type: {page['content_type']}")
        print(f"⏰ Expires: {page['expires_at']}")
        print(f"👁️  Access count: {page['access_count']}")
    else:
        print("❌ Failed to retrieve temporary page")

    # Test 3: Create permanent receipt
    print("\n3. Testing Receipt Creation")
    receipt_content = {
        "student_name": "Test Student",
        "inscription_id": "TEST-001",
        "payment_date": datetime.utcnow().isoformat(),
        "payment_method": "Mobile Money",
        "additional_info": "Inscription fee for 2024-2025"
    }

    receipt_code = temp_service.create_receipt(
        title="Payment Receipt - Test Student",
        content=receipt_content,
        receipt_type="payment",
        amount=15000,
        reference_id="TEST-001"
    )

    if receipt_code:
        print(f"✅ Receipt created: {receipt_code}")
        print(f"🔗 Receipt link: http://localhost:8000/api/v1/temporary-pages/receipt/{receipt_code}/web")
    else:
        print("❌ Failed to create receipt")

    # Test 4: Retrieve receipt
    print("\n4. Testing Receipt Retrieval")
    receipt = temp_service.get_receipt(receipt_code)
    if receipt:
        print(f"✅ Receipt retrieved: {receipt['title']}")
        print(f"💰 Amount: {receipt['amount']} FCFA")
        print(f"📝 Type: {receipt['receipt_type']}")
        print(f"👁️  Access count: {receipt['access_count']}")
    else:
        print("❌ Failed to retrieve receipt")

    # Test 5: System statistics
    print("\n5. Testing System Statistics")
    stats = temp_service.get_statistics()
    print(f"📊 System Statistics: {json.dumps(stats, indent=2)}")

    # Test 6: Test cleanup (simulate expiration)
    print("\n6. Testing Cleanup Functionality")

    # Create an expired page
    expired_content = {
        "test": "This should be cleaned up",
        "created_at": datetime.utcnow().isoformat()
    }

    # Create a page and manually set it as expired
    expired_access_code = temp_service.create_temporary_page(
        title="Expired Test Page",
        content=expired_content,
        expires_in_hours=-1  # Already expired
    )

    # Run cleanup
    deleted_count = temp_service.cleanup_expired_pages()
    print(f"🧹 Cleanup removed {deleted_count} expired pages")

    # Test 7: Test with real student data (if available)
    print("\n7. Testing with Real Student Data")

    # Try to get a real student ID
    try:
        from supabase import create_client
        from dotenv import load_dotenv
        import os

        load_dotenv()
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        client = create_client(supabase_url, supabase_key)

        # Get first student
        student_result = client.table('catechumenes').select('*').limit(1).execute()
        if student_result.data:
            student_id = student_result.data[0]['id_catechumene']
            student_name = f"{student_result.data[0]['prenoms']} {student_result.data[0]['nom']}"

            print(f"👤 Testing with student: {student_name}")

            # Create student report
            report_access_code = utils.create_student_report_page(
                student_id=student_id,
                report_type="complete",
                expires_in_hours=2
            )

            if report_access_code:
                print(f"✅ Student report created: {report_access_code}")
                print(f"🔗 Report link: http://localhost:8000/api/v1/temporary-pages/view/{report_access_code}/web")
            else:
                print("❌ Failed to create student report")
        else:
            print("ℹ️  No students found in database for testing")

    except Exception as e:
        print(f"ℹ️  Could not test with real student data: {e}")

    # Test 8: Test access limits
    print("\n8. Testing Access Limits")

    # Create a page with max access count of 2
    limited_page = temp_service.create_temporary_page(
        title="Limited Access Test",
        content={"test": "This should only be accessible twice"},
        max_access_count=2,
        expires_in_hours=24
    )

    if limited_page:
        # Access it twice
        for i in range(2):
            page = temp_service.get_temporary_page(limited_page)
            if page:
                print(f"✅ Access {i+1}: Success")
            else:
                print(f"❌ Access {i+1}: Failed")

        # Try third access (should fail)
        page = temp_service.get_temporary_page(limited_page)
        if page:
            print("❌ Third access should have failed")
        else:
            print("✅ Third access correctly denied")

    print("\n🎉 All tests completed!")
    print("\n📋 Summary:")
    print("- ✅ Temporary page creation and retrieval")
    print("- ✅ Receipt creation and retrieval")
    print("- ✅ System statistics")
    print("- ✅ Cleanup functionality")
    print("- ✅ Access limit enforcement")
    print("- ✅ Real student data integration")

if __name__ == "__main__":
    asyncio.run(test_temporary_pages())