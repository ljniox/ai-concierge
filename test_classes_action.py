#!/usr/bin/env python3
"""
Test script specifically for classes action
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.profile_service import ProfileService
import structlog

logger = structlog.get_logger()

async def test_classes_action():
    """Test classes action specifically"""
    print("🧪 Testing Classes Action")
    print("=" * 30)

    try:
        profile_service = ProfileService()

        # Get parent profile
        parent_profile = await profile_service.get_profile_by_phone("221765055550")

        if not parent_profile:
            print("❌ Parent profile not found")
            return False

        print(f"✅ Parent profile: {parent_profile.get('profile_name')}")

        # Test classes action with detailed logging
        result = await profile_service.execute_action(
            profile=parent_profile,
            action_id="list_classes",
            parameters={}
        )

        print(f"\nResult: {result}")

        return True

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error("classes_action_test_failed", error=str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_classes_action())
    sys.exit(0 if success else 1)