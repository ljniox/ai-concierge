#!/usr/bin/env python3
"""
Test script to audit admin flow and submenu access
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.super_admin_service import SuperAdminService
from src.services.profile_service import ProfileService
from src.services.interaction_service import InteractionService
import structlog

logger = structlog.get_logger()

async def test_admin_flow():
    """Audit admin flow and submenu access"""
    print("🔍 Auditing Admin Flow and Submenu Access")
    print("=" * 50)

    try:
        # Initialize services
        admin_service = SuperAdminService()
        profile_service = ProfileService()
        interaction_service = InteractionService()

        admin_phone = "221765005555"

        # 1. Test admin authentication
        print("\n1. Testing admin authentication...")
        is_admin = admin_service.is_super_admin(admin_phone)
        print(f"   Admin status for {admin_phone}: {'✅ Authenticated' if is_admin else '❌ Not authenticated'}")

        # Get admin profile
        admin_profile = await profile_service.get_profile_by_phone(admin_phone)
        if admin_profile:
            print(f"   Admin profile: {admin_profile.get('profile_name')}")
            print(f"   Permissions: {admin_profile.get('permissions', [])}")
        else:
            print("   ❌ Admin profile not found")
            return False

        # 2. Test admin command access
        print("\n2. Testing admin command access...")

        # Test admin help command
        help_result = await admin_service.parse_admin_command("aide")
        print(f"   Admin help command: {'✅ Success' if help_result.get('success') else '❌ Failed'}")

        if help_result.get('success'):
            print("   ✅ Admin can access help system")
        else:
            print(f"   ❌ Admin help failed: {help_result.get('message')}")

        # 3. Test management submenu commands
        print("\n3. Testing management submenu access...")

        management_commands = [
            ("lister admins", "List admin users"),
            ("categories", "View categories"),
            ("lister renseignements", "List renseignements"),
        ]

        for command, description in management_commands:
            result = await admin_service.parse_admin_command(command)
            status = "✅ Success" if result.get('success') else "❌ Failed"
            print(f"   {description}: {status}")
            if not result.get('success'):
                print(f"      Error: {result.get('message')}")

        # 4. Test catechese submenu commands
        print("\n4. Testing catechese submenu access...")

        catechese_commands = [
            ("rechercher catechumene test", "Search catechumene"),
            ("lister classes", "List classes"),
            ("voir parent", "View parent info"),
        ]

        for command, description in catechese_commands:
            result = await admin_service.parse_admin_command(command)
            status = "✅ Success" if result.get('success') else "❌ Failed"
            print(f"   {description}: {status}")
            if not result.get('success'):
                print(f"      Error: {result.get('message')}")

        # 5. Test catechese requests (renseignements) submenu commands
        print("\n5. Testing catechese requests (renseignements) submenu access...")

        # Check if we can access renseignements
        categories_result = await admin_service.get_categories()
        print(f"   Access categories: {'✅ Success' if categories_result.get('success') else '❌ Failed'}")

        if categories_result.get('success'):
            categories = categories_result.get('categories', [])
            print(f"   Found {len(categories)} categories")

        # Test listing renseignements
        list_result = await admin_service.parse_admin_command("lister renseignements")
        print(f"   List renseignements: {'✅ Success' if list_result.get('success') else '❌ Failed'}")

        # 6. Test service menu sending
        print("\n6. Testing service menu access...")
        try:
            menu_result = await interaction_service.send_service_menu(admin_phone)
            print(f"   Service menu: {'✅ Success' if menu_result.get('success') else '❌ Failed'}")

            if menu_result.get('success'):
                print("   ✅ Admin can receive service menu")
            else:
                print(f"   ❌ Service menu failed: {menu_result.get('error')}")
        except Exception as e:
            print(f"   ❌ Service menu exception: {str(e)}")

        # 7. Test admin profile-based actions
        print("\n7. Testing admin profile-based actions...")

        admin_actions = [
            {"action_id": "search_catechumene", "params": {"search_term": "test"}, "description": "Search catechumene"},
            {"action_id": "list_classes", "params": {}, "description": "List classes"},
            {"action_id": "view_parent_info", "params": {"parent_code": "PARENT001"}, "description": "View parent info"},
        ]

        for action in admin_actions:
            try:
                result = await profile_service.execute_action(
                    profile=admin_profile,
                    action_id=action["action_id"],
                    parameters=action["params"]
                )
                status = "✅ Success" if result.get("success") else "❌ Failed"
                print(f"   {action['description']}: {status}")
                if not result.get("success"):
                    print(f"      Error: {result.get('error')}")
            except Exception as e:
                print(f"   {action['description']}: ❌ Exception: {str(e)}")

        print("\n🎉 Admin flow audit completed!")
        return True

    except Exception as e:
        print(f"❌ Admin audit failed with error: {str(e)}")
        logger.error("admin_audit_failed", error=str(e))
        return False

if __name__ == "__main__":
    success = asyncio.run(test_admin_flow())
    sys.exit(0 if success else 1)