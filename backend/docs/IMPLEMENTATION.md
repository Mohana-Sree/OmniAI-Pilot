# OmniTrust AI - Developer Implementation Guide

## Overview

This guide explains how to use and extend OmniTrust AI's core components.

## Service Layer Architecture

The application uses a layered architecture:

```
API Routes (FastAPI)
    ↓
Services (Business Logic)
    ↓
Repositories (Data Access)
    ↓
Database (PostgreSQL)
```

## Core Services

### 1. Authentication Service

```python
from app.services.auth import AuthenticationService
from app.schemas import UserRegisterRequest, UserLoginRequest
from app.db import SessionLocal

db = SessionLocal()
auth_service = AuthenticationService(db)

# Register user
user = auth_service.register_user(
    tenant_id="tenant123",
    user_data=UserRegisterRequest(
        email="user@example.com",
        password="secure_pwd",
        first_name="John",
        last_name="Doe"
    )
)

# Login
access_token, refresh_token = auth_service.login(
    tenant_id="tenant123",
    credentials=UserLoginRequest(
        email="user@example.com",
        password="secure_pwd"
    )
)

# Refresh token
new_access = auth_service.refresh_access_token(refresh_token)

# Get current user
user = auth_service.get_current_user(access_token)
```

### 2. Evaluation Service (Main API)

```python
from app.services.evaluation import EvaluationService
from app.schemas import TrustEvaluationRequest

eval_service = EvaluationService(db)

# Perform trust evaluation
result = eval_service.evaluate(
    project_id="proj123",
    tenant_id="tenant123",
    request=TrustEvaluationRequest(
        user_id="user456",
        session_id="sess789",
        content={"text": "Content to analyze"},
        attachments=[]
    )
)

# Returns:
# {
#   "evaluation_id": "eval123",
#   "trust_score": 85.0,
#   "risk_level": "LOW",
#   "action": "ALLOW",
#   "confidence": 0.92,
#   "explanation": {...},
#   "violations": [],
#   "created_at": "2024-06-05T..."
# }

# Get evaluation history
evals = eval_service.get_user_evaluations(
    user_profile_id="profile123",
    skip=0,
    limit=50
)
```

### 3. Privacy Service

```python
from app.services.privacy import PrivacyService

privacy = PrivacyService()

# Detect PII
pii_found = privacy.detect_pii(
    "Call me at 555-1234 or email john@example.com"
)
# Returns: [
#   {"entity_type": "PHONE_NUMBER", "text": "555-1234", "score": 0.95},
#   {"entity_type": "EMAIL_ADDRESS", "text": "john@example.com", "score": 0.98}
# ]

# Anonymize text
anonymized, pii_details = privacy.anonymize_text(
    "John Smith from NYC works at Google"
)
# Returns: ("[PERSON] from [LOCATION] works at [COMPANY]", [pii_details])

# Sanitize complete content
content = {
    "text": "John's phone: 555-1234",
    "author": "john@example.com"
}
sanitized, pii_info = privacy.sanitize_content(content)

# Strip image metadata
clean_image = privacy.strip_image_metadata(image_bytes)

# Get PII summary
summary = privacy.get_pii_summary(pii_found)
# Returns: {"PHONE_NUMBER": 1, "EMAIL_ADDRESS": 1}
```

### 4. Trust Engine

```python
from app.trust_engine.engine import TrustEngine, TrustCalculator

trust_engine = TrustEngine(db)
calculator = trust_engine.calculator

# Evaluate trust based on analysis
evaluation = trust_engine.evaluate_trust(
    user_profile=user_profile,
    analysis_results=analysis_results
)

# Calculate custom trust score
trust_score = calculator.calculate_trust_score(
    user_profile=user_profile,
    current_violation_scores=[0.8, 0.6],
    time_window_days=30
)

# Get risk level
risk_level = calculator.get_risk_level(trust_score=45.0)
# Returns: RiskLevel.MEDIUM

# Generate report
report = calculator.generate_trust_report(user_profile)
# Returns: {
#   "user_id": "...",
#   "trust_score": 70.0,
#   "risk_level": "MEDIUM",
#   "total_violations": 3,
#   "recent_violations": 1,
#   ...
# }
```

