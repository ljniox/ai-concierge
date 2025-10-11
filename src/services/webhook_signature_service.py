"""
Webhook signature verification service for the automatic account creation system.

This module provides HMAC signature verification for webhook security
with support for multiple algorithms and platform-specific configurations.
"""

import hashlib
import hmac
import os
from typing import Dict, Optional, Tuple, List, Any
from dataclasses import dataclass
from urllib.parse import quote

from src.utils.logging import get_logger
from src.utils.exceptions import SecurityError, ValidationError

logger = get_logger(__name__)


@dataclass
class SignatureVerificationResult:
    """Result of signature verification."""
    is_valid: bool
    algorithm: str
    provided_signature: Optional[str] = None
    computed_signature: Optional[str] = None
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WebhookConfig:
    """Webhook configuration for signature verification."""

    def __init__(self, platform: str, secret_key: str, algorithm: str = "sha256",
                 header_name: str = "X-Signature", encoding: str = "utf-8"):
        self.platform = platform
        self.secret_key = secret_key
        self.algorithm = algorithm.lower()
        self.header_name = header_name
        self.encoding = encoding

        # Platform-specific settings
        self.platform_settings = self._get_platform_settings()

    def _get_platform_settings(self) -> Dict[str, Any]:
        """Get platform-specific webhook settings."""
        settings = {
            # WhatsApp Business API settings
            'whatsapp': {
                'header_name': 'X-Hub-Signature-256',
                'algorithm': 'sha256',
                'prefix': 'sha256=',
                'encoding': 'utf-8'
            },
            # Telegram Bot API settings
            'telegram': {
                'header_name': 'X-Telegram-Bot-Api-Secret-Token',
                'algorithm': 'sha256',
                'prefix': '',
                'encoding': 'utf-8'
            },
            # Generic webhook settings
            'generic': {
                'header_name': 'X-Signature',
                'algorithm': 'sha256',
                'prefix': '',
                'encoding': 'utf-8'
            }
        }

        platform_settings = settings.get(self.platform.lower(), settings['generic'])

        # Override with instance settings if provided
        if self.header_name != "X-Signature":
            platform_settings['header_name'] = self.header_name
        if self.algorithm != "sha256":
            platform_settings['algorithm'] = self.algorithm

        return platform_settings


