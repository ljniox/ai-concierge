import logging
import os
from typing import Any, Dict, List, Optional

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
        # Lazy import
        client = None
        if api_key:
            try:
                from anthropic import Anthropic  # type: ignore
                client = Anthropic(api_key=api_key, base_url=base_url)
            except Exception as e:
                logger.warning(f"Anthropic client not available: {e}")
        self.client = client

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

        # Service-specific first flow: Catéchèse SJB Dakar (infos)
        if (service_code or "").upper() == "CATECHESE_SJB_DAKAR":
            response = self._run_catechese_infos(session, user_text)
            # Log assistant turn + embedding
            try:
                emb = embeddings_client.create(response)
                supabase_client.log_interaction(session_id, "assistant", response, meta={"service_code": service_code}, embedding=emb)
            except Exception as e:
                logger.warning(f"Log assistant interaction failed: {e}")
            return response

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

    def _run_catechese_infos(self, session: Dict[str, Any], user_text: str) -> str:
        """First flow: infos catéchèse. Generates a structured info message and saves an artifact."""
        session_id = session["id"]
        service_code = session.get("service_code") or "CATECHESE_SJB_DAKAR"

        # Basic intent routing (extend later):
        t = (user_text or "").lower()
        sub = "infos"
        if any(k in t for k in ["inscription", "inscrire", "inscriptions"]):
            sub = "inscription"
        elif any(k in t for k in ["horaire", "horaires", "heures", "quand"]):
            sub = "horaires"
        elif any(k in t for k in ["lieu", "où", "ou?"]):
            sub = "lieux"
        elif any(k in t for k in ["document", "pièce", "requis"]):
            sub = "documents"

        # Draft content (replace with live data when available)
        header = "Informations - Catéchèse St Jean Bosco Dakar"
        body = [
            "- Présentation: parcours de catéchèse pour enfants et jeunes.",
            "- Contact: Service Diocésain de la Catéchèse (SDB).",
            "- Détails: horaires, lieux, inscription, documents requis.",
        ]
        if sub == "inscription":
            body = [
                "- Inscription: formulaire à compléter + frais (si applicable).",
                "- Prévoir certificat de baptême ou EB si disponible.",
                "- Confirmation par message après validation du dossier.",
            ]
        elif sub == "horaires":
            body = [
                "- Horaires habituels: en semaine fin d'après-midi ou samedi matin (variable selon centre).",
                "- Le planning détaillé est communiqué à l'inscription.",
            ]
        elif sub == "lieux":
            body = [
                "- Lieux: centres/paroisses partenaires à Dakar (selon quartier).",
                "- Le lieu exact est indiqué lors de l'inscription.",
            ]
        elif sub == "documents":
            body = [
                "- Documents: extrait de baptême (EB) si disponible, photo d'identité, autorisation parentale.",
                "- Autres pièces peuvent être demandées selon le niveau.",
            ]

        msg = header + "\n" + "\n".join(body) + "\n\nSouhaitez-vous d'autres précisions (inscription, horaires, lieux, documents) ?"

        # Persist as artifact (report)
        try:
            supabase_client.save_artifact(
                session_id=session_id,
                service_code=service_code,
                type_="report",
                content=msg,
                meta={"subservice": sub},
            )
        except Exception as e:
            logger.warning(f"save_artifact failed: {e}")

        return msg


orchestrator = Orchestrator()
