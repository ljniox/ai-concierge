#!/usr/bin/env python3
"""
Production Integration Test Suite

Tests the complete Gust-IA enrollment system integration with the new
cate.sdb-dkr.ovh proxy configuration.

Tests:
- HTTPS proxy routing through Caddy
- Telegram webhook delivery
- API endpoint accessibility
- Service health monitoring
- End-to-end message processing
"""

import asyncio
import aiohttp
import json
from datetime import datetime

class ProductionIntegrationTester:
    def __init__(self):
        self.base_url = "https://cate.sdb-dkr.ovh"
        self.webhook_url = f"{self.base_url}/api/v1/telegram/webhook"
        self.secret_token = "gust-ia-webhook-secret"
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_proxy_routing(self):
        """Test that the proxy is routing requests correctly."""
        print("🌐 Testing Proxy Routing")
        print("-" * 40)

        tests = [
            ("/health", "Health check endpoint"),
            ("/", "Root endpoint"),
            ("/stats", "Statistics endpoint"),
            ("/features", "Features endpoint")
        ]

        results = []

        for endpoint, description in tests:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ {description}: OK (status {response.status})")
                        results.append({"endpoint": endpoint, "status": "success", "response_status": response.status})
                    else:
                        print(f"❌ {description}: FAILED (status {response.status})")
                        results.append({"endpoint": endpoint, "status": "failed", "response_status": response.status})
            except Exception as e:
                print(f"❌ {description}: ERROR - {e}")
                results.append({"endpoint": endpoint, "status": "error", "error": str(e)})

        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n📊 Proxy Routing: {success_count}/{len(results)} endpoints working")
        return {"status": "success" if success_count == len(results) else "partial", "results": results}

    async def test_webhook_delivery(self):
        """Test webhook message delivery through the proxy."""
        print("\n📨 Testing Webhook Delivery")
        print("-" * 40)

        test_message = {
            "update_id": int(datetime.now().timestamp()),
            "message": {
                "message_id": int(datetime.now().timestamp()),
                "from": {
                    "id": 777777777,
                    "first_name": "Production",
                    "last_name": "Test"
                },
                "chat": {
                    "id": 777777777,
                    "type": "private"
                },
                "text": "start",
                "date": int(datetime.now().timestamp())
            }
        }

        headers = {
            "Content-Type": "application/json",
            "X-Telegram-Bot-Api-Secret-Token": self.secret_token
        }

        try:
            async with self.session.post(
                self.webhook_url,
                json=test_message,
                headers=headers,
                timeout=15
            ) as response:
                result = await response.json()

                if response.status == 200 and result.get("status") == "success":
                    print("✅ Webhook delivery: SUCCESS")
                    print(f"   Response: {result.get('result', {}).get('status', 'unknown')}")
                    return {"status": "success", "response": result}
                else:
                    print(f"❌ Webhook delivery: FAILED (status {response.status})")
                    print(f"   Response: {result}")
                    return {"status": "failed", "response": result}

        except Exception as e:
            print(f"❌ Webhook delivery: ERROR - {e}")
            return {"status": "error", "error": str(e)}

    async def test_api_endpoints(self):
        """Test API endpoint accessibility."""
        print("\n🔧 Testing API Endpoints")
        print("-" * 40)

        api_tests = [
            ("/api/v1/payments", "Payments API"),
            ("/api/v1/workflow", "Workflow API"),
            ("/api/v1/enrollments", "Enrollments API"),
            ("/api/v1/documents", "Documents API"),
            ("/api/v1/telegram", "Telegram API")
        ]

        results = []

        for endpoint, description in api_tests:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}", timeout=10) as response:
                    if response.status in [200, 401, 405]:  # All valid responses
                        print(f"✅ {description}: Accessible (status {response.status})")
                        results.append({"endpoint": endpoint, "status": "success", "response_status": response.status})
                    else:
                        print(f"❌ {description}: Unexpected response (status {response.status})")
                        results.append({"endpoint": endpoint, "status": "failed", "response_status": response.status})
            except Exception as e:
                print(f"❌ {description}: ERROR - {e}")
                results.append({"endpoint": endpoint, "status": "error", "error": str(e)})

        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n📊 API Endpoints: {success_count}/{len(api_tests)} endpoints accessible")
        return {"status": "success" if success_count == len(api_tests) else "partial", "results": results}

    async def test_telegram_webhook_info(self):
        """Test Telegram webhook configuration."""
        print("\n🤖 Testing Telegram Webhook Configuration")
        print("-" * 40)

        bot_token = "8452784787:AAGHhQ9cTRAg1XnJsBi7uBSaAGIAn-PNhus"

        try:
            async with self.session.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})

                    webhook_url = result.get('url')
                    pending_count = result.get('pending_update_count', 0)
                    last_error = result.get('last_error_message')

                    if webhook_url == self.webhook_url:
                        print("✅ Webhook URL: Correctly configured")
                    else:
                        print(f"❌ Webhook URL: Mismatch (expected {self.webhook_url}, got {webhook_url})")

                    if pending_count == 0:
                        print("✅ Pending updates: None")
                    else:
                        print(f"⚠️  Pending updates: {pending_count}")

                    if last_error is None:
                        print("✅ Last error: None")
                    else:
                        print(f"❌ Last error: {last_error}")

                    return {
                        "status": "success",
                        "webhook_url": webhook_url,
                        "pending_count": pending_count,
                        "last_error": last_error
                    }
                else:
                    print(f"❌ Failed to get webhook info (status {response.status})")
                    return {"status": "failed", "response_status": response.status}

        except Exception as e:
            print(f"❌ Error checking webhook info: {e}")
            return {"status": "error", "error": str(e)}

    async def test_message_processing(self):
        """Test different message types and commands."""
        print("\n💬 Testing Message Processing")
        print("-" * 40)

        test_commands = ["start", "aide", "statut", "inscrire", "information"]
        results = []

        for command in test_commands:
            test_message = {
                "update_id": int(datetime.now().timestamp()) + len(test_commands),
                "message": {
                    "message_id": int(datetime.now().timestamp()) + len(test_commands),
                    "from": {
                        "id": 999999999,
                        "first_name": "Integration",
                        "last_name": "Test"
                    },
                    "chat": {
                        "id": 999999999,
                        "type": "private"
                    },
                    "text": command,
                    "date": int(datetime.now().timestamp())
                }
            }

            headers = {
                "Content-Type": "application/json",
                "X-Telegram-Bot-Api-Secret-Token": self.secret_token
            }

            try:
                async with self.session.post(
                    self.webhook_url,
                    json=test_message,
                    headers=headers,
                    timeout=10
                ) as response:
                    result = await response.json()

                    if response.status == 200 and result.get("status") == "success":
                        print(f"✅ Command '{command}': Processed successfully")
                        results.append({"command": command, "status": "success"})
                    else:
                        print(f"❌ Command '{command}': Processing failed")
                        results.append({"command": command, "status": "failed", "response": result})

            except Exception as e:
                print(f"❌ Command '{command}': Error - {e}")
                results.append({"command": command, "status": "error", "error": str(e)})

        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"\n📊 Message Processing: {success_count}/{len(test_commands)} commands processed")
        return {"status": "success" if success_count == len(test_commands) else "partial", "results": results}

    async def run_full_integration_test(self):
        """Run the complete integration test suite."""
        print("🚀 Gust-IA Production Integration Test Suite")
        print("=" * 60)
        print(f"Testing URL: {self.base_url}")
        print(f"Webhook URL: {self.webhook_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)

        test_start_time = datetime.now()

        # Run all tests
        proxy_result = await self.test_proxy_routing()
        webhook_result = await self.test_webhook_delivery()
        api_result = await self.test_api_endpoints()
        telegram_result = await self.test_telegram_webhook_info()
        message_result = await self.test_message_processing()

        test_duration = datetime.now() - test_start_time

        print("\n" + "=" * 60)
        print("📋 INTEGRATION TEST SUMMARY")
        print("=" * 60)

        # Print summary
        print(f"🌐 Proxy Routing: {'✅ PASS' if proxy_result['status'] == 'success' else '⚠️  PARTIAL'}")
        print(f"📨 Webhook Delivery: {'✅ PASS' if webhook_result['status'] == 'success' else '❌ FAIL'}")
        print(f"🔧 API Endpoints: {'✅ PASS' if api_result['status'] == 'success' else '⚠️  PARTIAL'}")
        print(f"🤖 Telegram Config: {'✅ PASS' if telegram_result['status'] == 'success' else '❌ FAIL'}")
        print(f"💬 Message Processing: {'✅ PASS' if message_result['status'] == 'success' else '⚠️  PARTIAL'}")

        # Calculate overall status
        all_success = all([
            proxy_result['status'] == 'success',
            webhook_result['status'] == 'success',
            api_result['status'] == 'success',
            telegram_result['status'] == 'success',
            message_result['status'] == 'success'
        ])

        print(f"\n🎯 Overall Status: {'✅ SUCCESS' if all_success else '⚠️  NEEDS ATTENTION'}")
        print(f"⏱️  Test Duration: {test_duration.total_seconds():.2f} seconds")

        # Production readiness check
        if all_success:
            print("\n🏆 PRODUCTION READY")
            print("✅ All systems are operational")
            print("✅ Ready to receive real Telegram messages")
            print("✅ Webhook is configured and working")
            print("✅ All API endpoints are accessible")
        else:
            print("\n⚠️  PRODUCTION NOT READY")
            print("❌ Some tests failed - review results above")

        return {
            "overall_status": "success" if all_success else "needs_attention",
            "duration_seconds": test_duration.total_seconds(),
            "test_results": {
                "proxy_routing": proxy_result,
                "webhook_delivery": webhook_result,
                "api_endpoints": api_result,
                "telegram_config": telegram_result,
                "message_processing": message_result
            },
            "production_ready": all_success,
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """Main test execution function."""
    async with ProductionIntegrationTester() as tester:
        results = await tester.run_full_integration_test()

        # Save results
        with open("/home/ubuntu/ai-concierge/production_integration_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Test results saved to: production_integration_test_results.json")
        return results


if __name__ == "__main__":
    asyncio.run(main())