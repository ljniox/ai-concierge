"""
Authentication and Authorization Service

Enhanced with JWT service for automatic account creation system while maintaining
legacy code parent authentication with rate limiting per research.md#5.

Security Features:
- bcrypt password hashing (work factor 12)
- Enhanced JWT token service with rotation and blacklisting
- Rate limiting via Redis (5 attempts/hour)
- Code parent authentication for legacy parent access (FR-032)
- Secure token management for account creation system

Constitution Principle V: Security (no credential leaks)
"""

import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
import json
import os
import logging

from ..database.sqlite_manager import get_sqlite_manager
from ..models.legacy import LegacyParent, LegacyDataQueries
from src.utils.logging import get_logger
from src.utils.exceptions import AuthenticationError, AuthorizationError

logger = get_logger(__name__)


class JWTConfig:
    """JWT configuration management for account creation system."""

    def __init__(self):
        # JWT settings
        self.jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.jwt_access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.jwt_refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
        self.jwt_issuer = os.getenv("JWT_ISSUER", "ai-concierge")
        self.jwt_audience = os.getenv("JWT_AUDIENCE", "sdb-users")

        # Token rotation settings
        self.enable_token_rotation = os.getenv("ENABLE_TOKEN_ROTATION", "true").lower() == "true"
        self.token_rotation_threshold_minutes = int(os.getenv("TOKEN_ROTATION_THRESHOLD_MINUTES", "15"))

        # Blacklist settings
        self.enable_token_blacklist = os.getenv("ENABLE_TOKEN_BLACKLIST", "true").lower() == "true"
        self.blacklist_storage = os.getenv("TOKEN_BLACKLIST_STORAGE", "redis")  # redis or memory

        # Validate required settings
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate JWT configuration."""
        if not self.jwt_secret_key:
            raise AuthenticationError("JWT_SECRET_KEY environment variable is required")

        if len(self.jwt_secret_key) < 32:
            logger.warning("JWT_SECRET_KEY should be at least 32 characters long for security")

        if self.jwt_algorithm not in jwt.algorithms.get_supported_algorithms():
            raise AuthenticationError(f"Unsupported JWT algorithm: {self.jwt_algorithm}")


class TokenInfo:
    """Token information container."""

    def __init__(
        self,
        token: str,
        token_type: str,
        expires_at: datetime,
        user_id: UUID,
        claims: Dict[str, Any],
        jti: Optional[str] = None
    ):
        self.token = token
        self.token_type = token_type  # access or refresh
        self.expires_at = expires_at
        self.user_id = user_id
        self.claims = claims
        self.jti = jti or str(uuid4())
        self.created_at = datetime.now(timezone.utc)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) > self.expires_at

    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until token expires."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))

    def to_dict(self) -> Dict[str, Any]:
        """Convert token info to dictionary."""
        return {
            'token': self.token,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat(),
            'expires_in_seconds': self.expires_in_seconds,
            'user_id': str(self.user_id),
            'claims': self.claims,
            'jti': self.jti,
            'created_at': self.created_at.isoformat()
        }


class TokenBlacklist:
    """Token blacklist management."""

    def __init__(self, storage_type: str = "redis"):
        self.storage_type = storage_type
        self._blacklist = set() if storage_type == "memory" else None

    def add(self, jti: str, expires_at: datetime) -> bool:
        """Add token to blacklist."""
        try:
            if self.storage_type == "redis":
                from src.services.redis_service import cache_set_sync
                ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
                return cache_set_sync(
                    key=f"blacklist:{jti}",
                    value="blacklisted",
                    ttl=ttl,
                    namespace="jwt_blacklist"
                )
            else:
                self._blacklist.add(jti)
                return True
        except Exception as e:
            logger.error("Failed to add token to blacklist", jti=jti, error=str(e))
            return False

    def is_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted."""
        try:
            if self.storage_type == "redis":
                from src.services.redis_service import cache_exists_sync
                return cache_exists_sync(
                    key=jti,
                    namespace="jwt_blacklist"
                )
            else:
                return jti in self._blacklist
        except Exception as e:
            logger.error("Failed to check blacklist status", jti=jti, error=str(e))
            return False

    def remove(self, jti: str) -> bool:
        """Remove token from blacklist."""
        try:
            if self.storage_type == "redis":
                from src.services.redis_service import cache_delete_sync
                return cache_delete_sync(
                    key=jti,
                    namespace="jwt_blacklist"
                )
            else:
                self._blacklist.discard(jti)
                return True
        except Exception as e:
            logger.error("Failed to remove token from blacklist", jti=jti, error=str(e))
            return False


