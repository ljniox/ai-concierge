import json
import logging
import os
from typing import List, Optional

import requests
try:
    from anthropic import Anthropic  # type: ignore
except Exception:  # pragma: no cover
    Anthropic = None  # type: ignore

logger = logging.getLogger(__name__)


class EmbeddingsClient:
    """Embeddings via GLM (Anthropic-compatible base) with fallback strategy.

    Strategy:
      1) Try a standard /embeddings endpoint (model configurable)
      2) Fallback: use Anthropic Messages with a strict JSON instruction to emit a float array
    """

    def __init__(self):
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "").rstrip("/") or None
        # Prefer ANTHROPIC_AUTH_TOKEN if present, fallback to ANTHROPIC_API_KEY
        self.api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
        self.session = requests.Session()
        self.model = os.getenv("EMBEDDING_MODEL", "glm-4.5-embedding")
        # Default dimension for vector schema; we store JSON anyway
        self.dim = int(os.getenv("EMBEDDING_DIM", "384"))

        # Anthropic client for fallback (supports custom base_url)
        try:
            # Construct client if library and key are available
            self.anthropic = Anthropic(api_key=self.api_key, base_url=self.base_url) if (self.api_key and Anthropic) else None
        except Exception as e:
            logger.warning(f"Anthropic client init failed: {e}")
            self.anthropic = None

    def create(self, text: str) -> Optional[List[float]]:
        text = (text or "").strip()
        if not text:
            return None

        # 1) Try embeddings endpoint if base_url provided
        if self.base_url and self.api_key:
            try:
                url = f"{self.base_url}/embeddings"
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {"input": text, "model": self.model}
                r = self.session.post(url, headers=headers, json=payload, timeout=30)
                if 200 <= r.status_code < 300:
                    data = r.json()
                    # Support common shapes: {data:[{embedding:[...] }]} or {embedding:[...]}
                    if isinstance(data, dict):
                        if isinstance(data.get("data"), list) and data["data"]:
                            emb = data["data"][0].get("embedding")
                            if isinstance(emb, list):
                                return [float(x) for x in emb]
                        if isinstance(data.get("embedding"), list):
                            return [float(x) for x in data["embedding"]]
                else:
                    logger.warning(f"Embeddings endpoint status: {r.status_code} {r.text}")
            except Exception as e:
                logger.warning(f"Embeddings endpoint error: {e}")

        # 2) Fallback: Anthropic Messages with JSON instruction
        if self.anthropic:
            try:
                sys_prompt = (
                    "You convert text into a numerical embedding vector. "
                    "Return only a JSON array of floats (no text), length ~" + str(self.dim) + "."
                )
                msg = self.anthropic.messages.create(
                    model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
                    max_tokens=2048,
                    system=sys_prompt,
                    messages=[{"role": "user", "content": text}],
                )
                content = msg.content[0].text if msg and msg.content else ""
                # Parse JSON array
                embedding = json.loads(content)
                if isinstance(embedding, list):
                    return [float(x) for x in embedding]
            except Exception as e:
                logger.error(f"Anthropic fallback embedding error: {e}")

        return None


embeddings_client = EmbeddingsClient()
