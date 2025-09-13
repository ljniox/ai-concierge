import os
import json
import logging
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Minimal Supabase REST client using service role key."""

    def __init__(self):
        self.base_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not self.base_url or not self.service_key:
            logger.warning("Supabase client missing configuration")
        self.rest_url = f"{self.base_url}/rest/v1"
        self.headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    # Services
    def list_services(self) -> List[Dict[str, Any]]:
        try:
            url = f"{self.rest_url}/services?enabled=is.true&order=title.asc"
            r = requests.get(url, headers=self.headers, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            logger.error(f"Supabase list_services error: {e}")
            return []

    def get_service(self, code: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.rest_url}/services?code=eq.{code}"
            r = requests.get(url, headers=self.headers, timeout=20)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Supabase get_service error: {e}")
            return None

    # Sessions
    def get_active_session_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.rest_url}/sessions?phone=eq.{phone}&status=in.(active,in_service)&order=started_at.desc&limit=1"
            r = requests.get(url, headers=self.headers, timeout=20)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Supabase get_active_session_by_phone error: {e}")
            return None

    def create_session(self, phone: str, status: str = "active", service_code: Optional[str] = None,
                       context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "phone": phone,
                "status": status,
                "service_code": service_code,
                "context": context or {"state": "awaiting_selection"},
            }
            url = f"{self.rest_url}/sessions"
            r = requests.post(url, headers=self.headers, json=payload, timeout=20)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Supabase create_session error: {e}")
            return None

    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            url = f"{self.rest_url}/sessions?id=eq.{session_id}"
            r = requests.patch(url, headers=self.headers, json=updates, timeout=20)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Supabase update_session error: {e}")
            return None

    # Interactions
    def log_interaction(self, session_id: str, role: str, content: str,
                        meta: Optional[Dict[str, Any]] = None,
                        embedding: Optional[List[float]] = None) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "session_id": session_id,
                "role": role,
                "content": content,
                "meta": meta or {},
            }
            if embedding is not None:
                payload["embedding_json"] = embedding
            url = f"{self.rest_url}/interactions"
            r = requests.post(url, headers=self.headers, json=payload, timeout=20)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Supabase log_interaction error: {e}")
            return None

    # Artifacts
    def save_artifact(self, session_id: str, service_code: str, type_: str,
                      content: str, meta: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        try:
            payload = {
                "session_id": session_id,
                "service_code": service_code,
                "type": type_,
                "content": content,
                "meta": meta or {},
            }
            url = f"{self.rest_url}/artifacts"
            r = requests.post(url, headers=self.headers, json=payload, timeout=20)
            r.raise_for_status()
            rows = r.json()
            return rows[0] if rows else None
        except Exception as e:
            logger.error(f"Supabase save_artifact error: {e}")
            return None


# Singleton
supabase_client = SupabaseClient()

