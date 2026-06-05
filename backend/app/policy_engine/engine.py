"""
Policy Engine for rule evaluation and enforcement decisions.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models import Policy, UserProfile, Violation
from app.core.constants import EnforcementAction, RiskLevel
from app.core.logger import get_logger

logger = get_logger(__name__)


class PolicyEvaluator:
    """Evaluate policies and determine enforcement actions."""

    def __init__(self, db: Session):
        self.db = db

    def get_tenant_policies(self, tenant_id: str) -> List[Policy]:
        """Get active policies for a tenant."""
        return self.db.query(Policy).filter(
            Policy.tenant_id == tenant_id,
            Policy.is_active == True
        ).all()

    def evaluate_policy(
        self,
        policy: Policy,
        trust_score: float,
        risk_level: RiskLevel,
        violation_count: int
    ) -> Dict[str, Any]:
        """Evaluate a single policy."""
        config = policy.policy_config
        thresholds = config.get("thresholds", {})
        actions = config.get("actions", [])

        matched_actions = []

        # Check thresholds
        if trust_score <= thresholds.get("trust_threshold", 30):
            matched_actions.extend(self._get_actions_for_trigger(actions, "low_trust"))

        if risk_level == RiskLevel.CRITICAL:
            matched_actions.extend(self._get_actions_for_trigger(actions, "critical_risk"))

        if violation_count >= thresholds.get("violation_threshold", 3):
            matched_actions.extend(self._get_actions_for_trigger(actions, "repeat_violator"))

        # Get highest priority action
        final_action = self._select_action(matched_actions) or EnforcementAction.ALLOW

        return {
            "policy_id": policy.id,
            "matched": len(matched_actions) > 0,
            "matched_triggers": [a["trigger"] for a in matched_actions],
            "action": final_action,
            "matched_actions": matched_actions
        }

    def _get_actions_for_trigger(self, actions: List[Dict], trigger: str) -> List[Dict]:
        """Get actions for a specific trigger."""
        return [a for a in actions if a.get("trigger") == trigger]

    def _select_action(self, actions: List[Dict]) -> Optional[EnforcementAction]:
        """Select the most severe action."""
        if not actions:
            return None

        # Priority order
        priority = {
            EnforcementAction.PERMANENT_BAN: 5,
            EnforcementAction.ESCALATE_REVIEW: 4,
            EnforcementAction.TEMP_SUSPEND: 3,
            EnforcementAction.RESTRICT: 2,
            EnforcementAction.WARN: 1,
            EnforcementAction.ALLOW: 0
        }

        selected = max(
            actions,
            key=lambda a: priority.get(a.get("action"), 0)
        )

        return selected.get("action")


class PolicyEngine:
    """Central policy engine for enforcement decisions."""

    def __init__(self, db: Session):
        self.db = db
        self.evaluator = PolicyEvaluator(db)

    def make_enforcement_decision(
        self,
        tenant_id: str,
        user_profile: UserProfile,
        trust_evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make final enforcement decision based on policies."""
        logger.info("Making enforcement decision",
                   tenant_id=tenant_id,
                   user_id=user_profile.id)

        trust_score = trust_evaluation.get("trust_score", 100)
        risk_level = trust_evaluation.get("risk_level", RiskLevel.SAFE)
        violations_detected = trust_evaluation.get("violations_detected", [])

        # Get tenant policies
        policies = self.evaluator.get_tenant_policies(tenant_id)

        if not policies:
            logger.warning("No policies found for tenant", tenant_id=tenant_id)
            return self._default_decision(trust_score, risk_level)

        # Evaluate all policies
        policy_decisions = []
        for policy in policies:
            decision = self.evaluator.evaluate_policy(
                policy,
                trust_score,
                risk_level,
                user_profile.violation_count
            )
            policy_decisions.append(decision)

        # Get most severe action
        final_action = self._select_most_severe_action(policy_decisions)

        # Generate explanation
        explanation = self._generate_explanation(
            trust_score,
            risk_level,
            violations_detected,
            policy_decisions
        )

        result = {
            "action": final_action,
            "trust_score": trust_score,
            "risk_level": risk_level,
            "policy_decisions": policy_decisions,
            "explanation": explanation,
            "requires_review": final_action in [
                EnforcementAction.ESCALATE_REVIEW,
                EnforcementAction.PERMANENT_BAN
            ]
        }

        logger.info("Enforcement decision made",
                   user_id=user_profile.id,
                   action=final_action.value)

        return result

    def _default_decision(self, trust_score: float, risk_level: RiskLevel) -> Dict[str, Any]:
        """Generate default decision when no policies exist."""
        if risk_level == RiskLevel.CRITICAL:
            action = EnforcementAction.ESCALATE_REVIEW
        elif risk_level == RiskLevel.HIGH:
            action = EnforcementAction.WARN
        else:
            action = EnforcementAction.ALLOW

        return {
            "action": action,
            "trust_score": trust_score,
            "risk_level": risk_level,
            "policy_decisions": [],
            "explanation": {
                "trigger": "Default decision (no policies)",
                "reasoning": f"Risk level {risk_level.value}",
                "evidence": []
            },
            "requires_review": False
        }

    def _select_most_severe_action(self, decisions: List[Dict]) -> EnforcementAction:
        """Select most severe action from policy decisions."""
        priority = {
            EnforcementAction.PERMANENT_BAN: 5,
            EnforcementAction.ESCALATE_REVIEW: 4,
            EnforcementAction.TEMP_SUSPEND: 3,
            EnforcementAction.RESTRICT: 2,
            EnforcementAction.WARN: 1,
            EnforcementAction.ALLOW: 0
        }

        max_action = EnforcementAction.ALLOW
        for decision in decisions:
            if decision.get("matched"):
                action = decision.get("action")
                if priority.get(action, 0) > priority.get(max_action, 0):
                    max_action = action

        return max_action

    def _generate_explanation(
        self,
        trust_score: float,
        risk_level: RiskLevel,
        violations: List[Dict],
        policy_decisions: List[Dict]
    ) -> Dict[str, Any]:
        """Generate explanation for the decision."""
        triggers = []
        evidence = []

        if risk_level == RiskLevel.CRITICAL:
            triggers.append(f"Critical risk level detected")
            evidence.append(f"Risk Level: {risk_level.value}")

        if trust_score < 30:
            triggers.append(f"Trust score below threshold")
            evidence.append(f"Trust Score: {trust_score}/100")

        for violation in violations:
            triggers.append(f"Violation detected: {violation.get('category')}")
            evidence.append(f"{violation.get('category')}: {violation.get('score')} confidence")

        return {
            "trigger": " | ".join(triggers) if triggers else "Policy evaluation",
            "reasoning": f"Risk level {risk_level.value} with {len(violations)} violation(s) detected",
            "evidence": evidence
        }
