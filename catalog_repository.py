import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from supabase_client import supabase_client

logger = logging.getLogger(__name__)


def list_services() -> List[Dict[str, Any]]:
    return supabase_client.list_services()


def build_menu_message(services: List[Dict[str, Any]]) -> str:
    lines = [
        "Je suis gust-ai, assistant virtuel de James. Que voulez-vous faire ?",
    ]
    for idx, s in enumerate(services, start=1):
        title = s.get("title") or s.get("code")
        lines.append(f"{idx}) {title}")
    lines.append("Répondez par le numéro ou un mot-clé.")
    return "\n".join(lines)


def match_service(user_input: str, services: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    txt = (user_input or "").strip().lower()
    if not txt:
        return None

    # Try numeric choice
    if txt.isdigit():
        i = int(txt)
        if 1 <= i <= len(services):
            return services[i - 1]

    # Try keywords
    for s in services:
        kws = s.get("keywords") or []
        for kw in kws:
            if kw and kw.lower() in txt:
                return s

    # Try title contains
    for s in services:
        title = (s.get("title") or "").lower()
        if title and title in txt or txt in title:
            return s

    return None