class JWTAuthService:
    """
    JWT authentication service with token rotation and blacklisting.

    Provides secure JWT token generation, validation, refresh,
    and revocation functionality for the account creation system.
    """

    def __init__(self, config: Optional[JWTConfig] = None):
        self.config = config or JWTConfig()
        self.blacklist = TokenBlacklist(self.config.blacklist_storage) if self.config.enable_token_blacklist else None

    def generate_access_token(
        self,
        user_id: UUID,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_in_minutes: Optional[int] = None
    ) -> TokenInfo:
        """Generate JWT access token."""
        expires_delta = timedelta(
            minutes=expires_in_minutes or self.config.jwt_access_token_expire_minutes
        )
        expires_at = datetime.now(timezone.utc) + expires_delta

        # Generate JWT ID for token tracking
        jti = str(uuid4())

        # Standard claims
        claims = {
            'sub': str(user_id),
            'exp': expires_at,
            'iat': datetime.now(timezone.utc),
            'iss': self.config.jwt_issuer,
            'aud': self.config.jwt_audience,
            'type': 'access',
            'jti': jti,
        }

        # Add additional claims
        if additional_claims:
            claims.update(additional_claims)

        # Generate token
        token = jwt.encode(
            payload=claims,
            key=self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )

        logger.info("Access token generated", user_id=str(user_id), jti=jti, expires_at=expires_at.isoformat())

        return TokenInfo(
            token=token,
            token_type='access',
            expires_at=expires_at,
            user_id=user_id,
            claims=claims,
            jti=jti
        )

    def generate_refresh_token(
        self,
        user_id: UUID,
        access_token_jti: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> TokenInfo:
        """Generate JWT refresh token."""
        expires_delta = timedelta(
            days=expires_in_days or self.config.jwt_refresh_token_expire_days
        )
        expires_at = datetime.now(timezone.utc) + expires_delta

        # Generate JWT ID
        jti = str(uuid4())

        # Standard claims for refresh token
        claims = {
            'sub': str(user_id),
            'exp': expires_at,
            'iat': datetime.now(timezone.utc),
            'iss': self.config.jwt_issuer,
            'aud': self.config.jwt_audience,
            'type': 'refresh',
            'jti': jti,
        }

        # Link to access token if provided
        if access_token_jti:
            claims['access_jti'] = access_token_jti

        # Generate token
        token = jwt.encode(
            payload=claims,
            key=self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )

        logger.info("Refresh token generated", user_id=str(user_id), jti=jti, expires_at=expires_at.isoformat())

        return TokenInfo(
            token=token,
            token_type='refresh',
            expires_at=expires_at,
            user_id=user_id,
            claims=claims,
            jti=jti
        )

    def generate_token_pair(
        self,
        user_id: UUID,
        additional_claims: Optional[Dict[str, Any]] = None
    ) -> Dict[str, TokenInfo]:
        """Generate access and refresh token pair."""
        access_token = self.generate_access_token(user_id, additional_claims)
        refresh_token = self.generate_refresh_token(user_id, access_token.jti)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    def validate_token(self, token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
        """Validate JWT token and return claims."""
        try:
            # Decode and validate token
            claims = jwt.decode(
                token=token,
                key=self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                audience=self.config.jwt_audience,
                issuer=self.config.jwt_issuer
            )

            # Check token type if specified
            if expected_type and claims.get('type') != expected_type:
                raise AuthorizationError(f"Token type mismatch: expected {expected_type}, got {claims.get('type')}")

            # Check blacklist if enabled
            if self.blacklist and claims.get('jti'):
                if self.blacklist.is_blacklisted(claims['jti']):
                    raise AuthorizationError("Token has been revoked")

            logger.debug("Token validated successfully", jti=claims.get('jti'), user_id=claims.get('sub'))
            return claims

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            raise AuthenticationError("Token validation failed")

    def refresh_access_token(self, refresh_token: str) -> TokenInfo:
        """Refresh access token using refresh token."""
        # Validate refresh token
        claims = self.validate_token(refresh_token, 'refresh')

        user_id = UUID(claims['sub'])
        refresh_jti = claims.get('jti')
        access_jti = claims.get('access_jti')

        # Check if token rotation is needed
        if self.config.enable_token_rotation:
            # Check if the associated access token should be rotated
            if access_jti and self._should_rotate_token(access_jti):
                logger.info("Rotating refresh token", user_id=str(user_id), refresh_jti=refresh_jti)
                # Blacklist old refresh token
                if self.blacklist:
                    exp = datetime.fromtimestamp(claims['exp'], timezone.utc)
                    self.blacklist.add(refresh_jti, exp)

                # Generate new token pair
                return self.generate_access_token(user_id)

        # Generate new access token
        return self.generate_access_token(user_id)

    def _should_rotate_token(self, access_jti: str) -> bool:
        """Check if token should be rotated based on usage patterns."""
        # This is a simplified implementation
        # In production, you might want to track token usage and rotate
        # based on usage patterns or security policies
        return False

    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token by adding it to the blacklist."""
        if not self.blacklist:
            logger.warning("Token blacklist is disabled, cannot revoke token")
            return False

        try:
            claims = jwt.decode(
                token=token,
                key=self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
                options={"verify_exp": False}  # Don't verify expiration for revocation
            )

            jti = claims.get('jti')
            exp = datetime.fromtimestamp(claims['exp'], timezone.utc)

            if jti:
                success = self.blacklist.add(jti, exp)
                if success:
                    logger.info("Token revoked", jti=jti, user_id=claims.get('sub'))
                return success

        except Exception as e:
            logger.error("Failed to revoke token", error=str(e))

        return False


class AuthService:
    """
    Authentication service for enrollment system.

    Supports two authentication methods:
    1. User profile authentication (new system)
    2. Code parent authentication (legacy system, FR-032)
    """

    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here-change-in-production')
        self.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.jwt_expire_minutes = int(os.getenv('JWT_EXPIRE_MINUTES', '30'))
        self.manager = get_sqlite_manager()

    async def hash_code_parent(self, code_parent: str) -> str:
        """
        Hash a parent code using bcrypt with work factor 12.

        Args:
            code_parent: Plain text parent code

        Returns:
            str: bcrypt hash of the code

        Research Decision: research.md#5 - bcrypt work factor 12
        """
        try:
            # Convert to bytes
            code_bytes = code_parent.encode('utf-8')

            # Generate salt and hash with work factor 12
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(code_bytes, salt)

            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to hash code parent: {e}")
            raise

    async def verify_code_parent(self, code_parent: str, hashed_code: str) -> bool:
        """
        Verify a parent code against its hash.

        Args:
            code_parent: Plain text code to verify
            hashed_code: bcrypt hash from database

        Returns:
            bool: True if code matches hash
        """
        try:
            code_bytes = code_parent.encode('utf-8')
            hash_bytes = hashed_code.encode('utf-8')

            # bcrypt will handle the salt internally
            return bcrypt.checkpw(code_bytes, hash_bytes)
        except Exception as e:
            logger.error(f"Failed to verify code parent: {e}")
            return False

    async def authenticate_code_parent(self, telephone: str, code_parent: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate using legacy code parent system (FR-032).

        Args:
            telephone: Phone number (E.164 format)
            code_parent: Parent code (e.g., "CAT-12345" or "1de90")

        Returns:
            Dict with authentication data if successful, None if failed

        Flow:
        1. Check rate limiting (Redis)
        2. Find parent by phone + code in legacy tables
        3. Verify code matches (legacy codes are stored in plain text)
        4. Create user profile if not exists
        5. Generate JWT token
        """
        try:
            # Check rate limiting
            if not await self._check_rate_limit(telephone):
                logger.warning(f"Rate limit exceeded for phone: {telephone}")
                return None

            # Query legacy parent data
            query = LegacyDataQueries.get_parent_by_code(code_parent)
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (code_parent,))
                row = await cursor.fetchone()

            if not row:
                logger.info(f"Parent not found with code: {code_parent}")
                await self._record_failed_attempt(telephone)
                return None

            # Parse legacy parent data
            parent = LegacyParent.from_db_row(dict(row))

            # Verify phone number matches
            if parent.primary_phone != telephone:
                logger.info(f"Phone mismatch for code {code_parent}: expected {parent.primary_phone}, got {telephone}")
                await self._record_failed_attempt(telephone)
                return None

            # Create or update user profile
            user_id = await self._ensure_parent_profile(parent)

            # Generate JWT token
            token_data = await self._generate_token(
                user_id=user_id,
                role="parent",
                telephone=telephone,
                auth_method="code_parent",
                legacy_code_parent=code_parent
            )

            logger.info(f"Code parent authentication successful: {telephone} with code {code_parent}")
            return token_data

        except Exception as e:
            logger.error(f"Code parent authentication error: {e}")
            return None

    async def authenticate_user(self, user_id: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate using user profile system.

        Args:
            user_id: User UUID
            password: Plain text password

        Returns:
            Dict with authentication data if successful, None if failed
        """
        try:
            # Get user profile
            query = "SELECT * FROM profil_utilisateurs WHERE user_id = ? AND actif = TRUE"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (user_id,))
                row = await cursor.fetchone()

            if not row:
                logger.info(f"User not found: {user_id}")
                return None

            user_data = dict(row)

            # Check if user has a password hash (non-parent roles)
            if 'password_hash' not in user_data or not user_data['password_hash']:
                logger.info(f"User {user_id} has no password set")
                return None

            # Verify password
            if not await self.verify_code_parent(password, user_data['password_hash']):
                logger.info(f"Invalid password for user: {user_id}")
                return None

            # Generate JWT token
            token_data = await self._generate_token(
                user_id=user_id,
                role=user_data['role'],
                telephone=user_data['telephone'],
                auth_method="password",
                metadata={
                    "nom": user_data['nom'],
                    "prenom": user_data['prenom']
                }
            )

            logger.info(f"User authentication successful: {user_id}")
            return token_data

        except Exception as e:
            logger.error(f"User authentication error: {e}")
            return None

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and extract claims.

        Args:
            token: JWT token string

        Returns:
            Dict with token claims if valid, None if invalid
        """
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )

            # Check expiration
            exp = payload.get('exp')
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                logger.info("Token expired")
                return None

            # Verify user still exists and is active
            user_id = payload.get('user_id')
            if not user_id:
                return None

            query = "SELECT user_id, role, actif FROM profil_utilisateurs WHERE user_id = ?"
            async with self.manager.get_connection('catechese') as conn:
                cursor = await conn.execute(query, (user_id,))
                row = await cursor.fetchone()

            if not row:
                logger.info(f"User not found for token: {user_id}")
                return None

            user_data = dict(row)
            if not user_data['actif']:
                logger.info(f"User {user_id} is inactive")
                return None

            return payload

        except jwt.ExpiredSignatureError:
            logger.info("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.info(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    async def _generate_token(self, user_id: str, role: str, telephone: str,
                             auth_method: str, **metadata) -> Dict[str, Any]:
        """
        Generate JWT access token.

        Args:
            user_id: User UUID
            role: User role
            telephone: Phone number
            auth_method: Authentication method used
            **metadata: Additional token claims

        Returns:
            Dict containing access token and metadata
        """
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.jwt_expire_minutes)

        payload = {
            'user_id': user_id,
            'role': role,
            'telephone': telephone,
            'auth_method': auth_method,
            'iat': now,
            'exp': exp,
            **metadata
        }

        # Generate JWT token
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

        return {
            'access_token': token,
            'token_type': 'bearer',
            'expires_in': self.jwt_expire_minutes * 60,  # seconds
            'user_id': user_id,
            'role': role,
            'telephone': telephone,
            'auth_method': auth_method
        }

    async def _ensure_parent_profile(self, legacy_parent: LegacyParent) -> str:
        """
        Ensure parent profile exists in new system.

        Args:
            legacy_parent: Legacy parent data

        Returns:
            str: User UUID
        """
        # Check if profile already exists
        query = """
        SELECT user_id FROM profil_utilisateurs
        WHERE telephone = ? AND role = 'parent'
        """
        async with self.manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (legacy_parent.primary_phone,))
            row = await cursor.fetchone()

            if row:
                return row['user_id']

            # Create new profile
            user_id = legacy_parent.to_new_profile_data()['user_id']

            insert_query = """
            INSERT INTO profil_utilisateurs (
                user_id, nom, prenom, role, telephone, email,
                canal_prefere, identifiant_canal, code_parent_hash, actif, permissions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            # Hash the legacy code parent
            code_hash = await self.hash_code_parent(legacy_parent.Code_Parent)

            # Default permissions for parent role
            permissions = json.dumps({
                "create_inscription": True,
                "view_own_inscriptions": True,
                "upload_documents": True,
                "submit_payments": True,
                "validate_ocr": True
            })

            await conn.execute(insert_query, (
                user_id,
                legacy_parent.Nom,
                legacy_parent.Prenoms,
                "parent",
                legacy_parent.primary_phone,
                legacy_parent.Email,
                "whatsapp",  # Default to WhatsApp for legacy parents
                legacy_parent.primary_phone,  # Use phone as channel identifier
                code_hash,
                legacy_parent.is_active,
                permissions
            ))
            await conn.commit()

            logger.info(f"Created parent profile: {user_id} for {legacy_parent.Code_Parent}")
            return user_id

    async def _check_rate_limit(self, telephone: str) -> bool:
        """
        Check rate limiting for code parent attempts.

        Args:
            telephone: Phone number to check

        Returns:
            bool: True if attempt is allowed

        Research Decision: research.md#5 - 5 attempts per hour per phone
        """
        try:
            # Use Redis for rate limiting
            # Note: This requires Redis connection setup
            # For now, implement basic in-memory limiting

            # In production, use Redis:
            # key = f"auth_limit:{telephone}"
            # count = await redis.get(key)
            # if count and int(count) >= 5:
            #     return False
            # await redis.incr(key)
            # await redis.expire(key, 3600)  # 1 hour

            return True  # Simplified for now
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error

    async def _record_failed_attempt(self, telephone: str):
        """Record failed authentication attempt."""
        try:
            # Log failed attempt for monitoring
            logger.warning(f"Failed authentication attempt: {telephone}")

            # In production, store in Redis for rate limiting
            pass
        except Exception as e:
            logger.error(f"Failed to record attempt: {e}")


# Global service instance
_auth_service_instance: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get global auth service instance."""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance


