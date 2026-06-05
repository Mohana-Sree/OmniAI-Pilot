"""
Core constants and custom exceptions.
"""

from enum import Enum
from typing import Optional


# Risk Levels
class RiskLevel(str, Enum):
    """Risk level classifications."""
    SAFE = "SAFE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Enforcement Actions
class EnforcementAction(str, Enum):
    """Possible enforcement actions."""
    ALLOW = "ALLOW"
    WARN = "WARN"
    RESTRICT = "RESTRICT"
    TEMP_SUSPEND = "TEMP_SUSPEND"
    PERMANENT_BAN = "PERMANENT_BAN"
    ESCALATE_REVIEW = "ESCALATE_REVIEW"


# Violation Categories
class ViolationCategory(str, Enum):
    """Violation categories."""
    TOXICITY = "TOXICITY"
    HARASSMENT = "HARASSMENT"
    HATE_SPEECH = "HATE_SPEECH"
    FRAUD = "FRAUD"
    PHISHING = "PHISHING"
    SCAM = "SCAM"
    THREATS = "THREATS"
    NSFW = "NSFW"
    VIOLENCE = "VIOLENCE"
    MALICIOUS_LINKS = "MALICIOUS_LINKS"
    FAKE_DOCUMENTS = "FAKE_DOCUMENTS"
    OTHER = "OTHER"


# Review Status
class ReviewStatus(str, Enum):
    """Review queue status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# User Roles
class UserRole(str, Enum):
    """User roles in the platform."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    ANALYST = "ANALYST"


# Custom Exceptions
class OmniTrustException(Exception):
    """Base exception for OmniTrust."""
    pass


class AuthenticationError(OmniTrustException):
    """Authentication error."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class AuthorizationError(OmniTrustException):
    """Authorization error."""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message)


class TenantNotFoundError(OmniTrustException):
    """Tenant not found."""
    def __init__(self, tenant_id: str):
        super().__init__(f"Tenant {tenant_id} not found")


class ProjectNotFoundError(OmniTrustException):
    """Project not found."""
    def __init__(self, project_id: str):
        super().__init__(f"Project {project_id} not found")


class UserNotFoundError(OmniTrustException):
    """User not found."""
    def __init__(self, user_id: str):
        super().__init__(f"User {user_id} not found")


class InvalidAPIKeyError(OmniTrustException):
    """Invalid API key."""
    def __init__(self):
        super().__init__("Invalid API key")


class RateLimitExceededError(OmniTrustException):
    """Rate limit exceeded."""
    def __init__(self):
        super().__init__("Rate limit exceeded")


class ValidationError(OmniTrustException):
    """Validation error."""
    def __init__(self, message: str):
        super().__init__(message)
