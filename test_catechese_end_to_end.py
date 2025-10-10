#!/usr/bin/env python3
"""
End-to-End Catechese Management System Test
Tests all service profiles with mock webhook content to assess solution readiness
"""

import asyncio
import json
import uuid
import requests
from datetime import datetime
from typing import Dict, Any, List

# Import the required services
import sys
sys.path.append('/home/ubuntu/ai-concierge')

class CatecheseSystemTest:
    """Comprehensive test suite for catechese management system"""

    def __init__(self):
        self.test_results = []
        self.mock_users = [
            {
                "phone": "+221765005555",
                "name": "Parent Test User",
                "profile": "parent",
                "code_parent": "PARENT001"
            },
            {
                "phone": "+221765005556",
                "name": "Catechist Test User",
                "profile": "catechist",
                "code_parent": "CATECHIST001"
            },
            {
                "phone": "+221765005557",
                "name": "Student Test User",
                "profile": "student",
                "code_parent": None
            },
            {
                "phone": "+221765005558",
                "name": "Admin Test User",
                "profile": "admin",
                "code_parent": None
            }
        ]

        self.test_scenarios = {
            "RENSEIGNEMENT": [
                {
                    "name": "General Information Request",
                    "message": "Bonjour, je voudrais des informations sur les horaires de catéchèse",
                    "expected_service": "RENSEIGNEMENT",
                    "expected_keywords": ["horaire", "catéchèse", "information"]
                },
                {
                    "name": "Location Information",
                    "message": "Où se trouve le centre de catéchèse le plus proche ?",
                    "expected_service": "RENSEIGNEMENT",
                    "expected_keywords": ["centre", "proche", "lieu"]
                },
                {
                    "name": "Registration Process",
                    "message": "Comment puis-je inscrire mon enfant à la catéchèse ?",
                    "expected_service": "RENSEIGNEMENT",
                    "expected_keywords": ["inscrire", "enfant", "procédure"]
                }
            ],
            "CATECHESE": [
                {
                    "name": "Catechism Content Request",
                    "message": "Pouvez-vous m'expliquer le sens de l'Eucharistie ?",
                    "expected_service": "CATECHESE",
                    "expected_keywords": ["Eucharistie", "sens", "explication"],
                    "requires_auth": True
                },
                {
                    "name": "Prayer Request",
                    "message": "J'ai besoin d'une prière pour la protection de ma famille",
                    "expected_service": "CATECHESE",
                    "expected_keywords": ["prière", "protection", "famille"]
                },
                {
                    "name": "Bible Question",
                    "message": "Que dit la Bible sur la charité ?",
                    "expected_service": "CATECHESE",
                    "expected_keywords": ["Bible", "charité", "enseignement"]
                }
            ],
            "CONTACT_HUMAIN": [
                {
                    "name": "Human Agent Request",
                    "message": "Je veux parler à un agent humain s'il vous plaît",
                    "expected_service": "CONTACT_HUMAIN",
                    "expected_keywords": ["agent", "humain", "parler"]
                },
                {
                    "name": "Emergency Request",
                    "message": "C'est urgent, j'ai besoin d'aide immédiatement",
                    "expected_service": "CONTACT_HUMAIN",
                    "expected_keywords": ["urgent", "aide", "immédiat"]
                },
                {
                    "name": "Complex Issue",
                    "message": "Mon problème est trop complexe pour un assistant, je préfère parler à quelqu'un",
                    "expected_service": "CONTACT_HUMAIN",
                    "expected_keywords": ["complexe", "quelqu'un", "parler"]
                }
            ]
        }

    def create_mock_webhook_payload(self, phone: str, message: str, message_type: str = "text") -> Dict[str, Any]:
        """Create a mock webhook payload for testing"""
        return {
            "event": "message",
            "session": "default",
            "payload": {
                "key": {
                    "remoteJid": f"{phone}@s.whatsapp.net",
                    "fromMe": False,
                    "id": f"wa_{uuid.uuid4()}",
                    "timestamp": int(datetime.now().timestamp())
                },
                "message": {
                    "conversation": message
                },
                "messageTimestamp": int(datetime.now().timestamp()),
                "from": f"{phone}@s.whatsapp.net",
                "hasMedia": False,
                "media": None
            }
        }

    def test_webhook_endpoint(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Test the webhook endpoint with mock data"""
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/webhook",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            result = response.json() if response.status_code == 200 else response.text
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def test_service_profile(self, service_type: str, scenarios: List[Dict[str, Any]], user_profile: str = None) -> Dict[str, Any]:
        """Test a specific service profile with multiple scenarios"""
        print(f"\n🧪 Testing {service_type} Service Profile")
        print("=" * 50)

        test_results = {
            "service_type": service_type,
            "user_profile": user_profile,
            "scenarios_tested": len(scenarios),
            "successful_tests": 0,
            "failed_tests": 0,
            "details": []
        }

        # Select appropriate user based on profile requirements
        if user_profile == "parent":
            test_user = self.mock_users[0]  # Parent user
        elif user_profile == "catechist":
            test_user = self.mock_users[1]  # Catechist user
        else:
            test_user = self.mock_users[2]  # Student user

        for scenario in scenarios:
            print(f"\n📝 Testing Scenario: {scenario['name']}")
            print(f"💬 Message: {scenario['message']}")

            # Check if authentication is required
            if scenario.get('requires_auth', False) and user_profile not in ['parent', 'catechist']:
                print(f"⚠️  Skipping - Authentication required for this scenario")
                continue

            # Create webhook payload
            payload = self.create_mock_webhook_payload(
                phone=test_user["phone"],
                message=scenario["message"]
            )

            # Send webhook
            webhook_result = self.test_webhook_endpoint(payload)

            # Analyze results
            scenario_result = {
                "scenario_name": scenario["name"],
                "message": scenario["message"],
                "webhook_success": webhook_result["success"],
                "response_received": webhook_result["success"],
                "response_data": webhook_result.get("response", {}),
                "expected_service": scenario["expected_service"],
                "expected_keywords": scenario["expected_keywords"],
                "user_profile": user_profile,
                "phone": test_user["phone"]
            }

            if webhook_result["success"]:
                # Check if response contains expected keywords
                response_text = str(webhook_result.get("response", {}))
                keyword_matches = [kw for kw in scenario["expected_keywords"] if kw.lower() in response_text.lower()]
                scenario_result["keyword_matches"] = keyword_matches

                if keyword_matches:
                    print(f"✅ Success - Keywords matched: {keyword_matches}")
                    test_results["successful_tests"] += 1
                else:
                    print(f"⚠️  Partial success - No keywords matched in response")
                    test_results["failed_tests"] += 1
            else:
                print(f"❌ Failed - Webhook error: {webhook_result.get('error', 'Unknown error')}")
                test_results["failed_tests"] += 1

            test_results["details"].append(scenario_result)

        print(f"\n📊 {service_type} Test Summary:")
        print(f"✅ Successful: {test_results['successful_tests']}")
        print(f"❌ Failed: {test_results['failed_tests']}")
        print(f"📈 Success Rate: {test_results['successful_tests'] / test_results['scenarios_tested'] * 100:.1f}%")

        return test_results

    def test_parent_authentication_workflow(self) -> Dict[str, Any]:
        """Test parent authentication workflow with code_parent"""
        print(f"\n🔐 Testing Parent Authentication Workflow")
        print("=" * 50)

        auth_scenarios = [
            {
                "name": "Valid Parent Code Authentication",
                "message": "Mon code parent est PARENT001, je veux accéder aux informations de mon enfant",
                "expected_behavior": "authentication_success",
                "code_parent": "PARENT001"
            },
            {
                "name": "Invalid Parent Code",
                "message": "Mon code parent est WRONG123, je veux accéder aux informations",
                "expected_behavior": "authentication_failure",
                "code_parent": "WRONG123"
            },
            {
                "name": "No Parent Code Provided",
                "message": "Je veux accéder aux informations de mon enfant",
                "expected_behavior": "code_required",
                "code_parent": None
            }
        ]

        auth_results = {
            "workflow_type": "parent_authentication",
            "scenarios_tested": len(auth_scenarios),
            "successful_tests": 0,
            "failed_tests": 0,
            "details": []
        }

        for scenario in auth_scenarios:
            print(f"\n📝 Testing Authentication Scenario: {scenario['name']}")
            print(f"💬 Message: {scenario['message']}")
            print(f"🔑 Code Parent: {scenario['code_parent']}")

            # Use parent user for authentication tests
            parent_user = self.mock_users[0]
            payload = self.create_mock_webhook_payload(
                phone=parent_user["phone"],
                message=scenario["message"]
            )

            webhook_result = self.test_webhook_endpoint(payload)

            scenario_result = {
                "scenario_name": scenario["name"],
                "message": scenario["message"],
                "code_parent": scenario["code_parent"],
                "expected_behavior": scenario["expected_behavior"],
                "webhook_success": webhook_result["success"],
                "response_data": webhook_result.get("response", {})
            }

            if webhook_result["success"]:
                response_text = str(webhook_result.get("response", {}))

                # Check response based on expected behavior
                if scenario["expected_behavior"] == "authentication_success":
                    if "succès" in response_text.lower() or "authentifié" in response_text.lower():
                        print("✅ Authentication successful detected")
                        auth_results["successful_tests"] += 1
                    else:
                        print("⚠️  Authentication success not confirmed in response")
                        auth_results["failed_tests"] += 1

                elif scenario["expected_behavior"] == "authentication_failure":
                    if "incorrect" in response_text.lower() or "erreur" in response_text.lower():
                        print("✅ Authentication failure correctly detected")
                        auth_results["successful_tests"] += 1
                    else:
                        print("⚠️  Authentication failure not properly handled")
                        auth_results["failed_tests"] += 1

                elif scenario["expected_behavior"] == "code_required":
                    if "code" in response_text.lower() and "parent" in response_text.lower():
                        print("✅ Code requirement correctly requested")
                        auth_results["successful_tests"] += 1
                    else:
                        print("⚠️  Code requirement not properly requested")
                        auth_results["failed_tests"] += 1
            else:
                print(f"❌ Webhook failed: {webhook_result.get('error', 'Unknown error')}")
                auth_results["failed_tests"] += 1

            auth_results["details"].append(scenario_result)

        print(f"\n📊 Parent Authentication Test Summary:")
        print(f"✅ Successful: {auth_results['successful_tests']}")
        print(f"❌ Failed: {auth_results['failed_tests']}")
        print(f"📈 Success Rate: {auth_results['successful_tests'] / auth_results['scenarios_tested'] * 100:.1f}%")

        return auth_results

    def test_student_data_retrieval_workflow(self) -> Dict[str, Any]:
        """Test student data retrieval workflow"""
        print(f"\n🎓 Testing Student Data Retrieval Workflow")
        print("=" * 50)

        student_scenarios = [
            {
                "name": "Student Information Request",
                "message": "Je veux voir les informations de l'élève Ndongo",
                "expected_data": "student_info",
                "student_name": "Ndongo"
            },
            {
                "name": "Grades Request",
                "message": "Montrez-moi les notes de l'élève Latyr",
                "expected_data": "grades",
                "student_name": "Latyr"
            },
            {
                "name": "Attendance Request",
                "message": "Quelles sont les présences de l'élève Emmanuel ?",
                "expected_data": "attendance",
                "student_name": "Emmanuel"
            }
        ]

        data_results = {
            "workflow_type": "student_data_retrieval",
            "scenarios_tested": len(student_scenarios),
            "successful_tests": 0,
            "failed_tests": 0,
            "details": []
        }

        for scenario in student_scenarios:
            print(f"\n📝 Testing Data Retrieval Scenario: {scenario['name']}")
            print(f"💬 Message: {scenario['message']}")
            print(f"👤 Student: {scenario['student_name']}")

            # Use authenticated parent user for data retrieval
            parent_user = self.mock_users[0]
            payload = self.create_mock_webhook_payload(
                phone=parent_user["phone"],
                message=scenario["message"]
            )

            webhook_result = self.test_webhook_endpoint(payload)

            scenario_result = {
                "scenario_name": scenario["name"],
                "message": scenario["message"],
                "student_name": scenario["student_name"],
                "expected_data": scenario["expected_data"],
                "webhook_success": webhook_result["success"],
                "response_data": webhook_result.get("response", {})
            }

            if webhook_result["success"]:
                response_text = str(webhook_result.get("response", {}))

                # Check if student name appears in response
                if scenario["student_name"].lower() in response_text.lower():
                    print(f"✅ Student '{scenario['student_name']}' found in response")
                    data_results["successful_tests"] += 1
                else:
                    print(f"⚠️  Student '{scenario['student_name']}' not found in response")
                    data_results["failed_tests"] += 1
            else:
                print(f"❌ Webhook failed: {webhook_result.get('error', 'Unknown error')}")
                data_results["failed_tests"] += 1

            data_results["details"].append(scenario_result)

        print(f"\n📊 Student Data Retrieval Test Summary:")
        print(f"✅ Successful: {data_results['successful_tests']}")
        print(f"❌ Failed: {data_results['failed_tests']}")
        print(f"📈 Success Rate: {data_results['successful_tests'] / data_results['scenarios_tested'] * 100:.1f}%")

        return data_results

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive end-to-end test of all services"""
        print("🚀 Starting Comprehensive Catechese Management System Test")
        print("=" * 70)
        print(f"📅 Test Date: {datetime.now().isoformat()}")
        print(f"🎯 Testing {len(self.test_scenarios)} service types")
        print(f"👥 Using {len(self.mock_users)} mock user profiles")

        comprehensive_results = {
            "test_start_time": datetime.now().isoformat(),
            "total_scenarios_tested": 0,
            "total_successful_tests": 0,
            "total_failed_tests": 0,
            "service_results": {},
            "workflow_results": {},
            "system_health": {}
        }

        # Test each service profile
        for service_type, scenarios in self.test_scenarios.items():
            # Test with general user
            service_result = self.test_service_profile(service_type, scenarios)
            comprehensive_results["service_results"][service_type] = service_result
            comprehensive_results["total_scenarios_tested"] += service_result["scenarios_tested"]
            comprehensive_results["total_successful_tests"] += service_result["successful_tests"]
            comprehensive_results["total_failed_tests"] += service_result["failed_tests"]

        # Test authentication workflow
        auth_result = self.test_parent_authentication_workflow()
        comprehensive_results["workflow_results"]["parent_authentication"] = auth_result
        comprehensive_results["total_scenarios_tested"] += auth_result["scenarios_tested"]
        comprehensive_results["total_successful_tests"] += auth_result["successful_tests"]
        comprehensive_results["total_failed_tests"] += auth_result["failed_tests"]

        # Test student data retrieval
        data_result = self.test_student_data_retrieval_workflow()
        comprehensive_results["workflow_results"]["student_data_retrieval"] = data_result
        comprehensive_results["total_scenarios_tested"] += data_result["scenarios_tested"]
        comprehensive_results["total_successful_tests"] += data_result["successful_tests"]
        comprehensive_results["total_failed_tests"] += data_result["failed_tests"]

        # System health check
        print(f"\n🏥 Performing System Health Check")
        print("=" * 50)
        health_check = self.check_system_health()
        comprehensive_results["system_health"] = health_check

        # Final summary
        comprehensive_results["test_end_time"] = datetime.now().isoformat()
        comprehensive_results["overall_success_rate"] = (
            comprehensive_results["total_successful_tests"] / comprehensive_results["total_scenarios_tested"] * 100
        ) if comprehensive_results["total_scenarios_tested"] > 0 else 0

        # Print final summary
        print(f"\n🎯 COMPREHENSIVE TEST SUMMARY")
        print("=" * 50)
        print(f"📊 Total Scenarios: {comprehensive_results['total_scenarios_tested']}")
        print(f"✅ Successful Tests: {comprehensive_results['total_successful_tests']}")
        print(f"❌ Failed Tests: {comprehensive_results['total_failed_tests']}")
        print(f"📈 Overall Success Rate: {comprehensive_results['overall_success_rate']:.1f}%")

        # System readiness assessment
        readiness_score = self.assess_solution_readiness(comprehensive_results)
        comprehensive_results["readiness_score"] = readiness_score
        comprehensive_results["readiness_assessment"] = self.get_readiness_assessment(readiness_score)

        print(f"🚀 Solution Readiness Score: {readiness_score}/100")
        print(f"📋 Assessment: {comprehensive_results['readiness_assessment']}")

        return comprehensive_results

    def check_system_health(self) -> Dict[str, Any]:
        """Check health of all system components"""
        try:
            health_results = {}

            # Check main application health
            try:
                response = requests.get("http://localhost:8000/", timeout=10)
                health_results["main_application"] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code
                }
            except:
                health_results["main_application"] = {"status": "unhealthy", "error": "Connection failed"}

            # Check webhook endpoint
            try:
                response = requests.options("http://localhost:8000/api/v1/webhook", timeout=10)
                health_results["webhook_endpoint"] = {
                    "status": "healthy" if response.status_code in [200, 405] else "unhealthy",
                    "status_code": response.status_code
                }
            except:
                health_results["webhook_endpoint"] = {"status": "unhealthy", "error": "Connection failed"}

            # Check database connectivity (through API)
            try:
                response = requests.get("http://localhost:8000/api/v1/sessions", timeout=10)
                health_results["database_connectivity"] = {
                    "status": "healthy" if response.status_code in [200, 401, 403] else "unhealthy",
                    "status_code": response.status_code
                }
            except:
                health_results["database_connectivity"] = {"status": "unhealthy", "error": "Connection failed"}

            return health_results

        except Exception as e:
            return {"error": str(e), "status": "unknown"}

    def assess_solution_readiness(self, results: Dict[str, Any]) -> int:
        """Assess overall solution readiness on scale of 1-100"""
        score = 0

        # Service functionality (40 points)
        service_success_rate = results.get("overall_success_rate", 0)
        score += int(service_success_rate * 0.4)

        # System health (30 points)
        health_components = results.get("system_health", {})
        healthy_components = sum(1 for comp in health_components.values() if comp.get("status") == "healthy")
        total_components = len(health_components)
        if total_components > 0:
            health_score = (healthy_components / total_components) * 30
            score += int(health_score)

        # Workflow completeness (20 points)
        workflow_results = results.get("workflow_results", {})
        workflow_success_count = sum(1 for workflow in workflow_results.values()
                                  if workflow.get("successful_tests", 0) > 0)
        if workflow_results:
            workflow_score = (workflow_success_count / len(workflow_results)) * 20
            score += int(workflow_score)

        # Test coverage (10 points)
        total_expected = 24  # Expected total scenarios across all services
        actual_tested = results.get("total_scenarios_tested", 0)
        coverage_score = min(actual_tested / total_expected, 1.0) * 10
        score += int(coverage_score)

        return min(score, 100)

    def get_readiness_assessment(self, score: int) -> str:
        """Get readiness assessment based on score"""
        if score >= 90:
            return "🟢 Production Ready"
        elif score >= 80:
            return "🟡 Production Ready with Minor Issues"
        elif score >= 70:
            return "🟡 Beta Ready - Address Issues Before Production"
        elif score >= 60:
            return "🟠 Alpha Ready - Significant Improvements Needed"
        else:
            return "🔴 Development Phase - Not Ready for Production"

    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"catechese_system_test_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"📄 Test results saved to: {filename}")
        return filename


