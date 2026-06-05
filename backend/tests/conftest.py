"""
Test configuration and fixtures.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.db import Base
from app.core.config import Settings
from app.models import *


@pytest.fixture(scope="session")
def settings():
    """Create test settings."""
    return Settings(
        database_url="sqlite:///:memory:",
        redis_url="redis://localhost:6379/0",
        redis_cache_url="redis://localhost:6379/1",
        redis_celery_url="redis://localhost:6379/2",
        secret_key="test-secret-key-for-testing",
        environment="testing",
        debug=True
    )


@pytest.fixture(scope="session")
def engine(settings):
    """Create test database engine."""
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=None,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(engine):
    """Create test database session."""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def tenant_data(db):
    """Create test tenant."""
    from app.models import Tenant
    from uuid import uuid4

    tenant = Tenant(
        id=str(uuid4()),
        name="Test Tenant",
        slug="test-tenant",
        is_active=True
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def user_data(db, tenant_data):
    """Create test user."""
    from app.models import TenantUser
    from app.auth.utils import hash_password
    from app.core.constants import UserRole
    from uuid import uuid4

    user = TenantUser(
        id=str(uuid4()),
        tenant_id=tenant_data.id,
        email="test@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        role=UserRole.ANALYST,
        is_active=True
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def project_data(db, tenant_data):
    """Create test project."""
    from app.models import Project
    from uuid import uuid4

    project = Project(
        id=str(uuid4()),
        tenant_id=tenant_data.id,
        name="Test Project",
        is_active=True
    )
    db.add(project)
    db.commit()
    return project


@pytest.fixture
def api_key_data(db, tenant_data, project_data):
    """Create test API key."""
    from app.models import APIKey
    from app.auth.utils import hash_api_key
    from uuid import uuid4

    api_key = APIKey(
        id=str(uuid4()),
        tenant_id=tenant_data.id,
        project_id=project_data.id,
        name="test-key",
        key_hash=hash_api_key("test-key-value"),
        is_active=True
    )
    db.add(api_key)
    db.commit()
    return api_key