### 5. Policy Engine

```python
from app.policy_engine.engine import PolicyEngine, PolicyEvaluator

policy_engine = PolicyEngine(db)
evaluator = policy_engine.evaluator

# Get tenant policies
policies = evaluator.get_tenant_policies(tenant_id="tenant123")

# Evaluate single policy
result = evaluator.evaluate_policy(
    policy=policies[0],
    trust_score=45.0,
    risk_level=RiskLevel.HIGH,
    violation_count=2
)
# Returns: {
#   "policy_id": "...",
#   "matched": True,
#   "matched_triggers": ["critical_risk", "repeat_violator"],
#   "action": "TEMP_SUSPEND"
# }

# Make enforcement decision
decision = policy_engine.make_enforcement_decision(
    tenant_id="tenant123",
    user_profile=user_profile,
    trust_evaluation=trust_eval_result
)
# Returns: {
#   "action": "WARN",
#   "trust_score": 75.0,
#   "risk_level": "MEDIUM",
#   "explanation": {...},
#   "requires_review": False
# }
```

### 6. AI Orchestration Engine

```python
from app.ai.orchestration import AIOrchestrationEngine

engine = AIOrchestrationEngine()

# Analyze content (auto-routes to appropriate analyzer)
results = engine.analyze_content({
    "text": "Toxic content here",
    "image_data": b"...",
    "audio_data": b"..."
})

# Returns: {
#   "analyses": [...],
#   "merged_scores": {
#     "toxicity": 0.85,
#     "harassment": 0.2,
#     "primary_score": 0.85
#   }
# }

# Determine content type
from app.ai.orchestration import ContentType
content_type = engine.determine_content_type({"text": "..."})
# Returns: ContentType.TEXT
```

## Repository Pattern

### Base Repository Usage

```python
from app.repositories.base import BaseRepository
from app.models import Evaluation

# Generic create, read, update, delete
repo = BaseRepository(db, Evaluation)

# Create
eval = repo.create({
    "id": "eval123",
    "user_profile_id": "prof123",
    "trust_score": 75.0,
    ...
})

# Get by ID
eval = repo.get_by_id("eval123")

# Get all with filters
evals = repo.get_all(
    skip=0,
    limit=100,
    filters={"risk_level": "HIGH"}
)

# Update
repo.update("eval123", {"trust_score": 80.0})

# Delete
repo.delete("eval123")

# Count
count = repo.count({"risk_level": "CRITICAL"})
```

### Specialized Repositories

```python
from app.repositories.evaluation import EvaluationRepository
from app.repositories.user_profile import UserProfileRepository
from app.repositories.tenant import TenantRepository

# Evaluation repository with specialized queries
eval_repo = EvaluationRepository(db)
high_risk = eval_repo.get_high_risk_evaluations()
recent = eval_repo.get_recent_evaluations(hours=24)
by_risk = eval_repo.count_by_risk_level()

# User profile repository
profile_repo = UserProfileRepository(db)
user = profile_repo.get_by_external_id("proj123", "external_user_id")
banned = profile_repo.get_banned_users("proj123")
low_trust = profile_repo.get_low_trust_users("proj123", threshold=30)

# Tenant repository
tenant_repo = TenantRepository(db)
tenant = tenant_repo.get_by_slug("demo-tenant")
active = tenant_repo.get_active_tenants()
```

## Creating Custom Analyzers

Extend the AI orchestration by creating custom analyzers:

