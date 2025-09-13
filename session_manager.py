import logging
from typing import Any, Dict, List, Optional

from catalog_repository import list_services, build_menu_message, match_service
from supabase_client import supabase_client
from orchestrator import orchestrator

logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        pass

    def handle_incoming(self, phone: str, text: str) -> List[str]:
        """Handle user message and return a list of outgoing messages.

        States: awaiting_selection -> in_service -> closed
        """
        # Get or create session
        session = supabase_client.get_active_session_by_phone(phone)
        if not session:
            session = supabase_client.create_session(phone, status="active", context={"state": "awaiting_selection"})
        if not session:
            logger.error("Failed to init session")
            return ["Désolé, le service est temporairement indisponible."]

        state = (session.get("context") or {}).get("state") or ("awaiting_selection" if not session.get("service_code") else "in_service")
        text_norm = (text or "").strip()

        # Menu shortcuts
        if text_norm.lower() in {"menu", "catalogue", "catalog", "help", "aide"}:
            return self._menu()

        if state == "awaiting_selection" or not session.get("service_code"):
            # Try match selection
            services = list_services()
            selected = match_service(text_norm, services)
            if not selected:
                # Return menu
                return self._menu()
            # Update session -> in_service
            updates = {
                "service_code": selected.get("code"),
                "status": "in_service",
                "context": {"state": "in_service"},
            }
            session = supabase_client.update_session(session["id"], updates) or session
            # Acknowledge + hand to orchestrator
            reply = orchestrator.run(session, text_norm)
            title = selected.get("title") or selected.get("code")
            return [f"Service sélectionné: {title}", reply]

        # Already in service -> hand over to orchestrator
        reply = orchestrator.run(session, text_norm)
        return [reply]

    def _menu(self) -> List[str]:
        services = list_services()
        return [build_menu_message(services)]


session_manager = SessionManager()

