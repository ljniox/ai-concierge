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
            # Best-effort create; if Supabase is not configured, still return menu
            created = supabase_client.create_session(phone, status="active", context={"state": "awaiting_selection"})
            session = created or {"id": None, "phone": phone, "status": "active", "context": {"state": "awaiting_selection"}}
            if created is None:
                logger.warning("Supabase unavailable: falling back to stateless menu")

        ctx = session.get("context") or {}
        state = ctx.get("state") or ("awaiting_selection" if not session.get("service_code") else "in_service")
        text_norm = (text or "").strip()

        # Menu shortcuts
        if text_norm.lower() in {"menu", "catalogue", "catalog", "help", "aide"}:
            return self._menu()

        if state == "awaiting_selection" or not session.get("service_code"):
            # Always show menu first if not yet shown in this session
            if not ctx.get("menu_shown"):
                supabase_client.update_session(session["id"], {"context": {"state": "awaiting_selection", "menu_shown": True}})
                return self._menu()

            # Try match selection on subsequent message
            services = self._services_with_james()
            selected = match_service(text_norm, services)
            if not selected:
                return self._menu()

            # Special: human handoff to James
            if (selected.get("code") or "").upper() == "HUMAIN_JAMES":
                # Keep session active but mark handoff
                supabase_client.update_session(session["id"], {"context": {"state": "human_handoff"}})
                if not self._is_james_available_by_time():
                    return ["James est indisponible pour le moment, mais il repondra des que possible"]
                # Within availability window
                return ["Nous vous mettons en relation avec James. Décrivez votre demande, s'il vous plaît."]

            # Normal service selection
            updates = {
                "service_code": selected.get("code"),
                "status": "in_service",
                "context": {"state": "in_service"},
            }
            if session.get("id"):
                session = supabase_client.update_session(session["id"], updates) or session
            reply = orchestrator.run(session, text_norm)
            title = selected.get("title") or selected.get("code")
            return [f"Service sélectionné: {title}", reply]

        # Already in service -> hand over to orchestrator
        reply = orchestrator.run(session, text_norm)
        return [reply]

    def _menu(self) -> List[str]:
        services = self._services_with_james()
        return [build_menu_message(services)]

    def _services_with_james(self) -> List[Dict[str, Any]]:
        services = list_services()
        # Append pseudo-service for human handoff to James as the last option
        services = list(services) + [{
            "code": "HUMAIN_JAMES",
            "title": "Parler directement à James",
            "keywords": ["james", "humain", "conseiller", "agent", "parler"],
            "enabled": True,
        }]
        return services

    def _is_james_available_by_time(self) -> bool:
        from datetime import datetime
        now = datetime.now().time()
        # Available between 07:00 and 23:00
        return (now.hour >= 7) and (now.hour < 23)


session_manager = SessionManager()
