"""
API Key repository with custom queries.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models import APIKey
from app.repositories.base import BaseRepository


class APIKeyRepository(BaseRepository[APIKey]):
    """Repository for APIKey model."""

    def __init__(self, db: Session):
        super().__init__(db, APIKey)

    def get_by_key_hash(self, key_hash: str) -> Optional[APIKey]:
        """Get API key by hash."""
        return self.db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()

    def get_project_keys(self, project_id: str):
        """Get all keys for a project."""
        return self.db.query(APIKey).filter(
            APIKey.project_id == project_id
        ).all()

    def get_tenant_keys(self, tenant_id: str):
        """Get all keys for a tenant."""
        return self.db.query(APIKey).filter(
            APIKey.tenant_id == tenant_id
        ).all()

    def count_active_keys(self, project_id: str) -> int:
        """Count active keys in a project."""
        return self.db.query(APIKey).filter(
            APIKey.project_id == project_id,
            APIKey.is_active == True
        ).count()
