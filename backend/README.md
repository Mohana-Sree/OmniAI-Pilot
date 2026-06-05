# OmniTrust AI - Multimodal Trust & Safety Infrastructure Platform

## Overview

OmniTrust AI is a production-ready, scalable backend platform for trust and safety evaluation of multimodal content. It analyzes text, images, audio, videos, and documents to generate risk scores, trust assessments, and enforces tenant-specific policies.

## Features

✓ **Multimodal Analysis** - Text, Image, Audio, Video, Document processing
✓ **Real-time Risk Assessment** - Instant trust scores and enforcement decisions
✓ **Privacy-First Design** - PII detection and removal using Presidio
✓ **Multi-tenant SaaS** - Complete tenant isolation with RBAC
✓ **Policy Engine** - Configurable policies and enforcement rules
✓ **Trust Engine** - Historical and behavioral trust scoring
✓ **Async Processing** - Celery workers for background tasks
✓ **Full-text Search** - Elasticsearch integration
✓ **Audit Logging** - Immutable records of all actions
✓ **Monitoring** - Prometheus metrics and Grafana dashboards
✓ **JWT Authentication** - Secure API key and token management

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI REST API Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  /auth  │  /trust/evaluate  │  /policies  │  /reviews  │ /admin │
├─────────────────────────────────────────────────────────────────┤
│                   Authentication & Authorization                │
├─────────────────────────────────────────────────────────────────┤
│                      Core Service Layer                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Privacy Service │ AI Orchestration │ Trust Engine         │ │
│  │ Policy Engine   │ Evaluation Service │ Audit Service      │ │
│  └────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                     Repository Layer (DAL)                      │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis Cache  │  MinIO Storage  │  Elasticsearch │
└─────────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Framework | FastAPI | REST API |
| Language | Python 3.12 | Backend logic |
| Database | PostgreSQL | Primary data store |
| Cache | Redis | Session & caching layer |
| Task Queue | Celery + Redis | Async task processing |
| Storage | MinIO | Object storage (S3-compatible) |
| Search | Elasticsearch | Full-text search & analytics |
| ORM | SQLAlchemy 2.0 | Database abstraction |
| Auth | JWT + bcrypt | Authentication & encryption |
| Privacy | Presidio | PII detection & removal |
| AI Models | Whisper, CLIP, YOLO | Multimodal ML models |
| Monitoring | Prometheus + Grafana | Observability |
| Logging | Structlog | Structured logging |
| Testing | Pytest | Unit & integration tests |
| Deployment | Docker Compose | Container orchestration |

## Project Structure

```
backend/
├── app/
│   ├── api/                 # API routes
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── trust.py         # Trust evaluation endpoints
│   │   ├── health.py        # Health check endpoints
│   │   └── __init__.py
│   ├── ai/                  # AI orchestration
│   │   └── orchestration.py # Content type routing and analysis
│   ├── auth/                # Authentication utilities
│   │   └── utils.py         # JWT, bcrypt, token management
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings management
│   │   ├── constants.py     # Enums and exceptions
│   │   ├── errors.py        # Exception handlers
│   │   └── logger.py        # Structured logging
│   ├── db/                  # Database
│   │   └── __init__.py      # SQLAlchemy session & engine
│   ├── middleware/          # Express middleware
│   │   └── __init__.py      # CORS, logging, auth
│   ├── models/              # SQLAlchemy models
│   │   └── __init__.py      # All DB models
│   ├── policy_engine/       # Policy evaluation
│   │   └── engine.py        # Policy rules & enforcement
│   ├── repositories/        # Data access layer
│   │   ├── base.py          # Generic CRUD repository
│   │   ├── tenant.py        # Tenant repository
│   │   ├── user.py          # User repository
│   │   ├── api_key.py       # API key repository
│   │   ├── evaluation.py    # Evaluation repository
│   │   ├── user_profile.py  # User profile repository
│   │   └── audit.py         # Audit log repository
│   ├── schemas/             # Pydantic schemas
│   │   └── __init__.py      # Request/response schemas
│   ├── services/            # Business logic
│   │   ├── auth.py          # Authentication service
│   │   ├── tenant.py        # Tenant/project service
│   │   ├── evaluation.py    # Trust evaluation pipeline
│   │   └── privacy.py       # Privacy & PII service
│   ├── trust_engine/        # Trust scoring
│   │   └── engine.py        # Trust calculation & reporting
│   ├── utils/               # Utilities
│   │   └── common.py        # Helper functions
│   ├── workers/             # Celery tasks
│   │   ├── celery_app.py    # Celery configuration
│   │   └── tasks.py         # Background tasks
│   └── main.py              # FastAPI app entry point
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── migrations/              # Alembic database migrations
├── docker/                  # Docker configuration
│   ├── Dockerfile           # Multi-stage build
│   └── prometheus.yml       # Prometheus config
├── docker-compose.yml       # Full stack orchestration
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Quick Start with Docker Compose

```bash
# Clone and setup
git clone <repo>
cd backend

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# The application will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3000 (admin/admin)
# - MinIO: http://localhost:9001
```

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your local settings

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# In another terminal, start Celery Beat
celery -A app.workers.celery_app beat --loglevel=info
```