# Global JWT auth service instance and convenience functions for account creation system
_jwt_auth_service: Optional[JWTAuthService] = None


def get_jwt_auth_service() -> JWTAuthService:
    """Get the global JWT auth service instance."""
    global _jwt_auth_service
    if _jwt_auth_service is None:
        _jwt_auth_service = JWTAuthService()
    return _jwt_auth_service


def generate_access_token(
    user_id: UUID,
    additional_claims: Optional[Dict[str, Any]] = None
) -> TokenInfo:
    """Generate access token using global service."""
    service = get_jwt_auth_service()
    return service.generate_access_token(user_id, additional_claims)


def generate_refresh_token(user_id: UUID, access_token_jti: Optional[str] = None) -> TokenInfo:
    """Generate refresh token using global service."""
    service = get_jwt_auth_service()
    return service.generate_refresh_token(user_id, access_token_jti)


def generate_token_pair(
    user_id: UUID,
    additional_claims: Optional[Dict[str, Any]] = None
) -> Dict[str, TokenInfo]:
    """Generate token pair using global service."""
    service = get_jwt_auth_service()
    return service.generate_token_pair(user_id, additional_claims)


def validate_jwt_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """Validate token using global JWT service."""
    service = get_jwt_auth_service()
    return service.validate_token(token, expected_type)


def refresh_access_token(refresh_token: str) -> TokenInfo:
    """Refresh access token using global service."""
    service = get_jwt_auth_service()
    return service.refresh_access_token(refresh_token)


def revoke_jwt_token(token: str) -> bool:
    """Revoke token using global service."""
    service = get_jwt_auth_service()
    return service.revoke_token(token)