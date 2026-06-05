"""
Evaluation service orchestrating the complete trust evaluation pipeline.
"""

from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import UserProfile, Evaluation, Violation, Project
from app.schemas import TrustEvaluationRequest
from app.repositories.user_profile import UserProfileRepository, ViolationRepository
from app.repositories.evaluation import EvaluationRepository
from app.services.privacy import PrivacyService
from app.ai.orchestration import AIOrchestrationEngine
from app.trust_engine.engine import TrustEngine
from app.policy_engine.engine import PolicyEngine
from app.core.constants import ViolationCategory
from app.core.logger import get_logger

logger = get_logger(__name__)


class EvaluationService:
    """Service for handling trust evaluations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_profile_repo = UserProfileRepository(db)
        self.violation_repo = ViolationRepository(db)
        self.evaluation_repo = EvaluationRepository(db)
        self.privacy_service = PrivacyService()
        self.ai_engine = AIOrchestrationEngine()
        self.trust_engine = TrustEngine(db)
        self.policy_engine = PolicyEngine(db)

    def evaluate(
        self,
        project_id: str,
        tenant_id: str,
        request: TrustEvaluationRequest
    ) -> Dict[str, Any]:
        """Perform complete trust evaluation."""
        logger.info("Starting evaluation",
                   project_id=project_id,
                   user_id=request.user_id)

        # Get or create user profile
        user_profile = self.user_profile_repo.get_by_external_id(
            project_id,
            request.user_id
        )

        if not user_profile:
            user_profile = self._create_user_profile(project_id, request.user_id)

        # Step 1: Privacy processing
        sanitized_content, pii_info = self.privacy_service.sanitize_content(
            request.content
        )

        # Step 2: AI Analysis
        analysis_results = self.ai_engine.analyze_content(sanitized_content)

        # Step 3: Trust evaluation
        trust_evaluation = self.trust_engine.evaluate_trust(
            user_profile,
            analysis_results
        )

        # Step 4: Policy evaluation
        enforcement_decision = self.policy_engine.make_enforcement_decision(
            tenant_id,
            user_profile,
            trust_evaluation
        )

        # Step 5: Store evaluation record
        evaluation = self._store_evaluation(
            user_profile,
            request,
            analysis_results,
            trust_evaluation,
            enforcement_decision,
            pii_info
        )

        # Step 6: Store violations if detected
        if trust_evaluation.get("violations_detected"):
            self._store_violations(user_profile, evaluation, trust_evaluation)

        # Step 7: Update user profile
        self._update_user_profile(user_profile, trust_evaluation, enforcement_decision)

        # Step 8: Prepare response
        response = self._prepare_response(
            evaluation,
            trust_evaluation,
            enforcement_decision
        )

        logger.info("Evaluation completed",
                   evaluation_id=evaluation.id,
                   action=enforcement_decision["action"].value)

        return response

    def _create_user_profile(self, project_id: str, external_user_id: str) -> UserProfile:
        """Create new user profile."""
        profile = UserProfile(
            id=str(uuid4()),
            project_id=project_id,
            external_user_id=external_user_id,
            trust_score=100.0,
            violation_count=0,
            ban_status="ACTIVE"
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        logger.info("User profile created", user_id=profile.id)
        return profile

    def _store_evaluation(
        self,
        user_profile: UserProfile,
        request: TrustEvaluationRequest,
        analysis_results: Dict,
        trust_evaluation: Dict,
        enforcement_decision: Dict,
        pii_info: Dict
    ) -> Evaluation:
        """Store evaluation record."""
        evaluation = Evaluation(
            id=str(uuid4()),
            user_profile_id=user_profile.id,
            session_id=request.session_id,
            content_type=self.ai_engine.determine_content_type(request.content).value,
            trust_score=trust_evaluation["trust_score"],
            risk_level=trust_evaluation["risk_level"],
            action=enforcement_decision["action"],
            confidence=max([v.get("score", 0) for v in trust_evaluation.get("violations_detected", [])] or [0.0]),
            explanation={
                "trigger": enforcement_decision["explanation"]["trigger"],
                "reasoning": enforcement_decision["explanation"]["reasoning"],
                "evidence": enforcement_decision["explanation"]["evidence"]
            },
            raw_analysis={
                "analysis_results": analysis_results,
                "trust_evaluation": trust_evaluation,
                "pii_detected": pii_info
            }
        )

        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)

        return evaluation

    def _store_violations(
        self,
        user_profile: UserProfile,
        evaluation: Evaluation,
        trust_evaluation: Dict
    ):
        """Store violation records."""
        for violation_data in trust_evaluation.get("violations_detected", []):
            violation = Violation(
                id=str(uuid4()),
                user_profile_id=user_profile.id,
                evaluation_id=evaluation.id,
                category=ViolationCategory[violation_data.get("category", "OTHER").upper()],
                severity=violation_data.get("severity", "LOW"),
                evidence={
                    "detected_in": evaluation.content_type,
                    "score": violation_data.get("score", 0)
                }
            )
            self.db.add(violation)

        self.db.commit()

    def _update_user_profile(
        self,
        user_profile: UserProfile,
        trust_evaluation: Dict,
        enforcement_decision: Dict
    ):
        """Update user profile with latest evaluation."""
        user_profile.trust_score = trust_evaluation["trust_score"]
        user_profile.violation_count += len(trust_evaluation.get("violations_detected", []))

        # Update ban status based on enforcement action
        action = enforcement_decision["action"]
        if action.value == "PERMANENT_BAN":
            user_profile.ban_status = "BANNED"
        elif action.value == "TEMP_SUSPEND":
            user_profile.ban_status = "SUSPENDED"

        user_profile.updated_at = datetime.utcnow()
        self.db.commit()

    def _prepare_response(
        self,
        evaluation: Evaluation,
        trust_evaluation: Dict,
        enforcement_decision: Dict
    ) -> Dict[str, Any]:
        """Prepare response for API."""
        return {
            "evaluation_id": evaluation.id,
            "trust_score": evaluation.trust_score,
            "risk_level": evaluation.risk_level.value,
            "action": evaluation.action.value,
            "confidence": evaluation.confidence,
            "explanation": evaluation.explanation,
            "violations": [
                v.get("category", "other") for v in trust_evaluation.get("violations_detected", [])
            ],
            "created_at": evaluation.created_at
        }

    def get_evaluation(self, evaluation_id: str) -> Optional[Evaluation]:
        """Get evaluation by ID."""
        return self.evaluation_repo.get_by_id(evaluation_id)

    def get_user_evaluations(
        self,
        user_profile_id: str,
        skip: int = 0,
        limit: int = 100
    ):
        """Get all evaluations for a user."""
        return self.evaluation_repo.get_user_evaluations(
            user_profile_id,
            skip,
            limit
        )
