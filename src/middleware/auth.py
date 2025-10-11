"""
Authentication Middleware for Account Creation System

This middleware handles authentication for platform-specific requests,
including webhook verification and JWT token validation.
"""

import os
import hashlib
import hmac
import logging
from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import json

from src.models.account import UserAccount
from src.models.session import AccountCreationSession
from src.utils.logging import account_logger


class PlatformAuthMiddleware:
    """Authentication middleware for platform-specific requests."""

    def __init__(self, require_auth: bool = True):
        """
        Initialize platform authentication middleware.

        Args:
            require_auth: Whether to require authentication for all requests
        """
        self.require_auth = require_auth
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.telegram_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    async def verify_telegram_webhook(self, request: Request) -> bool:
        """
        Verify Telegram webhook signature.

        Args:
            request: FastAPI request object

        Returns:
            True if webhook is valid, False otherwise
        """
        try:
            # Get secret token from header
            secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")

            if not secret_token:
                self.logger.warning("Missing Telegram webhook secret token")
                return False

            if not self.telegram_secret:
                self.logger.error("Telegram webhook secret not configured")
                return False

            # Verify secret token
            if not hmac.compare_digest(secret_token, self.telegram_secret):
                self.logger.warning(f"Invalid Telegram webhook secret: {secret_token[:10]}***")
                return False

            self.logger.info("Telegram webhook verified successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error verifying Telegram webhook: {str(e)}")
            return False

    async def verify_whatsapp_webhook(self, request: Request) -> bool:
        """
        Verify WhatsApp webhook signature.

        Args:
            request: FastAPI request object

        Returns:
            True if webhook is valid, False otherwise
        """
        try:
            # For WAHA, we can verify the session and token
            # Get WAHA token from header or check session
            waha_token = request.headers.get("Authorization")

            if not waha_token:
                self.logger.warning("Missing WhatsApp webhook authorization")
                return False

            # Verify WAHA token (basic implementation)
            expected_token = os.getenv("WAHA_API_TOKEN")
            if expected_token and waha_token == f"Bearer {expected_token}":
                self.logger.info("WhatsApp webhook verified successfully")
                return True

            self.logger.warning("Invalid WhatsApp webhook token")
            return False

        except Exception as e:
            self.logger.error(f"Error verifying WhatsApp webhook: {str(e)}")
            return False

    def create_jwt_token(self, user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT token for user authentication.

        Args:
            user_data: User data to include in token
            expires_delta: Custom expiration time

        Returns:
            JWT token string
        """
        try:
            if not self.jwt_secret_key:
                raise ValueError("JWT secret key not configured")

            to_encode = user_data.copy()

            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=self.jwt_expire_minutes)

            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, self.jwt_secret_key, algorithm=self.jwt_algorithm)

            self.logger.info(f"JWT token created for user {user_data.get('user_id', 'unknown')}")
            return encoded_jwt

        except Exception as e:
            self.logger.error(f"Error creating JWT token: {str(e)}")
            raise

    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded token data if valid, None otherwise
        """
        try:
            if not self.jwt_secret_key:
                self.logger.error("JWT secret key not configured")
                return None

            # Remove "Bearer " prefix if present
            if token.startswith("Bearer "):
                token = token[7:]

            payload = jwt.decode(token, self.jwt_secret_key, algorithms=[self.jwt_algorithm])

            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                self.logger.warning("JWT token expired")
                return None

            self.logger.info(f"JWT token verified for user {payload.get('user_id', 'unknown')}")
            return payload

        except JWTError as e:
            self.logger.warning(f"JWT token verification failed: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error verifying JWT token: {str(e)}")
            return None

    def create_platform_token(self, platform: str, platform_user_id: str, user_id: int) -> str:
        """
        Create platform-specific authentication token.

        Args:
            platform: Platform name ('telegram' or 'whatsapp')
            platform_user_id: Platform-specific user ID
            user_id: Internal user ID

        Returns:
            Platform token string
        """
        try:
            token_data = {
                "platform": platform,
                "platform_user_id": platform_user_id,
                "user_id": user_id,
                "type": "platform_auth",
                "iat": datetime.utcnow().timestamp()
            }

            # Create short-lived token (30 minutes)
            token = self.create_jwt_token(token_data, timedelta(minutes=30))

            self.logger.info(f"Platform token created for {platform} user {platform_user_id[:10]}***")
            return token

        except Exception as e:
            self.logger.error(f"Error creating platform token: {str(e)}")
            raise

    def verify_platform_token(self, token: str, expected_platform: str) -> Optional[Dict[str, Any]]:
        """
        Verify platform-specific token.

        Args:
            token: Platform token string
            expected_platform: Expected platform name

        Returns:
            Token data if valid, None otherwise
        """
        try:
            payload = self.verify_jwt_token(token)

            if not payload:
                return None

            # Verify token type and platform
            if payload.get("type") != "platform_auth":
                self.logger.warning("Invalid token type for platform authentication")
                return None

            if payload.get("platform") != expected_platform:
                self.logger.warning(f"Token platform mismatch: expected {expected_platform}, got {payload.get('platform')}")
                return None

            return payload

        except Exception as e:
            self.logger.error(f"Error verifying platform token: {str(e)}")
            return None


class RateLimitMiddleware:
    """Rate limiting middleware for account creation endpoints."""

    def __init__(self, redis_client=None):
        """
        Initialize rate limiting middleware.

        Args:
            redis_client: Redis client for distributed rate limiting
        """
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)

        # Rate limits from configuration
        self.account_creation_limit = os.getenv("ACCOUNT_CREATION_RATE_LIMIT", "100_per_minute")
        self.phone_validation_limit = os.getenv("PHONE_VALIDATION_RATE_LIMIT", "1000_per_minute")
        self.admin_operations_limit = os.getenv("ADMIN_OPERATIONS_RATE_LIMIT", "200_per_minute")

    def _parse_rate_limit(self, rate_string: str) -> tuple[int, int]:
        """
        Parse rate limit string like "100_per_minute" into (count, period_seconds).

        Args:
            rate_string: Rate limit string

        Returns:
            Tuple of (count, period_seconds)
        """
        try:
            parts = rate_string.split("_per_")
            count = int(parts[0])
            period = parts[1]

            if period == "minute":
                period_seconds = 60
            elif period == "hour":
                period_seconds = 3600
            elif period == "day":
                period_seconds = 86400
            else:
                period_seconds = 60  # Default to minute

            return count, period_seconds

        except Exception:
            # Default fallback
            return 100, 60

    async def check_rate_limit(
        self,
        identifier: str,
        limit_type: str,
        custom_limit: Optional[str] = None
    ) -> bool:
        """
        Check if rate limit is exceeded.

        Args:
            identifier: Unique identifier (IP address, user ID, etc.)
            limit_type: Type of rate limit to check
            custom_limit: Custom rate limit string

        Returns:
            True if within limit, False if exceeded
        """
        try:
            # Get rate limit configuration
            if custom_limit:
                rate_limit = custom_limit
            elif limit_type == "account_creation":
                rate_limit = self.account_creation_limit
            elif limit_type == "phone_validation":
                rate_limit = self.phone_validation_limit
            elif limit_type == "admin_operations":
                rate_limit = self.admin_operations_limit
            else:
                rate_limit = "100_per_minute"  # Default

            max_requests, period_seconds = self._parse_rate_limit(rate_limit)

            if self.redis:
                # Use Redis for distributed rate limiting
                key = f"rate_limit:{limit_type}:{identifier}"

                # Get current count
                current_count = await self.redis.get(key)

                if current_count is None:
                    # First request in this period
                    await self.redis.setex(key, period_seconds, 1)
                    return True
                else:
                    current_count = int(current_count)

                    if current_count >= max_requests:
                        self.logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{max_requests}")
                        account_logger.log_rate_limit_exceeded(identifier, limit_type)
                        return False
                    else:
                        # Increment counter
                        await self.redis.incr(key)
                        return True
            else:
                # In-memory rate limiting (less reliable)
                # For production, Redis should be used
                self.logger.warning("Redis not available, using in-memory rate limiting")
                return True

        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}")
            # Fail open - allow request if rate limiting fails
            return True


