"""
API Key Management with Round-Robin Rotation
"""

import threading
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys with round-robin rotation for load balancing"""

    def __init__(self, api_keys: List[str], provider_name: str):
        self.api_keys = api_keys
        self.provider_name = provider_name
        self.current_index = 0
        self.lock = threading.Lock()

        if not api_keys:
            logger.warning(f"No API keys provided for {provider_name}")

        logger.info(f"Key manager initialized for {provider_name} with {len(api_keys)} keys")

    def get_next_key(self) -> Optional[str]:
        """Get the next API key using round-robin rotation"""
        if not self.api_keys:
            logger.error(f"No API keys available for {self.provider_name}")
            return None

        with self.lock:
            key = self.api_keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.api_keys)

            logger.debug(f"Selected key {self.current_index - 1} for {self.provider_name}")

            return key

    def get_active_key_count(self) -> int:
        """Get the number of active API keys"""
        return len(self.api_keys)

    def remove_key(self, key_to_remove: str) -> bool:
        """Remove a compromised or invalid API key"""
        try:
            with self.lock:
                if key_to_remove in self.api_keys:
                    self.api_keys.remove(key_to_remove)
                    # Adjust current index if needed
                    if self.current_index >= len(self.api_keys):
                        self.current_index = 0

                    logger.warning(f"Removed key for {self.provider_name}, {len(self.api_keys)} keys remaining")
                    return True
                return False
        except Exception as e:
            logger.error(f"Key removal failed for {self.provider_name}: {str(e)}")
            return False


class ProviderConfig:
    """Configuration for AI providers"""

    def __init__(self, provider_type: str, base_url: str, model: str,
                 max_tokens: int = 1000, temperature: float = 0.7):
        self.provider_type = provider_type
        self.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.key_manager: Optional[APIKeyManager] = None

    def set_key_manager(self, key_manager: APIKeyManager):
        """Set the API key manager for this provider"""
        self.key_manager = key_manager

    def is_configured(self) -> bool:
        """Check if the provider is properly configured"""
        return (
            self.base_url and
            self.model and
            self.key_manager and
            self.key_manager.get_active_key_count() > 0
        )


class AIProviderRegistry:
    """Registry for managing multiple AI providers"""

    def __init__(self):
        self.providers = {}
        self.default_provider = None

    def register_provider(self, name: str, config: ProviderConfig, is_default: bool = False):
        """Register an AI provider"""
        self.providers[name] = config
        if is_default or not self.default_provider:
            self.default_provider = name

        is_default_flag = is_default or name == self.default_provider
        logger.info(f"Registered provider {name} (default: {is_default_flag}, configured: {config.is_configured()})")

    def get_provider(self, name: Optional[str] = None) -> Optional[ProviderConfig]:
        """Get a provider by name or return the default"""
        provider_name = name or self.default_provider
        return self.providers.get(provider_name)

    def get_active_providers(self) -> List[str]:
        """Get list of configured and active providers"""
        active = []
        for name, config in self.providers.items():
            if config.is_configured():
                active.append(name)
        return active

    def is_provider_available(self, name: str) -> bool:
        """Check if a provider is available and configured"""
        provider = self.providers.get(name)
        return provider is not None and provider.is_configured()