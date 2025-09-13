import logging
from typing import Optional
import requests
import os

logger = logging.getLogger(__name__)


def send_text(to_number: str, text: str) -> bool:
    """Send a WhatsApp text via WAHA."""
    api_key = os.getenv('WAHA_API_KEY', '28C5435535C2487DAFBD1164B9CD4E34')
    base_url = os.getenv('WAHA_BASE_URL', 'https://waha-core.niox.ovh/api')
    session_name = os.getenv('SESSION_NAME', 'default')

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "session": session_name,
        "chatId": f"{to_number}@c.us",
        "text": text
    }
    try:
        r = requests.post(f"{base_url}/sendText", headers=headers, json=payload, verify=False, timeout=20)
        if 200 <= r.status_code < 300:
            return True
        logger.error(f"WA send failed: {r.status_code} {r.text}")
    except Exception as e:
        logger.error(f"WA send error: {e}")
    return False

