#!/usr/bin/env python3
"""
Script to load profiles and actions configuration into the database
"""

import asyncio
import sys
import os
from src.services.profile_service import ProfileService

async def main():
    """Main function to load configuration"""
    if len(sys.argv) != 2:
        print("Usage: python load_profiles_config.py <config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    if not os.path.exists(config_file):
        print(f"Error: Configuration file '{config_file}' not found")
        sys.exit(1)

    try:
        # Initialize profile service
        profile_service = ProfileService()

        # Load configuration
        success = await profile_service.load_actions_from_config(config_file)

        if success:
            print(f"✅ Configuration loaded successfully from '{config_file}'")
        else:
            print(f"❌ Failed to load configuration from '{config_file}'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())