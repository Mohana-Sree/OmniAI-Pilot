"""
Tenant User repository with custom queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models import TenantUser
from app.repositories.base import BaseRepository


class TenantUserRepository(BaseRepository[TenantUser]):
    """Repository for TenantUser model."""

    def __init__(self, db: Session):
        super().__init__(db, TenantUser)

    def get_by_email(self, tenant_id: str, email: str) -> Optional[TenantUser]:
        """Get user by email within a tenant."""
        return self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.email == email
        ).first()

    def get_active_users(self, tenant_id: str, skip: int = 0, limit: int = 100):
        """Get all active users in a tenant."""
        return self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.is_active == True
        ).offset(skip).limit(limit).all()

    def count_active_users(self, tenant_id: str) -> int:
        """Count active users in a tenant."""
        return self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.is_active == True
        ).count()

    def authenticate(self, tenant_id: str, email: str, password_hash: str) -> Optional[TenantUser]:
        """Authenticate user by email and password."""
        return self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.email == email,
            TenantUser.password_hash == password_hash,
            TenantUser.is_active == True
        ).first()
