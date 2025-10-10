#!/usr/bin/env python3
"""
Test script for parent access rights functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.profile_service import ProfileService
import structlog

logger = structlog.get_logger()

async def test_parent_access():
    """Test parent access rights functionality"""
    print("🧪 Testing Parent Access Rights")
    print("=" * 50)

    try:
        # Initialize services
        profile_service = ProfileService()

        # Test parent profile loading
        print("\n1. Testing parent profile loading...")
        parent_profile = await profile_service.get_profile_by_phone("221765055550")

        if parent_profile:
            print(f"✅ Parent profile found: {parent_profile.get('profile_name', 'N/A')}")
            print(f"   Phone: {parent_profile.get('phone_number', 'N/A')}")
            print(f"   Permissions: {parent_profile.get('permissions', [])}")
            print(f"   Parent Code: {parent_profile.get('parent_code', 'N/A')}")
        else:
            print("❌ Parent profile not found")
            return False

        # Test action execution
        print("\n2. Testing action execution...")
        test_actions = [
            {
                "action_id": "view_parent_info",
                "params": {"parent_code": "PARENT001"},
                "description": "View parent information"
            },
            {
                "action_id": "list_classes",
                "params": {},
                "description": "List available classes"
            }
        ]

        for action_data in test_actions:
            print(f"\n   Testing: {action_data['description']}")

            try:
                result = await profile_service.execute_action(
                    profile=parent_profile,
                    action_id=action_data["action_id"],
                    parameters=action_data["params"]
                )

                if result.get("success"):
                    print(f"   ✅ Success: {result.get('message', 'Action completed')}")
                else:
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"   ❌ Exception: {str(e)}")
                logger.error("action_execution_failed", action_id=action_data["action_id"], error=str(e))

        print("\n🎉 Parent access rights testing completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        logger.error("parent_access_test_failed", error=str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_parent_access())
    sys.exit(0 if success else 1)