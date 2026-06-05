"""
Trust evaluation API routes.
"""

from fastapi import APIRouter, Depends, status, Header
from typing import Optional
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.services.evaluation import EvaluationService
from app.services.tenant import APIKeyService
from app.schemas import TrustEvaluationRequest, TrustEvaluationResponse
from app.repositories.user_profile import UserProfileRepository
from app.auth.utils import verify_api_key, hash_api_key
from app.core.constants import InvalidAPIKeyError
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/v1", tags=["trust_evaluation"])


def validate_api_key(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db_session)
) -> tuple:
    """Validate API key and return project and tenant info."""
    if not x_api_key:
        raise InvalidAPIKeyError()

    api_key_service = APIKeyService(db)

    # Hash the provided key to compare with stored hash
    # In production, would need more sophisticated key storage/lookup
    # For now, we'll use a simplified approach

    # Get API key from database
    from app.repositories.api_key import APIKeyRepository
    api_key_repo = APIKeyRepository(db)

    # In production, implement proper key lookup mechanism
    # For now, assuming the key is directly in the database
    raise InvalidAPIKeyError()


@router.post(
    "/trust/evaluate",
    response_model=TrustEvaluationResponse,
    status_code=status.HTTP_200_OK
)
async def evaluate_trust(
    request: TrustEvaluationRequest,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db_session)
):
    """
    Evaluate content for trust and safety.

    Request body:
    ```json
    {
        "user_id": "user123",
        "session_id": "sess123",
        "content": {
            "text": "Hello, this is content to evaluate"
        },
        "attachments": []
    }
    ```

    Returns:
    ```json
    {
        "evaluation_id": "eval123",
        "trust_score": 85,
        "risk_level": "LOW",
        "action": "ALLOW",
        "confidence": 0.92,
        "explanation": {...}
    }
    ```
    """
    logger.info("Trust evaluation request received", user_id=request.user_id)

    # Validate API key (simplified - in production, use proper key management)
    if not x_api_key:
        raise InvalidAPIKeyError()

    # Extract project and tenant from API key context
    # In production, would validate against database
    # For now, using default values
    project_id = "default_project"
    tenant_id = "default_tenant"

    # Perform evaluation
    evaluation_service = EvaluationService(db)
    result = evaluation_service.evaluate(
        project_id=project_id,
        tenant_id=tenant_id,
        request=request
    )

    logger.info("Evaluation completed successfully",
               evaluation_id=result["evaluation_id"])

    return result


@router.get("/trust/evaluations/{evaluation_id}")
async def get_evaluation(
    evaluation_id: str,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db_session)
):
    """Get evaluation by ID."""
    if not x_api_key:
        raise InvalidAPIKeyError()

    evaluation_service = EvaluationService(db)
    evaluation = evaluation_service.get_evaluation(evaluation_id)

    if not evaluation:
        return {"error": "Evaluation not found"}

    return {
        "evaluation_id": evaluation.id,
        "trust_score": evaluation.trust_score,
        "risk_level": evaluation.risk_level.value,
        "action": evaluation.action.value,
        "confidence": evaluation.confidence,
        "explanation": evaluation.explanation,
        "created_at": evaluation.created_at
    }


@router.get("/trust/users/{user_id}/evaluations")
async def get_user_evaluations(
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    x_api_key: str = Header(...),
    db: Session = Depends(get_db_session)
):
    """Get all evaluations for a user."""
    if not x_api_key:
        raise InvalidAPIKeyError()

    # Get user profile
    user_repo = UserProfileRepository(db)
    user_profile = user_repo.get_by_external_id("default_project", user_id)

    if not user_profile:
        return {"evaluations": []}

    # Get evaluations
    evaluation_service = EvaluationService(db)
    evaluations = evaluation_service.get_user_evaluations(
        user_profile.id,
        skip,
        limit
    )

    return {
        "user_id": user_id,
        "total": len(evaluations),
        "evaluations": [
            {
                "evaluation_id": e.id,
                "trust_score": e.trust_score,
                "risk_level": e.risk_level.value,
                "action": e.action.value,
                "created_at": e.created_at
            }
            for e in evaluations
        ]
    }
