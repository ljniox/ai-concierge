#!/usr/bin/env python3
"""
WAHA Webhook Configuration Script

This script helps configure webhooks for WAHA using the API key.
"""

import requests
import json
import sys

# Configuration
WAHA_BASE_URL = "https://waha-core.niox.ovh/api"
API_KEY = "28C5435535C2487DAFBD1164B9CD4E34"
WEBHOOK_URL = "https://ai-concierge.niox.ovh/webhook"
SESSION_NAME = "default"

# Headers for API requests
headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def create_session_with_webhook():
    """Create a new WAHA session with webhook configuration"""
    payload = {
        "name": SESSION_NAME,
        "config": {
            "webhook": {
                "webhookUrl": WEBHOOK_URL,
                "events": ["message", "session.status", "chat"],
                "session": SESSION_NAME
            }
        }
    }

    try:
        response = requests.post(
            f"{WAHA_BASE_URL}/sessions",
            headers=headers,
            json=payload,
            verify=False
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def update_session_webhook():
    """Update existing session with webhook configuration"""
    payload = {
        "config": {
            "webhook": {
                "webhookUrl": WEBHOOK_URL,
                "events": ["message", "session.status", "chat"]
            }
        }
    }

    try:
        response = requests.put(
            f"{WAHA_BASE_URL}/sessions/{SESSION_NAME}",
            headers=headers,
            json=payload,
            verify=False
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def get_session_info():
    """Get information about the session"""
    try:
        response = requests.get(
            f"{WAHA_BASE_URL}/sessions/{SESSION_NAME}",
            headers=headers,
            verify=False
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def start_session():
    """Start the session"""
    try:
        response = requests.post(
            f"{WAHA_BASE_URL}/sessions/{SESSION_NAME}/start",
            headers=headers,
            verify=False
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def send_test_message():
    """Send a test message to verify webhook is working"""
    payload = {
        "session": SESSION_NAME,
        "chatId": "221773387902@c.us",
        "text": "🔧 Testing webhook configuration - WAHA API connection successful!"
    }

    try:
        response = requests.post(
            f"{WAHA_BASE_URL}/sendText",
            headers=headers,
            json=payload,
            verify=False
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def main():
    """Main function to run webhook setup"""
    print("🚀 WAHA Webhook Configuration")
    print("=" * 40)

    # Check current session status
    print("1. Checking current session status...")
    session_info = get_session_info()
    if "error" in session_info:
        print(f"❌ Error getting session info: {session_info['error']}")
        return

    print(f"✅ Session found: {session_info.get('name', 'Unknown')}")
    print(f"   Status: {session_info.get('status', 'Unknown')}")

    # Try to update webhook configuration
    print("\n2. Configuring webhook...")
    webhook_result = update_session_webhook()

    if "error" in webhook_result:
        print(f"❌ Error configuring webhook: {webhook_result['error']}")
    else:
        print("✅ Webhook configuration updated successfully!")
        print(f"   Webhook URL: {WEBHOOK_URL}")
        print("   Events: message, session.status, chat")

    # Send test message
    print("\n3. Sending test message...")
    test_result = send_test_message()

    if "error" in test_result:
        print(f"❌ Error sending test message: {test_result['error']}")
    else:
        print("✅ Test message sent successfully!")
        print("   Check your WhatsApp for the test message")

    print("\n🎉 WAHA webhook configuration complete!")
    print(f"📡 Your webhook is ready at: {WEBHOOK_URL}")

if __name__ == "__main__":
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    main()