class WebhookSignatureService:
    """
    Webhook signature verification service.

    Provides secure HMAC signature verification for incoming webhooks
    with support for multiple algorithms and platform configurations.
    """

    def __init__(self):
        self.supported_algorithms = {
            'sha256': hashlib.sha256,
            'sha1': hashlib.sha1,
            'md5': hashlib.md5,
            'sha384': hashlib.sha384,
            'sha512': hashlib.sha512
        }

        # Default configurations for common platforms
        self.configurations: Dict[str, WebhookConfig] = {}

        # Load default configurations from environment
        self._load_default_configurations()

    def _load_default_configurations(self) -> None:
        """Load default webhook configurations from environment variables."""

        # WhatsApp configuration
        whatsapp_secret = os.getenv("WHATSAPP_WEBHOOK_SECRET")
        if whatsapp_secret:
            self.configurations['whatsapp'] = WebhookConfig(
                platform='whatsapp',
                secret_key=whatsapp_secret
            )
            logger.info("WhatsApp webhook configuration loaded")

        # Telegram configuration
        telegram_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        if telegram_secret:
            self.configurations['telegram'] = WebhookConfig(
                platform='telegram',
                secret_key=telegram_secret
            )
            logger.info("Telegram webhook configuration loaded")

        # Generic webhook configuration
        generic_secret = os.getenv("WEBHOOK_SECRET_KEY")
        if generic_secret:
            self.configurations['generic'] = WebhookConfig(
                platform='generic',
                secret_key=generic_secret
            )
            logger.info("Generic webhook configuration loaded")

    def add_configuration(self, config: WebhookConfig) -> None:
        """
        Add a webhook configuration.

        Args:
            config: Webhook configuration to add
        """
        self.configurations[config.platform] = config
        logger.info(f"Webhook configuration added for platform: {config.platform}")

    def get_configuration(self, platform: str) -> Optional[WebhookConfig]:
        """
        Get webhook configuration for a platform.

        Args:
            platform: Platform name

        Returns:
            WebhookConfig or None if not found
        """
        return self.configurations.get(platform)

    def verify_signature(
        self,
        platform: str,
        payload: str,
        headers: Dict[str, str],
        secret_key: Optional[str] = None
    ) -> SignatureVerificationResult:
        """
        Verify webhook signature.

        Args:
            platform: Platform name
            payload: Raw request payload
            headers: Request headers
            secret_key: Override secret key (optional)

        Returns:
            SignatureVerificationResult with verification details

        Raises:
            ValidationError: If platform configuration is not found
        """
        # Get configuration
        config = self.get_configuration(platform)
        if not config:
            raise ValidationError(f"No webhook configuration found for platform: {platform}")

        # Use provided secret key if available
        effective_secret = secret_key or config.secret_key
        if not effective_secret:
            return SignatureVerificationResult(
                is_valid=False,
                algorithm=config.algorithm,
                errors=["No secret key available for signature verification"]
            )

        # Get signature from headers
        signature_header = headers.get(config.platform_settings['header_name'])
        if not signature_header:
            return SignatureVerificationResult(
                is_valid=False,
                algorithm=config.algorithm,
                errors=[f"Missing signature header: {config.platform_settings['header_name']}"]
            )

        # Extract signature value (remove prefix if present)
        provided_signature = self._extract_signature(signature_header, config)
        if not provided_signature:
            return SignatureVerificationResult(
                is_valid=False,
                algorithm=config.algorithm,
                errors=["Invalid signature format"]
            )

        # Verify algorithm support
        if config.algorithm not in self.supported_algorithms:
            return SignatureVerificationResult(
                is_valid=False,
                algorithm=config.algorithm,
                errors=[f"Unsupported algorithm: {config.algorithm}"]
            )

        # Compute expected signature
        computed_signature = self._compute_signature(
            payload=payload,
            secret_key=effective_secret,
            algorithm=config.algorithm,
            encoding=config.encoding
        )

        # Perform secure comparison
        is_valid = self._secure_compare(provided_signature, computed_signature)

        # Create result
        result = SignatureVerificationResult(
            is_valid=is_valid,
            algorithm=config.algorithm,
            provided_signature=provided_signature,
            computed_signature=computed_signature,
            metadata={
                'platform': platform,
                'header_name': config.platform_settings['header_name'],
                'encoding': config.encoding
            }
        )

        if not is_valid:
            result.errors.append("Signature mismatch")
            logger.warning(
                "Webhook signature verification failed",
                platform=platform,
                header_name=config.platform_settings['header_name']
            )
        else:
            logger.debug(
                "Webhook signature verified successfully",
                platform=platform
            )

        return result

    def _extract_signature(self, signature_header: str, config: WebhookConfig) -> Optional[str]:
        """
        Extract signature value from header.

        Args:
            signature_header: Raw signature header value
            config: Webhook configuration

        Returns:
            Extracted signature or None if invalid
        """
        prefix = config.platform_settings.get('prefix', '')

        if prefix and signature_header.startswith(prefix):
            return signature_header[len(prefix):]

        # Handle WhatsApp format: sha256=signature
        if signature_header.startswith('sha256='):
            return signature_header[7:]

        # Handle other common formats
        for common_prefix in ['sha1=', 'sha384=', 'sha512=', 'hmac-sha256=']:
            if signature_header.startswith(common_prefix):
                return signature_header[len(common_prefix):]

        # Return as-is if no prefix
        return signature_header

    def _compute_signature(
        self,
        payload: str,
        secret_key: str,
        algorithm: str,
        encoding: str = 'utf-8'
    ) -> str:
        """
        Compute HMAC signature.

        Args:
            payload: Payload to sign
            secret_key: Secret key for signing
            algorithm: Hash algorithm
            encoding: Text encoding

        Returns:
            Computed signature as hex string
        """
        if algorithm not in self.supported_algorithms:
            raise SecurityError(f"Unsupported algorithm: {algorithm}")

        hash_func = self.supported_algorithms[algorithm]

        # Create HMAC
        hmac_obj = hmac.new(
            key=secret_key.encode(encoding),
            msg=payload.encode(encoding),
            digestmod=hash_func
        )

        # Return hex digest
        return hmac_obj.hexdigest()

    def _secure_compare(self, signature1: str, signature2: str) -> bool:
        """
        Securely compare two signatures to prevent timing attacks.

        Args:
            signature1: First signature
            signature2: Second signature

        Returns:
            True if signatures match
        """
        try:
            return hmac.compare_digest(signature1, signature2)
        except Exception:
            # Fallback to direct comparison if hmac.compare_digest fails
            return signature1 == signature2

    def generate_signature(
        self,
        platform: str,
        payload: str,
        secret_key: Optional[str] = None
    ) -> str:
        """
        Generate webhook signature for testing purposes.

        Args:
            platform: Platform name
            payload: Payload to sign
            secret_key: Override secret key (optional)

        Returns:
            Generated signature

        Raises:
            ValidationError: If platform configuration is not found
        """
        config = self.get_configuration(platform)
        if not config:
            raise ValidationError(f"No webhook configuration found for platform: {platform}")

        effective_secret = secret_key or config.secret_key
        if not effective_secret:
            raise ValidationError("No secret key available for signature generation")

        signature = self._compute_signature(
            payload=payload,
            secret_key=effective_secret,
            algorithm=config.algorithm,
            encoding=config.encoding
        )

        # Add prefix if required by platform
        prefix = config.platform_settings.get('prefix', '')
        return prefix + signature if prefix else signature

    def verify_webhook_event(
        self,
        platform: str,
        event_data: Dict[str, Any],
        headers: Dict[str, str],
        secret_key: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify webhook event and return parsed data if valid.

        Args:
            platform: Platform name
            event_data: Parsed event data
            headers: Request headers
            secret_key: Override secret key (optional)

        Returns:
            Tuple of (is_valid, processed_event_data)
        """
        # Convert event data back to string for signature verification
        import json
        payload = json.dumps(event_data, sort_keys=True, separators=(',', ':'))

        # Verify signature
        result = self.verify_signature(platform, payload, headers, secret_key)

        if not result.is_valid:
            return False, {
                'error': 'Invalid signature',
                'errors': result.errors,
                'platform': platform
            }

        # Add verification metadata to event data
        processed_event = {
            **event_data,
            '_verification': {
                'verified_at': str(result.metadata.get('timestamp', 'unknown')),
                'algorithm': result.algorithm,
                'platform': platform
            }
        }

        return True, processed_event

    def get_verification_statistics(self) -> Dict[str, Any]:
        """
        Get webhook verification service statistics.

        Returns:
            Service statistics
        """
        return {
            'supported_platforms': list(self.configurations.keys()),
            'supported_algorithms': list(self.supported_algorithms.keys()),
            'total_configurations': len(self.configurations),
            'platform_details': {
                platform: {
                    'algorithm': config.algorithm,
                    'header_name': config.platform_settings['header_name'],
                    'has_secret_key': bool(config.secret_key)
                }
                for platform, config in self.configurations.items()
            }
        }

    def validate_configuration(self, config: WebhookConfig) -> List[str]:
        """
        Validate webhook configuration.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not config.platform:
            errors.append("Platform name is required")

        if not config.secret_key:
            errors.append("Secret key is required")

        if not config.algorithm:
            errors.append("Algorithm is required")
        elif config.algorithm not in self.supported_algorithms:
            errors.append(f"Unsupported algorithm: {config.algorithm}")

        if not config.encoding:
            errors.append("Encoding is required")

        return errors

    def create_test_signature(
        self,
        platform: str,
        payload: str,
        secret_key: Optional[str] = None,
        include_headers: bool = True
    ) -> Dict[str, str]:
        """
        Create test signature and headers for testing.

        Args:
            platform: Platform name
            payload: Test payload
            secret_key: Override secret key (optional)
            include_headers: Whether to include headers in result

        Returns:
            Dictionary with signature and optional headers
        """
        config = self.get_configuration(platform)
        if not config:
            raise ValidationError(f"No webhook configuration found for platform: {platform}")

        signature = self.generate_signature(platform, payload, secret_key)

        result = {
            'signature': signature,
            'algorithm': config.algorithm,
            'platform': platform
        }

        if include_headers:
            header_name = config.platform_settings['header_name']
            result['headers'] = {
                header_name: signature,
                'Content-Type': 'application/json'
            }

        return result


# Global webhook signature service instance
_webhook_signature_service: Optional[WebhookSignatureService] = None


def get_webhook_signature_service() -> WebhookSignatureService:
    """Get the global webhook signature service instance."""
    global _webhook_signature_service
    if _webhook_signature_service is None:
        _webhook_signature_service = WebhookSignatureService()
    return _webhook_signature_service


def verify_webhook_signature(
    platform: str,
    payload: str,
    headers: Dict[str, str],
    secret_key: Optional[str] = None
) -> SignatureVerificationResult:
    """Verify webhook signature using global service."""
    service = get_webhook_signature_service()
    return service.verify_signature(platform, payload, headers, secret_key)


def generate_webhook_signature(
    platform: str,
    payload: str,
    secret_key: Optional[str] = None
) -> str:
    """Generate webhook signature using global service."""
    service = get_webhook_signature_service()
    return service.generate_signature(platform, payload, secret_key)


def verify_webhook_event(
    platform: str,
    event_data: Dict[str, Any],
    headers: Dict[str, str],
    secret_key: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """Verify webhook event using global service."""
    service = get_webhook_signature_service()
    return service.verify_webhook_event(platform, event_data, headers, secret_key)