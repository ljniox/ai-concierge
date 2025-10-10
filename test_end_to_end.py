#!/usr/bin/env python3
"""
Test script for end-to-end catechumen search functionality
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.interaction_service import InteractionService
from services.profile_service import ProfileService
from services.claude_service import ClaudeService
from services.supabase_service import SupabaseService

async def test_end_to_end_search():
    """Test complete end-to-end catechumen search"""
    print("🧪 Testing End-to-End Catechumen Search")
    print("=" * 50)

    # Initialize services
    interaction_service = InteractionService()

    # Test data
    test_phone = "22177123456"
    test_message = "Bonjour, je cherche des informations sur un catéchumène"

    print(f"📞 Phone: {test_phone}")
    print(f"💬 Message: {test_message}")
    print()

    # Test the complete flow
    try:
        print("🚀 Processing message through InteractionService...")
        result = await interaction_service.process_incoming_message(
            message=test_message,
            phone_number=test_phone,
            message_type="text"
        )

        print("✅ Message processed successfully!")
        print(f"📝 Result: {result}")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 50)
    print("🎯 End-to-End Test Complete")
    return True

if __name__ == "__main__":
    asyncio.run(test_end_to_end_search())