## API Endpoints

### Authentication

```bash
# Register user
POST /auth/register
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "tenant_id": "tenant123"
}

# Login
POST /auth/login
{
  "email": "user@example.com",
  "password": "securepassword123"
}

# Refresh token
POST /auth/refresh
{
  "refresh_token": "..."
}

# Get current user
GET /auth/me
Headers: Authorization: Bearer <access_token>

# Logout
POST /auth/logout
Headers: Authorization: Bearer <access_token>
```

### Trust Evaluation (Main API)

```bash
# Evaluate content for trust and safety
POST /v1/trust/evaluate
Headers: X-API-Key: <api_key>
{
  "user_id": "user123",
  "session_id": "sess456",
  "content": {
    "text": "Content to evaluate..."
  },
  "attachments": []
}

Response:
{
  "evaluation_id": "eval789",
  "trust_score": 85.0,
  "risk_level": "LOW",
  "action": "ALLOW",
  "confidence": 0.92,
  "explanation": {
    "trigger": "Content Analysis",
    "reasoning": "Content passed safety checks",
    "evidence": []
  },
  "violations": [],
  "created_at": "2024-06-05T10:30:00Z"
}

# Get evaluation details
GET /v1/trust/evaluations/{evaluation_id}
Headers: X-API-Key: <api_key>

# Get user evaluations
GET /v1/trust/users/{user_id}/evaluations?skip=0&limit=100
Headers: X-API-Key: <api_key>
```

### Health & System

```bash
# Health check
GET /health

# System info
GET /

# Metrics
GET /metrics
```

## Database Schema

### Core Models

**Tenant** - Multi-tenant organization
- Isolates data for each customer
- Contains projects, users, policies

**Project** - Organizational unit within tenant
- Groups evaluations and users
- Has separate API keys

**APIKey** - Authentication for API consumers
- Associated with a project
- Hashed for security

**TenantUser** - User account within tenant
- Email/password authentication
- Role-based access control (RBAC)

**UserProfile** - Content creator being evaluated
- External user ID mapping
- Trust score tracking
- Ban status management

**Evaluation** - Result of trust evaluation
- Content analysis results
- Risk level and enforcement action
- Confidence scores and explanation

**Violation** - Policy violation record
- Category of violation
- Severity level
- Evidence and timestamps

**Policy** - Tenant-specific enforcement rules
- Configurable thresholds
- Enforcement actions
- Conditional rules

**AuditLog** - Immutable action record
- All system actions logged
- User, resource, and timestamp
- IP and user agent tracking

## Trust & Safety Features

### Privacy Engine

```python
from app.services.privacy import PrivacyService

privacy = PrivacyService()

# Detect PII
pii_found = privacy.detect_pii("Call me at 555-1234, John Smith")
# Returns: [{"entity_type": "PHONE_NUMBER", ...}, {"entity_type": "PERSON", ...}]

# Anonymize text
anonymized, pii_info = privacy.anonymize_text("My email is john@example.com")
# Returns: ("My email is [EMAIL]", [{"entity_type": "EMAIL_ADDRESS", ...}])

# Strip image metadata
clean_image = privacy.strip_image_metadata(image_bytes)

# Sanitize full content
sanitized, pii_info = privacy.sanitize_content({"text": "...", "name": "..."})
```

