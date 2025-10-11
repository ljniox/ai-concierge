"""
Authentication API Endpoints

Provides authentication endpoints for:
- Code parent authentication (FR-032)
- User profile authentication
- Token refresh

Constitution Principle V: Security (no credential leaks)
Constitution Principle IV: Multi-channel support (WhatsApp/Telegram)
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from ...services.auth_service import get_auth_service
from ...models.base import DatabaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class CodeParentAuthRequest(BaseModel):
    """Request for code parent authentication."""
    telephone: str = Field(..., description="Phone number in E.164 format (e.g., +221770000001)")
    code_parent: str = Field(..., description="Parent code (e.g., CAT-12345 or 1de90)")


class AuthResponse(BaseModel):
    """Successful authentication response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user_id: str = Field(..., description="User UUID")
    role: str = Field(..., description="User role")
    telephone: str = Field(..., description="Authenticated phone number")
    auth_method: str = Field(..., description="Authentication method used")


class UserProfile(BaseModel):
    """User profile information."""
    user_id: str
    nom: str
    prenom: str
    role: str
    telephone: str
    email: Optional[str] = None
    canal_prefere: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        Dict: Token payload with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    auth_service = get_auth_service()
    payload = await auth_service.verify_token(credentials.credentials)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def require_role(required_roles: list):
    """
    Decorator factory to require specific user roles.

    Args:
        required_roles: List of allowed roles

    Returns:
        Dependency function
    """
    async def role_dependency(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = current_user.get('role')
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_roles}, found: {user_role}"
            )
        return current_user

    return role_dependency


@router.post("/code-parent", response_model=AuthResponse, responses={
    200: {"model": AuthResponse, "description": "Authentication successful"},
    400: {"model": ErrorResponse, "description": "Invalid request data"},
    401: {"model": ErrorResponse, "description": "Invalid credentials"},
    429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
})
async def authenticate_code_parent(request: CodeParentAuthRequest) -> AuthResponse:
    """
    Authenticate using legacy code parent system (FR-032).

    Supports hybrid authentication:
    - Legacy parents: Use existing Code_Parent from parents_2 table
    - Phone verification: Matches T_l_phone field in legacy database

    Security Features:
    - Rate limiting: 5 attempts per hour per phone number
    - Secure token generation with JWT
    - Audit logging of authentication attempts

    Args:
        request: Authentication request with phone and code parent

    Returns:
        AuthResponse: JWT token and user information

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Validate phone number format (basic E.164 check)
        if not request.telephone.startswith('+') or len(request.telephone) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format. Use E.164 format (e.g., +221770000001)"
            )

        # Validate code parent format
        if not request.code_parent or len(request.code_parent) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code parent format"
            )

        # Perform authentication
        auth_service = get_auth_service()
        auth_result = await auth_service.authenticate_code_parent(
            telephone=request.telephone,
            code_parent=request.code_parent
        )

        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid phone number or code parent"
            )

        logger.info(f"Code parent authentication successful for {request.telephone}")
        return AuthResponse(**auth_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code parent authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


@router.post("/refresh", response_model=AuthResponse, responses={
    200: {"model": AuthResponse, "description": "Token refreshed successfully"},
    401: {"model": ErrorResponse, "description": "Invalid or expired token"}
})
async def refresh_token(current_user: Dict[str, Any] = Depends(get_current_user)) -> AuthResponse:
    """
    Refresh JWT token for current authenticated user.

    Args:
        current_user: Currently authenticated user from JWT token

    Returns:
        AuthResponse: New JWT token with extended expiration
    """
    try:
        auth_service = get_auth_service()

        # Generate new token with same user data
        token_data = await auth_service._generate_token(
            user_id=current_user['user_id'],
            role=current_user['role'],
            telephone=current_user['telephone'],
            auth_method=current_user['auth_method'],
            **{k: v for k, v in current_user.items() if k not in ['user_id', 'role', 'telephone', 'auth_method', 'exp', 'iat']}
        )

        logger.info(f"Token refreshed for user: {current_user['user_id']}")
        return AuthResponse(**token_data)

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.get("/me", response_model=UserProfile, responses={
    200: {"model": UserProfile, "description": "User profile retrieved successfully"},
    401: {"model": ErrorResponse, "description": "Authentication required"}
})
async def get_current_profile(current_user: Dict[str, Any] = Depends(get_current_user)) -> UserProfile:
    """
    Get current user's profile information.

    Args:
        current_user: Currently authenticated user

    Returns:
        UserProfile: User profile details
    """
    try:
        # Get user profile from database
        from ...database.sqlite_manager import get_sqlite_manager
        manager = get_sqlite_manager()

        query = """
        SELECT user_id, nom, prenom, role, telephone, email, canal_prefere
        FROM profil_utilisateurs
        WHERE user_id = ? AND actif = TRUE
        """

        async with manager.get_connection('catechese') as conn:
            cursor = await conn.execute(query, (current_user['user_id'],))
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )

        user_data = dict(row)
        return UserProfile(**user_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.post("/logout", responses={
    200: {"description": "Logout successful"},
    401: {"model": ErrorResponse, "description": "Authentication required"}
})
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Logout current user.

    Note: Since JWT tokens are stateless, actual token invalidation
    would require a token blacklist or similar mechanism.
    This endpoint logs the logout for audit purposes.

    Args:
        current_user: Currently authenticated user
    """
    try:
        logger.info(f"User logged out: {current_user['user_id']} ({current_user['role']})")
        return {"message": "Logout successful"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/verify-token", responses={
    200: {"description": "Token is valid"},
    401: {"model": ErrorResponse, "description": "Invalid or expired token"}
})
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Verify current JWT token is valid.

    Useful for client applications to check token validity
    before making authenticated requests.

    Args:
        current_user: Currently authenticated user

    Returns:
        Dict: Token validity information
    """
    return {
        "valid": True,
        "user_id": current_user['user_id'],
        "role": current_user['role'],
        "expires_at": current_user.get('exp'),
        "auth_method": current_user.get('auth_method')
    }