"""
Audit Log repository.
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog model."""

    def __init__(self, db: Session):
        super().__init__(db, AuditLog)

    def get_tenant_logs(self, tenant_id: str, skip: int = 0, limit: int = 100):
        """Get audit logs for a tenant."""
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_action(self, tenant_id: str, action: str):
        """Get logs by action."""
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.action == action
        ).all()

    def get_by_resource(self, resource_type: str, resource_id: str):
        """Get logs by resource."""
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).all()

    def get_by_user(self, tenant_id: str, user_id: str):
        """Get logs for a specific user."""
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).all()

    def get_recent_logs(self, tenant_id: str, hours: int = 24, limit: int = 100):
        """Get recent logs from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id,
            AuditLog.created_at >= cutoff
        ).order_by(AuditLog.created_at.desc()).limit(limit).all()

    def count_tenant_logs(self, tenant_id: str) -> int:
        """Count logs for a tenant."""
        return self.db.query(AuditLog).filter(
            AuditLog.tenant_id == tenant_id
        ).count()
