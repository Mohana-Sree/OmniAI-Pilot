"""
User Profile and Violation repositories.
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models import UserProfile, Violation, ViolationCategory
from app.repositories.base import BaseRepository


class UserProfileRepository(BaseRepository[UserProfile]):
    """Repository for UserProfile model."""

    def __init__(self, db: Session):
        super().__init__(db, UserProfile)

    def get_by_external_id(self, project_id: str, external_user_id: str) -> Optional[UserProfile]:
        """Get user profile by external user ID."""
        return self.db.query(UserProfile).filter(
            UserProfile.project_id == project_id,
            UserProfile.external_user_id == external_user_id
        ).first()

    def get_banned_users(self, project_id: str):
        """Get all banned users in a project."""
        return self.db.query(UserProfile).filter(
            UserProfile.project_id == project_id,
            UserProfile.ban_status == "BANNED"
        ).all()

    def count_banned(self, project_id: str) -> int:
        """Count banned users in a project."""
        return self.db.query(UserProfile).filter(
            UserProfile.project_id == project_id,
            UserProfile.ban_status == "BANNED"
        ).count()

    def get_low_trust_users(self, project_id: str, threshold: float = 30):
        """Get users with low trust score."""
        return self.db.query(UserProfile).filter(
            UserProfile.project_id == project_id,
            UserProfile.trust_score < threshold
        ).all()

    def get_violators(self, project_id: str, min_violations: int = 1):
        """Get users with violations."""
        return self.db.query(UserProfile).filter(
            UserProfile.project_id == project_id,
            UserProfile.violation_count >= min_violations
        ).all()


class ViolationRepository(BaseRepository[Violation]):
    """Repository for Violation model."""

    def __init__(self, db: Session):
        super().__init__(db, Violation)

    def get_user_violations(self, user_profile_id: str):
        """Get all violations for a user."""
        return self.db.query(Violation).filter(
            Violation.user_profile_id == user_profile_id
        ).all()

    def count_user_violations(self, user_profile_id: str) -> int:
        """Count violations for a user."""
        return self.db.query(Violation).filter(
            Violation.user_profile_id == user_profile_id
        ).count()

    def get_by_category(self, category: ViolationCategory):
        """Get violations by category."""
        return self.db.query(Violation).filter(
            Violation.category == category
        ).all()

    def count_by_category(self, category: ViolationCategory) -> int:
        """Count violations by category."""
        return self.db.query(Violation).filter(
            Violation.category == category
        ).count()

    def get_critical_violations(self):
        """Get all critical violations."""
        return self.db.query(Violation).filter(
            Violation.severity == "CRITICAL"
        ).all()
