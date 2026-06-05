"""
Tenant repository with custom queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant model."""

    def __init__(self, db: Session):
        super().__init__(db, Tenant)

    def get_by_slug(self, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        return self.db.query(Tenant).filter(Tenant.slug == slug).first()

    def get_active_tenants(self, skip: int = 0, limit: int = 100):
        """Get all active tenants."""
        return self.db.query(Tenant).filter(
            Tenant.is_active == True
        ).offset(skip).limit(limit).all()

    def count_active(self) -> int:
        """Count active tenants."""
        return self.db.query(Tenant).filter(Tenant.is_active == True).count()
