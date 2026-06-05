"""
Authentication service for user management.
"""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from uuid import uuid4

from app.models import TenantUser
from app.schemas import UserLoginRequest, UserRegisterRequest
from app.repositories.user import TenantUserRepository
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)
from app.core.constants import (
    AuthenticationError,
    AuthorizationError,
    UserNotFoundError,
    UserRole
)
from app.core.logger import get_logger

logger = get_logger(__name__)


class AuthenticationService:
    """Service for handling authentication."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = TenantUserRepository(db)

    def register_user(
        self,
        tenant_id: str,
        user_data: UserRegisterRequest
    ) -> TenantUser:
        """Register a new user."""
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(tenant_id, user_data.email)
        if existing_user:
            logger.error("User already exists", email=user_data.email, tenant_id=tenant_id)
            raise AuthenticationError("User already exists")

        # Create new user
        user = TenantUser(
            id=str(uuid4()),
            tenant_id=tenant_id,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=UserRole.ANALYST,
            is_active=True
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info("User registered", user_id=user.id, email=user_data.email)
        return user

    def login(
        self,
        tenant_id: str,
        credentials: UserLoginRequest
    ) -> Tuple[str, str]:
        """Authenticate user and return tokens."""
        user = self.user_repo.get_by_email(tenant_id, credentials.email)

        if not user or not user.is_active:
            logger.warning("Login attempt with invalid email", email=credentials.email)
            raise AuthenticationError("Invalid credentials")

        if not verify_password(credentials.password, user.password_hash):
            logger.warning("Login attempt with invalid password", email=credentials.email)
            raise AuthenticationError("Invalid credentials")

        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()

        # Generate tokens
        access_token = create_access_token({
            "sub": user.id,
            "tenant_id": tenant_id,
            "email": user.email,
            "role": user.role.value
        })

        refresh_token = create_refresh_token({
            "sub": user.id,
            "tenant_id": tenant_id,
            "email": user.email
        })

        logger.info("User logged in", user_id=user.id, email=user.email)
        return access_token, refresh_token

    def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token from refresh token."""
        if not verify_token_type(refresh_token, "refresh"):
            logger.warning("Invalid refresh token type")
            raise AuthenticationError("Invalid refresh token")

        try:
            payload = decode_token(refresh_token)
        except AuthenticationError:
            logger.warning("Refresh token decode failed")
            raise

        # Get user from database for current role
        user = self.user_repo.get_by_id(payload["sub"])
        if not user or not user.is_active:
            logger.warning("User not found or inactive during token refresh")
            raise UserNotFoundError(payload["sub"])

        # Create new access token
        access_token = create_access_token({
            "sub": user.id,
            "tenant_id": user.tenant_id,
            "email": user.email,
            "role": user.role.value
        })

        logger.info("Access token refreshed", user_id=user.id)
        return access_token

    def logout(self, user_id: str) -> bool:
        """Logout user (currently a no-op, tokens are stateless)."""
        # In a production system, you might blacklist the token
        logger.info("User logged out", user_id=user_id)
        return True

    def get_user(self, user_id: str) -> TenantUser:
        """Get user by ID."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_current_user(self, token: str) -> TenantUser:
        """Get current user from token."""
        try:
            payload = decode_token(token)
            if not verify_token_type(token, "access"):
                raise AuthenticationError("Invalid token type")
        except AuthenticationError:
            logger.warning("Token decode failed")
            raise

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UserNotFoundError(user_id)

        return user
