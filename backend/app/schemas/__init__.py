"""
Pydantic schemas for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, EmailStr, Field
from app.core.constants import (
    RiskLevel, EnforcementAction, ViolationCategory, UserRole
)


# ============= Authentication Schemas =============

class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    tenant_id: Optional[str] = None


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """User response."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Tenant Schemas =============

class TenantCreate(BaseModel):
    """Create tenant request."""
    name: str
    slug: str
    description: Optional[str] = None


class TenantResponse(BaseModel):
    """Tenant response."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Project Schemas =============

class ProjectCreate(BaseModel):
    """Create project request."""
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= API Key Schemas =============

class APIKeyCreate(BaseModel):
    """Create API key request."""
    name: str
    project_id: str


class APIKeyResponse(BaseModel):
    """API key response."""
    id: str
    name: str
    is_active: bool
    last_used: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class APIKeyDetailResponse(BaseModel):
    """API key detail response (only on creation)."""
    id: str
    name: str
    key: str
    created_at: datetime


# ============= Trust Evaluation Schemas =============

class ContentAttachment(BaseModel):
    """Content attachment."""
    type: str  # image, audio, video, document, etc.
    url: Optional[str] = None
    data: Optional[str] = None  # Base64 encoded


class TrustEvaluationRequest(BaseModel):
    """Trust evaluation request."""
    user_id: str
    session_id: Optional[str] = None
    content: Dict[str, Any]  # Flexible content structure
    attachments: Optional[List[ContentAttachment]] = None


class ExplainabilityDetail(BaseModel):
    """Explainability details."""
    trigger: str
    reasoning: str
    evidence: List[Dict[str, Any]]


class TrustEvaluationResponse(BaseModel):
    """Trust evaluation response."""
    evaluation_id: str
    trust_score: float = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    action: EnforcementAction
    confidence: float = Field(..., ge=0, le=1)
    explanation: ExplainabilityDetail
    violations: Optional[List[str]] = None
    created_at: datetime


# ============= Violation Schemas =============

class ViolationResponse(BaseModel):
    """Violation response."""
    id: str
    user_id: str
    category: ViolationCategory
    severity: str
    evidence: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Policy Schemas =============

class PolicyThreshold(BaseModel):
    """Policy threshold configuration."""
    toxicity_threshold: float = Field(default=80, ge=0, le=100)
    harassment_threshold: float = Field(default=75, ge=0, le=100)
    hate_speech_threshold: float = Field(default=90, ge=0, le=100)
    fraud_threshold: float = Field(default=80, ge=0, le=100)
    nsfw_threshold: float = Field(default=70, ge=0, le=100)


class PolicyAction(BaseModel):
    """Policy action configuration."""
    action: EnforcementAction
    triggers: List[str]  # Violation categories that trigger this action


class PolicyCreate(BaseModel):
    """Create policy request."""
    name: str
    description: Optional[str] = None
    thresholds: PolicyThreshold
    actions: List[PolicyAction]


class PolicyResponse(BaseModel):
    """Policy response."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    policy_config: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Review Queue Schemas =============

class ReviewQueueItem(BaseModel):
    """Review queue item."""
    id: str
    evaluation_id: str
    status: str
    priority: int
    assignee: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewApprovalRequest(BaseModel):
    """Review approval request."""
    decision: EnforcementAction
    notes: Optional[str] = None


# ============= Analytics Schemas =============

class AnalyticsOverview(BaseModel):
    """Analytics overview."""
    total_evaluations: int
    total_bans: int
    total_warnings: int
    total_users: int
    avg_trust_score: float
    risk_distribution: Dict[str, int]


# ============= Error Schemas =============

class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    code: str
    timestamp: datetime


# ============= Health Check =============

class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    database: str = "connected"
    redis: str = "connected"
    elasticsearch: str = "connected"
