"""
Trust Engine for calculating trust scores.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import UserProfile, Evaluation, Violation
from app.core.constants import RiskLevel
from app.core.logger import get_logger

logger = get_logger(__name__)


class TrustCalculator:
    """Calculate trust scores for users."""

    # Weight factors for trust calculation
    BASE_TRUST_SCORE = 100.0
    CURRENT_VIOLATION_WEIGHT = 0.4
    HISTORICAL_WEIGHT = 0.3
    RECENCY_WEIGHT = 0.2
    FREQUENCY_WEIGHT = 0.1

    # Risk level thresholds
    RISK_THRESHOLDS = {
        RiskLevel.SAFE: (80, 100),
        RiskLevel.LOW: (60, 80),
        RiskLevel.MEDIUM: (40, 60),
        RiskLevel.HIGH: (20, 40),
        RiskLevel.CRITICAL: (0, 20)
    }

    def __init__(self, db: Session):
        self.db = db

    def calculate_trust_score(
        self,
        user_profile: UserProfile,
        current_violation_scores: List[float],
        time_window_days: int = 30
    ) -> float:
        """Calculate trust score for a user."""
        score = self.BASE_TRUST_SCORE

        # Get user's violation history
        violations = self.db.query(Violation).filter(
            Violation.user_profile_id == user_profile.id
        ).all()

        # Current violation penalty
        if current_violation_scores:
            current_penalty = max(current_violation_scores) * self.CURRENT_VIOLATION_WEIGHT
            score -= current_penalty

        # Historical violations within time window
        cutoff_date = datetime.utcnow() - timedelta(days=time_window_days)
        recent_violations = [v for v in violations if v.created_at >= cutoff_date]

        if recent_violations:
            historical_penalty = len(recent_violations) * 2 * self.HISTORICAL_WEIGHT
            score -= historical_penalty

        # Recency: More recent violations have higher impact
        if violations:
            latest_violation = max(violations, key=lambda v: v.created_at)
            days_since = (datetime.utcnow() - latest_violation.created_at).days
            if days_since < 7:
                recency_penalty = (7 - days_since) / 7 * 10 * self.RECENCY_WEIGHT
                score -= recency_penalty

        # Frequency: Repeated violations
        if recent_violations:
            frequency_penalty = len(recent_violations) / max(time_window_days, 1) * 20 * self.FREQUENCY_WEIGHT
            score -= frequency_penalty

        # Ensure score is within bounds
        score = max(0, min(100, score))

        return round(score, 2)

    def get_risk_level(self, trust_score: float) -> RiskLevel:
        """Determine risk level from trust score."""
        for level, (min_score, max_score) in self.RISK_THRESHOLDS.items():
            if min_score <= trust_score < max_score:
                return level
        return RiskLevel.CRITICAL

    def generate_trust_report(self, user_profile: UserProfile) -> Dict[str, Any]:
        """Generate detailed trust report."""
        violations = self.db.query(Violation).filter(
            Violation.user_profile_id == user_profile.id
        ).all()

        recent_violations = [v for v in violations if (
            datetime.utcnow() - v.created_at < timedelta(days=30)
        )]

        critical_violations = [v for v in violations if v.severity == "CRITICAL"]

        return {
            "user_id": user_profile.id,
            "trust_score": user_profile.trust_score,
            "risk_level": self.get_risk_level(user_profile.trust_score),
            "total_violations": len(violations),
            "recent_violations": len(recent_violations),
            "critical_violations": len(critical_violations),
            "ban_status": user_profile.ban_status,
            "last_updated": user_profile.updated_at
        }


class TrustEngine:
    """Central trust scoring system."""

    def __init__(self, db: Session):
        self.db = db
        self.calculator = TrustCalculator(db)

    def evaluate_trust(
        self,
        user_profile: UserProfile,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate overall trust based on analysis results."""
        logger.info("Evaluating trust", user_id=user_profile.id)

        # Extract violation scores from analysis
        violation_scores = []
        violations_detected = []

        # Process merged scores
        merged_scores = analysis_results.get("merged_scores", {})
        primary_score = merged_scores.get("primary_score", 0)
        violation_scores.append(primary_score)

        if primary_score > 70:
            violations_detected.append({
                "category": self._determine_violation_category(merged_scores),
                "severity": self._determine_severity(primary_score),
                "score": primary_score
            })

        # Calculate new trust score
        trust_score = self.calculator.calculate_trust_score(
            user_profile,
            violation_scores
        )

        # Determine risk level
        risk_level = self.calculator.get_risk_level(trust_score)

        # Generate evaluation details
        evaluation = {
            "trust_score": trust_score,
            "risk_level": risk_level,
            "violations_detected": violations_detected,
            "analysis_summary": merged_scores,
            "historic_data": {
                "previous_trust_score": user_profile.trust_score,
                "violation_count": user_profile.violation_count,
                "ban_status": user_profile.ban_status
            }
        }

        logger.info("Trust evaluation completed",
                   user_id=user_profile.id,
                   trust_score=trust_score,
                   risk_level=risk_level.value)

        return evaluation

    def _determine_violation_category(self, scores: Dict[str, float]) -> str:
        """Determine primary violation category from scores."""
        categories = {
            "toxicity": scores.get("toxicity", 0),
            "harassment": scores.get("harassment", 0),
            "hate_speech": scores.get("hate_speech", 0),
            "fraud": scores.get("fraud", 0),
            "phishing": scores.get("phishing", 0),
            "scam": scores.get("scam", 0),
            "threats": scores.get("threats", 0),
            "nsfw": scores.get("nsfw", 0),
            "violence": scores.get("violence", 0)
        }

        if categories:
            return max(categories, key=categories.get)
        return "other"

    def _determine_severity(self, score: float) -> str:
        """Determine severity level from score."""
        if score >= 90:
            return "CRITICAL"
        elif score >= 75:
            return "HIGH"
        elif score >= 50:
            return "MEDIUM"
        elif score >= 25:
            return "LOW"
        else:
            return "MINIMAL"
