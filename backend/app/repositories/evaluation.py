"""
Evaluation repository with custom queries.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Evaluation, UserProfile
from app.repositories.base import BaseRepository
from app.core.constants import RiskLevel, EnforcementAction


class EvaluationRepository(BaseRepository[Evaluation]):
    """Repository for Evaluation model."""

    def __init__(self, db: Session):
        super().__init__(db, Evaluation)

    def get_by_session(self, session_id: str):
        """Get evaluations by session ID."""
        return self.db.query(Evaluation).filter(
            Evaluation.session_id == session_id
        ).all()

    def get_user_evaluations(
        self,
        user_profile_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """Get evaluations for a user."""
        return self.db.query(Evaluation).filter(
            Evaluation.user_profile_id == user_profile_id
        ).order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()

    def count_user_evaluations(self, user_profile_id: str) -> int:
        """Count evaluations for a user."""
        return self.db.query(Evaluation).filter(
            Evaluation.user_profile_id == user_profile_id
        ).count()

    def get_high_risk_evaluations(
        self,
        skip: int = 0,
        limit: int = 100
    ):
        """Get high risk evaluations."""
        return self.db.query(Evaluation).filter(
            Evaluation.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ).order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()

    def count_high_risk(self) -> int:
        """Count high risk evaluations."""
        return self.db.query(Evaluation).filter(
            Evaluation.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
        ).count()

    def get_evaluations_by_action(self, action: EnforcementAction):
        """Get evaluations by enforcement action."""
        return self.db.query(Evaluation).filter(
            Evaluation.action == action
        ).all()

    def count_by_risk_level(self) -> dict:
        """Count evaluations by risk level."""
        counts = {}
        for level in RiskLevel:
            count = self.db.query(Evaluation).filter(
                Evaluation.risk_level == level
            ).count()
            counts[level.value] = count
        return counts

    def get_recent_evaluations(self, hours: int = 24, limit: int = 100):
        """Get evaluations from last N hours."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Evaluation).filter(
            Evaluation.created_at >= cutoff
        ).order_by(Evaluation.created_at.desc()).limit(limit).all()

    def get_evaluations_by_content_type(
        self,
        content_type: str,
        skip: int = 0,
        limit: int = 100
    ):
        """Get evaluations by content type."""
        return self.db.query(Evaluation).filter(
            Evaluation.content_type == content_type
        ).order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()