### AI Orchestration

```python
from app.ai.orchestration import AIOrchestrationEngine

engine = AIOrchestrationEngine()

# Route content to appropriate analyzer
results = engine.analyze_content({
    "text": "Harmful content here",
    "image_data": b"...",
    "audio_data": b"..."
})

# Results include:
# - Content-specific analysis results
# - Merged scores
# - Primary risk score
```

### Trust Engine

```python
from app.trust_engine.engine import TrustEngine

trust_engine = TrustEngine(db)

# Calculate trust score
evaluation = trust_engine.evaluate_trust(user_profile, analysis_results)
# Returns: trust_score, risk_level, violations_detected

# Generate trust report
report = trust_engine.calculator.generate_trust_report(user_profile)
```

### Policy Engine

```python
from app.policy_engine.engine import PolicyEngine

policy_engine = PolicyEngine(db)

# Make enforcement decision
decision = policy_engine.make_enforcement_decision(
    tenant_id,
    user_profile,
    trust_evaluation
)
# Returns: action, explanation, requires_review
```

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
DATABASE_POOL_SIZE=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
REDIS_CELERY_URL=redis://localhost:6379/2

# JWT
SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
APP_NAME="OmniTrust AI"
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200

# Celery
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Monitoring
PROMETHEUS_PORT=8001
RATE_LIMIT_PER_MINUTE=60
```

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/unit/test_auth.py

# Specific test
pytest tests/unit/test_auth.py::test_user_registration
```

### Test Structure

```
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_services.py
│   ├── test_trust_engine.py
│   ├── test_policy_engine.py
│   └── test_privacy.py
└── integration/
    ├── test_api_endpoints.py
    ├── test_evaluation_pipeline.py
    └── test_database.py
```

## Deployment

### Production Deployment

```bash
# Build Docker image
docker build -f docker/Dockerfile -t omnitrust-api:latest .

# Start with Docker Compose
docker-compose -f docker-compose.yml up -d

# Apply migrations
docker-compose exec app alembic upgrade head

# Create admin user
docker-compose exec app python -m app.scripts.create_admin
```

### Environment Considerations

1. **Secrets Management** - Use cloud key management (AWS Secrets Manager, Azure Key Vault)
2. **Database Backups** - Enable PostgreSQL automated backups
3. **Rate Limiting** - Configure based on expected throughput
4. **Scaling** - Use container orchestration (Kubernetes, ECS)
5. **SSL/TLS** - Enable HTTPS with valid certificates
6. **Firewall** - Restrict network access to internal services

## Monitoring & Debugging

### Logs

```bash
# View application logs
docker-compose logs -f app

# View specific service
docker-compose logs -f celery_worker

# Query logs with structlog
# Logs are in JSON format for easy parsing
```

### Metrics

- **Prometheus** - http://localhost:9090
- **Grafana** - http://localhost:3000

Key metrics:
- Request latency and throughput
- Model inference times
- Queue depth (Celery)
- Database connection pool
- Cache hit/miss rate

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# In code
from app.core.logger import get_logger
logger = get_logger(__name__)
logger.debug("Debug message", extra_data=value)
```

## Performance Optimization

1. **Caching** - Redis for frequent queries
2. **Database Indexing** - Proper indexes on large tables
3. **Connection Pooling** - SQLAlchemy pool configuration
4. **Async Processing** - Celery for long-running tasks
5. **Model Caching** - Cache loaded ML models in memory

## Security

✓ **JWT Authentication** - Stateless token-based auth
✓ **API Key Hashing** - bcrypt-hashed API keys
✓ **Password Hashing** - bcrypt for user passwords
✓ **SQL Injection Prevention** - SQLAlchemy parameterized queries
✓ **CORS Configuration** - Restricted origin list
✓ **Rate Limiting** - Per-IP, per-key rate limits
✓ **Audit Logging** - All actions logged
✓ **PII Protection** - Automatic detection and removal
✓ **Tenant Isolation** - Complete data separation

## Contributing

1. Create feature branch
2. Write tests for new features
3. Follow code style guidelines
4. Submit pull request

## License

Proprietary - OmniTrust AI

## Support

For issues and questions:
- Create issue on GitHub
- Email: support@omnitrust.ai
