"""
SQLAlchemy models for OmniTrust AI.
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.db import Base
from app.core.constants import (
    UserRole, RiskLevel, EnforcementAction,
    ViolationCategory, ReviewStatus
)


class Tenant(Base):
    """Tenant model for multi-tenancy."""
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata_ = Column(JSON, nullable=True)

    # Relationships
    projects = relationship("Project", back_populates="tenant", cascade="all, delete-orphan")
    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    roles = relationship("TenantRole", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="tenant", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="tenant", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_tenant_slug_active", "slug", "is_active"),
    )


class Project(Base):
    """Project model."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="projects")
    api_keys = relationship("APIKey", back_populates="project", cascade="all, delete-orphan")
    user_profiles = relationship("UserProfile", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_project_tenant_name"),
        Index("idx_project_tenant_active", "tenant_id", "is_active"),
    )


class TenantUser(Base):
    """Tenant user relationship model."""
    __tablename__ = "tenant_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    role = Column(Enum(UserRole), default=UserRole.ANALYST, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_tenant_user_email"),
        Index("idx_tenant_user_email", "email"),
        Index("idx_tenant_user_active", "tenant_id", "is_active"),
    )


class TenantRole(Base):
    """Tenant role model (for custom roles)."""
    __tablename__ = "tenant_roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, nullable=False, default=dict)  # List of permissions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_role_tenant_name"),
    )


class APIKey(Base):
    """API Key model for project authentication."""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_used = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")
    project = relationship("Project", back_populates="api_keys")

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_apikey_project_name"),
        Index("idx_apikey_tenant_active", "tenant_id", "is_active"),
    )


class UserProfile(Base):
    """User profile for content creators/users being evaluated."""
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    external_user_id = Column(String(255), nullable=False)  # ID from client system
    trust_score = Column(Float, default=100.0)
    violation_count = Column(Integer, default=0)
    ban_status = Column(String(50), default="ACTIVE", index=True)  # ACTIVE, SUSPENDED, BANNED
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="user_profiles")
    evaluations = relationship("Evaluation", back_populates="user_profile", cascade="all, delete-orphan")
    violations = relationship("Violation", back_populates="user_profile", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "external_user_id", name="uq_user_profile_external_id"),
        Index("idx_user_profile_ban_status", "project_id", "ban_status"),
        Index("idx_user_profile_trust", "project_id", "trust_score"),
    )


class Evaluation(Base):
    """Content evaluation record."""
    __tablename__ = "evaluations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    content_type = Column(String(50), nullable=False)  # text, image, audio, video, document
    trust_score = Column(Float, nullable=False)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    action = Column(Enum(EnforcementAction), nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(JSON, nullable=False)  # Detailed explanation
    raw_analysis = Column(JSON, nullable=False)  # Raw analysis results
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user_profile = relationship("UserProfile", back_populates="evaluations")
    violations = relationship("Violation", back_populates="evaluation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_evaluation_user_profile", "user_profile_id", "created_at"),
        Index("idx_evaluation_risk_level", "risk_level"),
        Index("idx_evaluation_action", "action"),
    )


class Violation(Base):
    """Policy violation record."""
    __tablename__ = "violations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, index=True)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=True, index=True)
    category = Column(Enum(ViolationCategory), nullable=False, index=True)
    severity = Column(String(50), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    evidence = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user_profile = relationship("UserProfile", back_populates="violations")
    evaluation = relationship("Evaluation", back_populates="violations")

    __table_args__ = (
        Index("idx_violation_user_profile", "user_profile_id", "created_at"),
        Index("idx_violation_category_severity", "category", "severity"),
    )


class EnforcementAction_(Base):
    """Enforcement action taken."""
    __tablename__ = "enforcement_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, index=True)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False, index=True)
    action = Column(Enum(EnforcementAction), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    duration = Column(String(50), nullable=True)  # For TEMP_SUSPEND
    applied_by = Column(String(255), nullable=True)  # moderator/system
    applied_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, REVOKED, EXPIRED

    __table_args__ = (
        Index("idx_enforcement_user_profile", "user_profile_id", "applied_at"),
    )


class Policy(Base):
    """Tenant policy configuration."""
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    policy_config = Column(JSON, nullable=False)  # Threshold and rule definitions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="policies")

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_policy_tenant_name"),
    )


class ReviewQueue(Base):
    """Human review queue."""
    __tablename__ = "review_queue"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False, unique=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.PENDING, index=True)
    priority = Column(Integer, default=0)
    assignee = Column(String(255), nullable=True)  # User who reviewed
    notes = Column(Text, nullable=True)
    decision = Column(Enum(EnforcementAction), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    """Audit log for all important actions."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(255), nullable=True)
    action = Column(String(255), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_log_tenant_action", "tenant_id", "action", "created_at"),
        Index("idx_audit_log_resource", "resource_type", "resource_id"),
    )


class Notification(Base):
    """Internal notification system."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # high_risk_event, policy_change, review_request
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("idx_notification_user", "tenant_id", "user_id", "is_read"),
    )
