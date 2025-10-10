#!/usr/bin/env python3
"""
Test script to verify admin catechumene search functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.super_admin_service import SuperAdminService
import structlog

logger = structlog.get_logger()

async def test_admin_search():
    """Test admin catechumene search functionality"""
    print("🧪 Testing Admin Catechumene Search")
    print("=" * 40)

    try:
        admin_service = SuperAdminService()
        admin_phone = "221765005555"

        # Test 1: Verify admin authentication
        print("\n1. Testing admin authentication...")
        is_admin = admin_service.is_super_admin(admin_phone)
        print(f"   Admin status: {'✅ Authenticated' if is_admin else '❌ Not authenticated'}")

        if not is_admin:
            print("❌ Cannot proceed - not authenticated as admin")
            return False

        # Test 2: Test admin catechumene search
        print("\n2. Testing admin catechumene search...")
        search_commands = [
            "rechercher catechumene Ethan",
            "rechercher catechumene Test",
            "rechercher catechumene Smith",
        ]

        for command in search_commands:
            print(f"\n   Testing: {command}")
            try:
                result = await admin_service.parse_admin_command(command)
                if result.get('success'):
                    print(f"   ✅ Success: {result.get('message', 'Command executed successfully')}")
                else:
                    print(f"   ❌ Failed: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")

        # Test 3: Test search with no results
        print("\n3. Testing search with non-existent name...")
        result = await admin_service.parse_admin_command("rechercher catechumene NonExistentName123")
        if result.get('success'):
            print("   ✅ Success: Handled non-existent search gracefully")
        else:
            print(f"   ❌ Failed: {result.get('message')}")

        print("\n🎉 Admin catechumene search testing completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        logger.error("admin_search_test_failed", error=str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_admin_search())
    sys.exit(0 if success else 1)