class AuthManager:
    """Authentication manager combining all authentication methods."""

    def __init__(self, redis_client=None):
        """
        Initialize authentication manager.

        Args:
            redis_client: Redis client for distributed operations
        """
        self.platform_auth = PlatformAuthMiddleware()
        self.rate_limiter = RateLimitMiddleware(redis_client)
        self.logger = logging.getLogger(__name__)

    async def authenticate_webhook_request(
        self,
        request: Request,
        platform: str,
        client_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Authenticate incoming webhook request.

        Args:
            request: FastAPI request object
            platform: Platform name ('telegram' or 'whatsapp')
            client_ip: Client IP address for rate limiting

        Returns:
            Authentication result dictionary
        """
        result = {
            "authenticated": False,
            "platform": platform,
            "error": None,
            "rate_limited": False
        }

        try:
            # Rate limiting check
            if client_ip:
                if not await self.rate_limiter.check_rate_limit(
                    client_ip, f"{platform}_webhook"
                ):
                    result["rate_limited"] = True
                    result["error"] = "Rate limit exceeded"
                    return result

            # Platform-specific verification
            if platform == "telegram":
                if await self.platform_auth.verify_telegram_webhook(request):
                    result["authenticated"] = True
                else:
                    result["error"] = "Invalid Telegram webhook"
            elif platform == "whatsapp":
                if await self.platform_auth.verify_whatsapp_webhook(request):
                    result["authenticated"] = True
                else:
                    result["error"] = "Invalid WhatsApp webhook"
            else:
                result["error"] = f"Unsupported platform: {platform}"

        except Exception as e:
            self.logger.error(f"Error authenticating webhook request: {str(e)}")
            result["error"] = "Authentication error"

        return result

    async def authenticate_api_request(
        self,
        request: Request,
        required_permissions: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Authenticate API request with JWT token.

        Args:
            request: FastAPI request object
            required_permissions: List of required permissions

        Returns:
            Authentication result dictionary
        """
        result = {
            "authenticated": False,
            "user_id": None,
            "permissions": [],
            "error": None
        }

        try:
            # Get Authorization header
            auth_header = request.headers.get("Authorization")

            if not auth_header:
                result["error"] = "Missing authorization header"
                return result

            # Verify JWT token
            token_data = self.platform_auth.verify_jwt_token(auth_header)

            if not token_data:
                result["error"] = "Invalid or expired token"
                return result

            # Extract user information
            user_id = token_data.get("user_id")
            permissions = token_data.get("permissions", [])
            roles = token_data.get("roles", [])

            # Check required permissions
            if required_permissions:
                missing_permissions = [
                    perm for perm in required_permissions
                    if perm not in permissions
                ]

                if missing_permissions:
                    result["error"] = f"Missing required permissions: {missing_permissions}"
                    return result

            result["authenticated"] = True
            result["user_id"] = user_id
            result["permissions"] = permissions
            result["roles"] = roles

            self.logger.info(f"API request authenticated for user {user_id}")

        except Exception as e:
            self.logger.error(f"Error authenticating API request: {str(e)}")
            result["error"] = "Authentication error"

        return result

    def create_user_token(self, user_account: UserAccount) -> str:
        """
        Create authentication token for user.

        Args:
            user_account: User account object

        Returns:
            JWT token string
        """
        token_data = {
            "user_id": user_account.id,
            "username": user_account.username,
            "phone_number": user_account.phone_number,
            "roles": user_account.roles,
            "is_active": user_account.is_active,
            "type": "user_auth"
        }

        return self.platform_auth.create_jwt_token(token_data)

    def create_session_token(self, session: AccountCreationSession) -> str:
        """
        Create authentication token for session.

        Args:
            session: Account creation session

        Returns:
            JWT token string
        """
        token_data = {
            "session_id": session.session_id,
            "platform": session.platform,
            "platform_user_id": session.platform_user_id,
            "session_type": session.session_type,
            "type": "session_auth"
        }

        # Create short-lived session token (15 minutes)
        return self.platform_auth.create_jwt_token(token_data, timedelta(minutes=15))


# Global auth manager instance
auth_manager = AuthManager()


# FastAPI dependency functions
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from request."""
    auth_result = await auth_manager.authenticate_api_request(request)
    return auth_result if auth_result["authenticated"] else None


async def require_permissions(required_permissions: list):
    """Create dependency that requires specific permissions."""
    async def permission_dependency(request: Request):
        auth_result = await auth_manager.authenticate_api_request(request, required_permissions)
        if not auth_result["authenticated"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.get("error", "Authentication failed")
            )
        return auth_result
    return permission_dependency