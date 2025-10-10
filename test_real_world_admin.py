#!/usr/bin/env python3
"""
Test script to simulate the real-world admin scenario that was failing
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.interaction_service import InteractionService
from src.services.super_admin_service import SuperAdminService
import structlog

logger = structlog.get_logger()

async def test_real_world_admin():
    """Test the real-world admin scenario that was failing"""
    print("🌍 Testing Real-World Admin Scenario")
    print("=" * 45)

    try:
        interaction_service = InteractionService()
        admin_service = SuperAdminService()

        admin_phone = "221765005555"
        test_message = "Rechercher Catechumene Ethan"

        print(f"\n📱 Simulating message: '{test_message}'")
        print(f"📞 From phone: {admin_phone}")

        # Test 1: Verify admin authentication
        print("\n1. Verifying admin authentication...")
        is_admin = admin_service.is_super_admin(admin_phone)
        print(f"   Admin status: {'✅ Authenticated' if is_admin else '❌ Not authenticated'}")

        # Test 2: Test the interaction service processing (the real scenario)
        print("\n2. Testing interaction service processing...")
        print(f"   Processing message: '{test_message}'")

        try:
            result = await interaction_service.process_incoming_message(
                phone_number=admin_phone,
                message=test_message,
                message_type="text",
                message_id="test_message_123"
            )

            print(f"   ✅ Message processed successfully")

            # Check the result details
            response = result.get('response', 'No response')
            service_type = result.get('service_type', 'Unknown')

            print(f"   📝 Response: {response[:100]}...")
            print(f"   🏷️  Service Type: {service_type}")

            # Check if it's being handled as admin command vs contact humain
            if service_type == 'SUPER_ADMIN':
                print("   ✅ Correctly routed to Super Admin service")
            elif service_type == 'CONTACT_HUMAIN':
                print("   ❌ Incorrectly routed to Contact Humain (this was the original problem)")
            else:
                print(f"   ⚠️  Routed to unexpected service: {service_type}")

            # Check processing metadata
            metadata = result.get('processing_metadata', {})
            if metadata.get('admin_action'):
                print("   ✅ Recognized as admin action")
            elif metadata.get('profile_action'):
                print("   ⚠️  Handled as profile action instead of admin action")
            else:
                print("   ℹ️  No specific action metadata found")

        except Exception as e:
            print(f"   ❌ Processing failed: {str(e)}")
            logger.error("message_processing_failed", error=str(e))
            return False

        # Test 3: Test various admin commands
        print("\n3. Testing various admin commands...")
        admin_commands = [
            "rechercher catechumene Test",
            "lister classes",
            "lister admins",
            "categories",
            "aide"
        ]

        for command in admin_commands:
            print(f"\n   Testing: '{command}'")
            try:
                result = await interaction_service.process_incoming_message(
                    phone_number=admin_phone,
                    message=command,
                    message_type="text",
                    message_id=f"test_{command.replace(' ', '_')}"
                )

                service_type = result.get('service_type', 'Unknown')
                if service_type == 'SUPER_ADMIN':
                    print(f"   ✅ Correctly routed to Super Admin")
                else:
                    print(f"   ❌ Routed to {service_type} instead of Super Admin")

            except Exception as e:
                print(f"   ❌ Failed: {str(e)}")

        print("\n🎉 Real-world admin scenario testing completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        logger.error("real_world_admin_test_failed", error=str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_real_world_admin())
    sys.exit(0 if success else 1)