import logging
import os
from typing import Any, Dict, List, Optional

from anthropic import Anthropic

from supabase_client import supabase_client
from embeddings import embeddings_client

logger = logging.getLogger(__name__)


class Orchestrator:
    """Minimal Claude orchestrator with tool stubs.

    For now: single-turn guidance. Extensible to tool-calls and multi-step flows.
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
        base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
        self.client = Anthropic(api_key=api_key, base_url=base_url) if api_key else None

    def run(self, session: Dict[str, Any], user_text: str) -> str:
        """Produce an assistant response, log interaction + embeddings.
        This is a simple first pass without explicit tool-calls.
        """
        session_id = session["id"]
        service_code = session.get("service_code")

        # Log user turn + embedding
        try:
            emb = embeddings_client.create(user_text)
            supabase_client.log_interaction(session_id, "user", user_text, meta={"service_code": service_code}, embedding=emb)
        except Exception as e:
            logger.warning(f"Log user interaction failed: {e}")

        # Minimal domain guidance per service
        domain_context = self._service_context(service_code)

        if not self.client:
            # Fallback deterministic response
            return f"[Mode dégradé] {domain_context} Vous avez dit: {user_text}"

        system = (
            "Tu es gust-ai, assistant de James. Sois clair, concis et orienté action. "
            "Produis toujours un résultat: message utile, rapport structuré, ou confirmation d'action."
        )

        prompt = (
            f"Contexte service: {domain_context}\n\n"
            f"Message utilisateur: {user_text}\n\n"
            "Réponds en français, avec étapes ou actions concrètes si utile."
        )

        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=600,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            response = msg.content[0].text if msg and msg.content else ""
        except Exception as e:
            logger.error(f"Claude orchestration error: {e}")
            response = "Désolé, une erreur est survenue lors du traitement."

        # Log assistant turn + embedding
        try:
            emb = embeddings_client.create(response)
            supabase_client.log_interaction(session_id, "assistant", response, meta={"service_code": service_code}, embedding=emb)
        except Exception as e:
            logger.warning(f"Log assistant interaction failed: {e}")

        return response

    def _service_context(self, service_code: Optional[str]) -> str:
        if not service_code:
            return "Service non sélectionné."
        if service_code.upper() == "CATECHESE_SJB_DAKAR":
            return (
                "Catéchèse St Jean Bosco Dakar. Sous-service: informations générales sur la catéchèse, "
                "horaires, lieux, inscription, documents requis."
            )
        return f"Service {service_code}."


orchestrator = Orchestrator()