def main():
    """Main test execution function"""
    tester = CatecheseSystemTest()

    try:
        # Run comprehensive test
        results = tester.run_comprehensive_test()

        # Save results
        results_file = tester.save_results(results)

        # Print executive summary
        print(f"\n🎯 EXECUTIVE SUMMARY")
        print("=" * 50)
        print(f"📊 Overall Success Rate: {results['overall_success_rate']:.1f}%")
        print(f"🚀 Readiness Score: {results['readiness_score']}/100")
        print(f"📋 Assessment: {results['readiness_assessment']}")
        print(f"📄 Detailed Results: {results_file}")

        # Print service-specific results
        print(f"\n📋 SERVICE-SPECIFIC RESULTS")
        print("=" * 50)
        for service_type, service_result in results['service_results'].items():
            success_rate = (service_result['successful_tests'] / service_result['scenarios_tested'] * 100) if service_result['scenarios_tested'] > 0 else 0
            print(f"{service_type}: {success_rate:.1f}% success rate")

        # Print workflow results
        print(f"\n🔄 WORKFLOW RESULTS")
        print("=" * 50)
        for workflow_type, workflow_result in results['workflow_results'].items():
            success_rate = (workflow_result['successful_tests'] / workflow_result['scenarios_tested'] * 100) if workflow_result['scenarios_tested'] > 0 else 0
            print(f"{workflow_type}: {success_rate:.1f}% success rate")

        return results

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "test_failed": True}


if __name__ == "__main__":
    main()