"""
Core services for tenant and project management.
"""

from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.models import Tenant, Project, APIKey
from app.repositories.tenant import TenantRepository
from app.repositories.api_key import APIKeyRepository
from app.core.constants import TenantNotFoundError, ProjectNotFoundError, ValidationError
from app.auth.utils import hash_api_key, generate_api_key
from app.core.logger import get_logger

logger = get_logger(__name__)


class TenantService:
    """Service for managing tenants."""

    def __init__(self, db: Session):
        self.db = db
        self.tenant_repo = TenantRepository(db)

    def create_tenant(self, name: str, slug: str, description: Optional[str] = None) -> Tenant:
        """Create a new tenant."""
        # Validate slug
        if not slug or not slug.isalnum() and "-" not in slug:
            raise ValidationError("Invalid slug format")

        # Check if slug already exists
        existing = self.tenant_repo.get_by_slug(slug)
        if existing:
            raise ValidationError(f"Slug '{slug}' already exists")

        tenant = Tenant(
            id=str(uuid4()),
            name=name,
            slug=slug,
            description=description,
            is_active=True
        )

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        logger.info("Tenant created", tenant_id=tenant.id, slug=slug)
        return tenant

    def get_tenant(self, tenant_id: str) -> Tenant:
        """Get tenant by ID."""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        return tenant

    def get_tenant_by_slug(self, slug: str) -> Tenant:
        """Get tenant by slug."""
        tenant = self.tenant_repo.get_by_slug(slug)
        if not tenant:
            raise TenantNotFoundError(slug)
        return tenant

    def list_tenants(self, skip: int = 0, limit: int = 100) -> List[Tenant]:
        """List all active tenants."""
        return self.tenant_repo.get_active_tenants(skip, limit)

    def update_tenant(self, tenant_id: str, **kwargs) -> Tenant:
        """Update tenant."""
        tenant = self.get_tenant(tenant_id)
        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        self.db.commit()
        self.db.refresh(tenant)

        logger.info("Tenant updated", tenant_id=tenant_id)
        return tenant

    def deactivate_tenant(self, tenant_id: str) -> Tenant:
        """Deactivate a tenant."""
        return self.update_tenant(tenant_id, is_active=False)


class ProjectService:
    """Service for managing projects."""

    def __init__(self, db: Session):
        self.db = db

    def create_project(self, tenant_id: str, name: str, description: Optional[str] = None) -> Project:
        """Create a new project."""
        tenant_service = TenantService(self.db)
        tenant_service.get_tenant(tenant_id)  # Verify tenant exists

        project = Project(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            is_active=True
        )

        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        logger.info("Project created", project_id=project.id, tenant_id=tenant_id)
        return project

    def get_project(self, project_id: str) -> Project:
        """Get project by ID."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ProjectNotFoundError(project_id)
        return project

    def list_tenant_projects(self, tenant_id: str) -> List[Project]:
        """List all projects for a tenant."""
        return self.db.query(Project).filter(
            Project.tenant_id == tenant_id,
            Project.is_active == True
        ).all()

    def update_project(self, project_id: str, **kwargs) -> Project:
        """Update project."""
        project = self.get_project(project_id)
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)

        self.db.commit()
        self.db.refresh(project)

        logger.info("Project updated", project_id=project_id)
        return project


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, db: Session):
        self.db = db
        self.api_key_repo = APIKeyRepository(db)

    def create_api_key(self, tenant_id: str, project_id: str, name: str) -> tuple[APIKey, str]:
        """Create a new API key."""
        project_service = ProjectService(self.db)
        project = project_service.get_project(project_id)

        # Generate API key
        api_key = generate_api_key()
        key_hash = hash_api_key(api_key)

        db_key = APIKey(
            id=str(uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            name=name,
            key_hash=key_hash,
            is_active=True
        )

        self.db.add(db_key)
        self.db.commit()
        self.db.refresh(db_key)

        logger.info("API key created", key_id=db_key.id, project_id=project_id)
        return db_key, api_key  # Return both DB object and plaintext key

    def get_api_key(self, key_id: str) -> APIKey:
        """Get API key by ID."""
        key = self.api_key_repo.get_by_id(key_id)
        if not key:
            raise ValidationError("API key not found")
        return key

    def validate_api_key(self, key_hash: str) -> Optional[APIKey]:
        """Validate API key by hash."""
        return self.api_key_repo.get_by_key_hash(key_hash)

    def list_project_keys(self, project_id: str) -> List[APIKey]:
        """List all keys for a project."""
        return self.api_key_repo.get_project_keys(project_id)

    def revoke_api_key(self, key_id: str) -> APIKey:
        """Revoke an API key."""
        key = self.get_api_key(key_id)
        key.is_active = False
        self.db.commit()
        self.db.refresh(key)

        logger.info("API key revoked", key_id=key_id)
        return key

    def delete_api_key(self, key_id: str) -> bool:
        """Delete an API key."""
        key = self.get_api_key(key_id)
        self.db.delete(key)
        self.db.commit()

        logger.info("API key deleted", key_id=key_id)
        return True