```python
from app.ai.orchestration import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    """Custom content analyzer."""

    def analyze(self, content):
        """Analyze content and return structured results."""
        scores = {
            "custom_risk_score": 0.5,
            "custom_category": "normal",
            "detected_items": []
        }

        # Your analysis logic here
        # Could call ML models, APIs, etc.

        return {
            "content_type": "custom",
            "scores": scores,
            "primary_score": 0.5,
            "primary_category": "normal"
        }
```

## Creating Celery Tasks

Add background tasks:

```python
from app.workers.celery_app import celery_app

@celery_app.task(name="app.workers.tasks.analyze_bulk_content")
def analyze_bulk_content(evaluation_ids: list):
    """Analyze multiple evaluations in background."""
    db = SessionLocal()
    try:
        from app.repositories.evaluation import EvaluationRepository

        repo = EvaluationRepository(db)

        for eval_id in evaluation_ids:
            eval = repo.get_by_id(eval_id)
            if eval:
                # Process evaluation
                pass

        return {"processed": len(evaluation_ids)}
    finally:
        db.close()

# Use in code:
# analyze_bulk_content.delay([eval1_id, eval2_id, eval3_id])
```

## Error Handling

```python
from app.core.constants import (
    OmniTrustException,
    AuthenticationError,
    AuthorizationError,
    TenantNotFoundError,
    ProjectNotFoundError,
    ValidationError
)

try:
    tenant = tenant_service.get_tenant(tenant_id)
except TenantNotFoundError as e:
    # Handle tenant not found
    logger.error(f"Tenant error: {e}")

try:
    user = auth_service.login(tenant_id, credentials)
except AuthenticationError as e:
    # Handle auth failure
    logger.warning(f"Auth failed: {e}")

try:
    # Validate input
    if not email or "@" not in email:
        raise ValidationError("Invalid email format")
except ValidationError as e:
    # Handle validation error
    pass
```

## Adding New API Endpoints

```python
# In app/api/custom.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db_session

router = APIRouter(prefix="/v1/custom", tags=["custom"])

@router.get("/example")
async def get_example(
    param1: str,
    db: Session = Depends(get_db_session)
):
    """Custom endpoint."""
    # Your logic here
    return {"result": "example"}

# In app/main.py
from app.api import custom
app.include_router(custom.router)
```

## Testing

```python
# tests/unit/test_custom.py

import pytest

class TestCustomFeature:
    def test_something(self, db, tenant_data):
        """Test custom feature."""
        # Use fixtures: db, tenant_data, user_data, project_data, etc.

        result = my_function(db, tenant_data.id)

        assert result is not None
        assert result.some_property == expected_value
```

## Logging

```python
from app.core.logger import get_logger

logger = get_logger(__name__)

# Log at different levels
logger.debug("Debug info", extra_data=value)
logger.info("Information", user_id=user.id)
logger.warning("Warning condition", error=str(e))
logger.error("Error occurred", exc_info=True)

# Logs are JSON-formatted for easy parsing
# Example: {"level": "INFO", "timestamp": "2024-06-05T...", "message": "...", "user_id": "..."}
```

## Best Practices

1. **Always use dependency injection** - Services receive their dependencies
2. **Use repositories for data access** - Don't use models directly outside services
3. **Handle exceptions explicitly** - Use custom exception types
4. **Log important events** - Use structured logging
5. **Write tests for new features** - Target >80% coverage
6. **Document complex logic** - Add docstrings and comments
7. **Follow naming conventions** - Use snake_case for functions/variables
8. **Keep functions small** - Single responsibility principle
9. **Use type hints** - Help with development and IDE support
10. **Validate input** - Never trust external input

## Performance Tips

1. **Use database indexes** - Already configured in models
2. **Batch operations** - Process multiple items at once
3. **Cache frequently accessed data** - Redis integration ready
4. **Async processing** - Use Celery for long tasks
5. **Query optimization** - Use `select()` instead of full-object queries
6. **Connection pooling** - Configured with SQLAlchemy

## Database Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add new column"

# Review migration in migrations/versions/xxx.py

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

For more details, see README.md and API documentation at `/docs`
