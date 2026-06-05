"""
Unit tests for authentication service.
"""

import pytest
from app.services.auth import AuthenticationService
from app.schemas import UserRegisterRequest, UserLoginRequest
from app.core.constants import AuthenticationError
from app.auth.utils import verify_password


class TestAuthenticationService:
    """Tests for AuthenticationService."""

    def test_user_registration_success(self, db, tenant_data):
        """Test successful user registration."""
        service = AuthenticationService(db)
        request = UserRegisterRequest(
            email="newuser@example.com",
            password="securepassword123",
            first_name="John",
            last_name="Doe",
            tenant_id=tenant_data.id
        )

        user = service.register_user(tenant_data.id, request)

        assert user.email == "newuser@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert verify_password("securepassword123", user.password_hash)

    def test_user_registration_duplicate_email(self, db, user_data):
        """Test registration with duplicate email."""
        service = AuthenticationService(db)
        request = UserRegisterRequest(
            email="test@example.com",  # Already exists
            password="newpassword123",
            first_name="Jane",
            last_name="Doe",
            tenant_id=user_data.tenant_id
        )

        with pytest.raises(AuthenticationError):
            service.register_user(user_data.tenant_id, request)

    def test_user_login_success(self, db, user_data):
        """Test successful login."""
        service = AuthenticationService(db)
        credentials = UserLoginRequest(
            email="test@example.com",
            password="password123"
        )

        access_token, refresh_token = service.login(user_data.tenant_id, credentials)

        assert access_token is not None
        assert refresh_token is not None

    def test_user_login_invalid_password(self, db, user_data):
        """Test login with invalid password."""
        service = AuthenticationService(db)
        credentials = UserLoginRequest(
            email="test@example.com",
            password="wrongpassword"
        )

        with pytest.raises(AuthenticationError):
            service.login(user_data.tenant_id, credentials)

    def test_user_login_nonexistent_user(self, db, tenant_data):
        """Test login with non-existent user."""
        service = AuthenticationService(db)
        credentials = UserLoginRequest(
            email="nonexistent@example.com",
            password="password123"
        )

        with pytest.raises(AuthenticationError):
            service.login(tenant_data.id, credentials)

    def test_get_user(self, db, user_data):
        """Test getting user by ID."""
        service = AuthenticationService(db)

        user = service.get_user(user_data.id)

        assert user.id == user_data.id
        assert user.email == user_data.email

    def test_token_refresh(self, db, user_data):
        """Test token refresh."""
        service = AuthenticationService(db)

        # First, login to get tokens
        credentials = UserLoginRequest(
            email="test@example.com",
            password="password123"
        )
        access_token, refresh_token = service.login(user_data.tenant_id, credentials)

        # Now refresh the token
        new_access_token = service.refresh_access_token(refresh_token)

        assert new_access_token is not None
        assert new_access_token != access_token
