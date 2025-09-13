import os
from typing import Optional

class WAHAConfig:
    """Configuration for WAHA webhook integration"""

    # WAHA API Configuration
    WAHA_BASE_URL: str = "https://waha-core.niox.ovh/api"
    WAHA_USERNAME: str = "admin"
    WAHA_PASSWORD: str = "WassProdt!2025"

    # Webhook Configuration
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "https://your-domain.com/webhook")
    WEBHOOK_VERIFY_TOKEN: str = os.getenv("WEBHOOK_VERIFY_TOKEN", "your-verify-token")

    # Session Configuration
    SESSION_NAME: str = os.getenv("SESSION_NAME", "default")
    WEBHOOK_EVENTS: list = ["message", "session.status", "chat"]

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", "8000"))

    @classmethod
    def get_webhook_payload(cls) -> dict:
        """Generate webhook configuration payload for WAHA"""
        return {
            "webhookUrl": cls.WEBHOOK_URL,
            "events": cls.WEBHOOK_EVENTS,
            "session": cls.SESSION_NAME
        }

    @classmethod
    def get_session_payload(cls) -> dict:
        """Generate session configuration payload for WAHA"""
        return {
            "name": cls.SESSION_NAME,
            "config": {
                "webhook": cls.get_webhook_payload()
            }
        }

# Example WAHA API calls using the configuration
def create_waha_session():
    """Create a new WAHA session with webhook configuration"""
    import requests
    from requests.auth import HTTPBasicAuth

    url = f"{WAHAConfig.WAHA_BASE_URL}/sessions"
    auth = HTTPBasicAuth(WAHAConfig.WAHA_USERNAME, WAHAConfig.WAHA_PASSWORD)

    try:
        response = requests.post(url, json=WAHAConfig.get_session_payload(), auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error creating WAHA session: {e}")
        return None

def get_waha_sessions():
    """Get list of existing WAHA sessions"""
    import requests
    from requests.auth import HTTPBasicAuth

    url = f"{WAHAConfig.WAHA_BASE_URL}/sessions"
    auth = HTTPBasicAuth(WAHAConfig.WAHA_USERNAME, WAHAConfig.WAHA_PASSWORD)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting WAHA sessions: {e}")
        return None

if __name__ == "__main__":
    print("WAHA Configuration:")
    print(f"Base URL: {WAHAConfig.WAHA_BASE_URL}")
    print(f"Webhook URL: {WAHAConfig.WEBHOOK_URL}")
    print(f"Verify Token: {WAHAConfig.WEBHOOK_VERIFY_TOKEN}")

    # Test API connection
    sessions = get_waha_sessions()
    if sessions:
        print(f"Existing sessions: {sessions}")
    else:
        print("Could not retrieve sessions or none exist")

    # Create new session
    new_session = create_waha_session()
    if new_session:
        print(f"Created new session: {new_session}")