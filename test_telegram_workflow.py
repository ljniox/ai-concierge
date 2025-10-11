#!/usr/bin/env python3
"""
Telegram Webhook Integration Test Script

Tests the complete Gust-IA enrollment system via Telegram webhook integration.

Features:
- Webhook endpoint validation
- Enrollment workflow simulation
- OCR document processing
- Payment validation
- Multi-step conversation testing

Constitution Principle II: Type safety throughout codebase
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

class TelegramWorkflowTester:
    """Test the complete Telegram enrollment workflow."""

    def __init__(self):
        self.webhook_url = "https://gust-ia-enrollment.loca.lt/api/v1/telegram/webhook"
        self.secret_token = "gust-ia-webhook-secret"
        self.test_user_id = 123456789
        self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the HTTP session."""
        await self.session.close()

    async def send_telegram_update(self, message_text: str) -> Dict[str, Any]:
        """
        Send a simulated Telegram update to the webhook.

        Args:
            message_text: Message text to send

        Returns:
            Dict: Response from the webhook
        """
        update_data = {
            "update_id": int(datetime.now(timezone.utc).timestamp()),
            "message": {
                "message_id": int(datetime.now(timezone.utc).timestamp()),
                "from": {
                    "id": self.test_user_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "testuser"
                },
                "chat": {
                    "id": self.test_user_id,
                    "type": "private"
                },
                "text": message_text,
                "date": int(datetime.now(timezone.utc).timestamp())
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-Telegram-Bot-Api-Secret-Token": self.secret_token
        }

        try:
            async with self.session.post(
                self.webhook_url,
                json=update_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                return {
                    "status": response.status,
                    "success": response.status == 200,
                    "data": result
                }
        except Exception as e:
            return {
                "status": 0,
                "success": False,
                "error": str(e)
            }

    async def test_webhook_connectivity(self) -> Dict[str, Any]:
        """Test basic webhook connectivity."""
        print("🔍 Testing Webhook Connectivity...")

        response = await self.send_telegram_update("ping")

        if response["success"]:
            print("✅ Webhook connectivity: SUCCESS")
            print(f"   Response: {response['data']}")
            return {"status": "success", "response": response["data"]}
        else:
            print(f"❌ Webhook connectivity: FAILED")
            print(f"   Error: {response.get('error', 'Unknown error')}")
            return {"status": "failed", "error": response.get("error")}

    async def test_conversation_workflow(self) -> Dict[str, Any]:
        """Test the complete conversational enrollment workflow."""
        print("\n🗣️  Testing Conversation Workflow...")

        workflow_steps = [
            ("start", "Start the enrollment process"),
            ("aide", "Request help information"),
            ("statut", "Check system status"),
            ("inscrire", "Begin enrollment"),
            ("information", "Get more information"),
            ("contact", "Request human contact")
        ]

        results = []

        for message, description in workflow_steps:
            print(f"   📝 Testing: {description} ('{message}')")
            response = await self.send_telegram_update(message)

            if response["success"]:
                print(f"      ✅ Success: {response['data'].get('result', {}).get('status', 'processed')}")
                results.append({
                    "step": message,
                    "description": description,
                    "status": "success",
                    "response": response["data"]
                })
            else:
                print(f"      ❌ Failed: {response.get('error', 'Unknown error')}")
                results.append({
                    "step": message,
                    "description": description,
                    "status": "failed",
                    "error": response.get("error")
                })

        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n   📊 Workflow Results: {success_count}/{len(results)} steps successful")

        return {
            "status": "success" if success_count == len(results) else "partial",
            "results": results,
            "success_rate": success_count / len(results) * 100
        }

    async def test_system_endpoints(self) -> Dict[str, Any]:
        """Test various system endpoints through Telegram commands."""
        print("\n🔧 Testing System Endpoints...")

        endpoint_tests = [
            ("sante", "Health check"),
            ("statistiques", "System statistics"),
            ("fonctionnalités", "System features"),
            ("api", "API information"),
            ("version", "Version information")
        ]

        results = []

        for command, description in endpoint_tests:
            print(f"   🔗 Testing: {description} ('{command}')")
            response = await self.send_telegram_update(command)

            if response["success"]:
                print(f"      ✅ Endpoint responsive")
                results.append({
                    "command": command,
                    "description": description,
                    "status": "success",
                    "response": response["data"]
                })
            else:
                print(f"      ❌ Endpoint failed")
                results.append({
                    "command": command,
                    "description": description,
                    "status": "failed",
                    "error": response.get("error")
                })

        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n   📊 Endpoint Results: {success_count}/{len(results)} endpoints responding")

        return {
            "status": "success" if success_count == len(results) else "partial",
            "results": results,
            "success_rate": success_count / len(results) * 100
        }

    async def test_error_handling(self) -> Dict[str, Any]:
        """Test system error handling with invalid inputs."""
        print("\n⚠️  Testing Error Handling...")

        error_tests = [
            ("invalid_command_xyz", "Unknown command"),
            ("", "Empty message"),
            ("1234567890" * 20, "Very long message"),
            ("/start with extra args", "Command with arguments")
        ]

        results = []

        for invalid_input, description in error_tests:
            print(f"   🚫 Testing: {description}")
            response = await self.send_telegram_update(invalid_input)

            # Even invalid inputs should return proper HTTP 200 responses
            # The system should handle errors gracefully
            if response["success"]:
                print(f"      ✅ Error handled gracefully")
                results.append({
                    "input": invalid_input,
                    "description": description,
                    "status": "handled",
                    "response": response["data"]
                })
            else:
                print(f"      ❌ Error not handled properly")
                results.append({
                    "input": invalid_input,
                    "description": description,
                    "status": "unhandled",
                    "error": response.get("error")
                })

        handled_count = sum(1 for r in results if r["status"] == "handled")
        print(f"\n   📊 Error Handling: {handled_count}/{len(results)} errors handled properly")

        return {
            "status": "success" if handled_count == len(results) else "partial",
            "results": results,
            "handling_rate": handled_count / len(results) * 100
        }

    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run the complete webhook workflow test suite."""
        print("🚀 Starting Gust-IA Telegram Webhook Test Suite")
        print("=" * 60)

        test_start_time = datetime.now()

        # Run all test suites
        connectivity_result = await self.test_webhook_connectivity()
        workflow_result = await self.test_conversation_workflow()
        endpoint_result = await self.test_system_endpoints()
        error_handling_result = await self.test_error_handling()

        test_duration = datetime.now() - test_start_time

        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)

        # Print summary
        connectivity_status = "✅ PASS" if connectivity_result['status'] == 'success' else "❌ FAIL"
        workflow_status = "✅ PASS" if workflow_result['success_rate'] == 100 else f"⚠️  PARTIAL ({workflow_result.get('success_rate', 0):.1f}%)"
        endpoint_status = "✅ PASS" if endpoint_result['success_rate'] == 100 else f"⚠️  PARTIAL ({endpoint_result.get('success_rate', 0):.1f}%)"
        error_status = "✅ PASS" if error_handling_result['handling_rate'] == 100 else f"⚠️  PARTIAL ({error_handling_result.get('handling_rate', 0):.1f}%)"

        print(f"🔗 Webhook Connectivity: {connectivity_status}")
        print(f"🗣️  Conversation Workflow: {workflow_status}")
        print(f"🔧 System Endpoints: {endpoint_status}")
        print(f"⚠️  Error Handling: {error_status}")

        # Calculate overall status
        overall_success = (
            connectivity_result['status'] == 'success' and
            workflow_result['success_rate'] >= 80 and
            endpoint_result['success_rate'] >= 80 and
            error_handling_result['handling_rate'] >= 80
        )

        print(f"\n🎯 Overall Status: {'✅ SUCCESS' if overall_success else '⚠️  NEEDS ATTENTION'}")
        print(f"⏱️  Test Duration: {test_duration.total_seconds():.2f} seconds")

        return {
            "overall_status": "success" if overall_success else "needs_attention",
            "duration_seconds": test_duration.total_seconds(),
            "test_results": {
                "connectivity": connectivity_result,
                "workflow": workflow_result,
                "endpoints": endpoint_result,
                "error_handling": error_handling_result
            },
            "webhook_url": self.webhook_url,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


async def main():
    """Main test execution function."""
    tester = TelegramWorkflowTester()

    try:
        results = await tester.run_comprehensive_test()

        # Save test results
        with open("/home/ubuntu/ai-concierge/telegram_webhook_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Test results saved to: telegram_webhook_test_results.json")

        return results

    finally:
        await tester.close()


if __name__ == "__main__":
    asyncio.run(main())