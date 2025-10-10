#!/usr/bin/env python3

import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.evolution_service import EvolutionAPIService

async def test_evolution_api():
    """Test Evolution API functionality"""

    print("🧪 Testing Evolution API Integration")
    print("=" * 50)

    # Initialize service
    evolution_service = EvolutionAPIService(
        base_url="http://localhost:8080",
        api_key="429683C4C977415CAAFCCE10F7D57E11",
        instance_name="gust-ia-v2",
        instance_token="gust-ia-token-v2"
    )

    print("1. Testing instance information...")
    instance_info = await evolution_service.get_instance_info()
    print(f"   Instance Name: {instance_info.get('name')}")
    print(f"   Connection Status: {instance_info.get('connectionStatus')}")
    print(f"   Integration: {instance_info.get('integration')}")
    print(f"   Number: {instance_info.get('number')}")
    print()

    print("2. Testing connection state...")
    connection_state = await evolution_service.get_connection_state()
    print(f"   Connection State: {connection_state}")
    print()

    print("3. Testing QR code generation...")
    qr_code = await evolution_service.get_qr_code()
    if qr_code:
        print(f"   QR Code Available: Yes (length: {len(qr_code)} chars)")
    else:
        print("   QR Code Available: No or not ready")
    print()

    print("✅ Evolution API test completed successfully!")
    print(f"   Instance Status: {connection_state}")

    return True

if __name__ == "__main__":
    asyncio.run(test_evolution_api())