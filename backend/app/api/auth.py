"""
Authentication API routes.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.services.auth import AuthenticationService
from app.schemas import (
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    TokenResponse
)
from app.auth.utils import decode_token, verify_token_type
from app.core.constants import AuthenticationError
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def get_current_user(token: str, db: Session = Depends(get_db_session)):
    """Dependency to get current user from token."""
    if not token:
        raise AuthenticationError("Missing token")

    try:
        payload = decode_token(token)
        if not verify_token_type(token, "access"):
            raise AuthenticationError("Invalid token type")
    except AuthenticationError:
        raise

    auth_service = AuthenticationService(db)
    return auth_service.get_user(payload["sub"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    db: Session = Depends(get_db_session)
):
    """Register a new user."""
    # Extract or create tenant ID  (in production, would be from context)
    tenant_id = request.tenant_id or "default"

    auth_service = AuthenticationService(db)
    user = auth_service.register_user(tenant_id, request)

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLoginRequest,
    db: Session = Depends(get_db_session)
):
    """Authenticate user and return tokens."""
    # Extract tenant ID (in production, would be from context)
    tenant_id = "default"

    auth_service = AuthenticationService(db)
    access_token, refresh_token = auth_service.login(tenant_id, credentials)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db_session)
):
    """Refresh access token."""
    auth_service = AuthenticationService(db)
    access_token = auth_service.refresh_access_token(refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 1800
    }


@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Logout user."""
    auth_service = AuthenticationService(db)
    auth_service.logout(current_user.id)

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user = Depends(get_current_user)
):
    """Get current user profile."""
    return current_user
