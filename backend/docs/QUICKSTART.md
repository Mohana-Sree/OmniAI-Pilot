#!/bin/bash
# OmniTrust AI Quick Start Guide

cat << 'EOF'

╔═════════════════════════════════════════════════════════════╗
║     OmniTrust AI - Quick Start Guide                       ║
╚═════════════════════════════════════════════════════════════╝

## 1. LOCAL DEVELOPMENT (5 minutes)

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (optional, for full stack)
- Git

### Setup

```bash
# Clone repository
git clone <repo> omnitrust
cd omnitrust/backend

# Copy environment template
cp .env.example .env

# Edit .env with your settings (or leave defaults for dev)
nano .env

# Run setup script (creates venv, installs deps)
bash scripts/start.sh

# In new terminal, start the server
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API Documentation
# Visit: http://localhost:8000/docs
```

### First API Call

```bash
# 1. Login (get tokens)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@demo.local",
    "password": "admin123"
  }'

# Response:
# {
#   "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
#   "token_type": "bearer"
# }

# 2. Evaluate content for trust
curl -X POST http://localhost:8000/v1/trust/evaluate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "session_id": "sess456",
    "content": {
      "text": "This is content to evaluate for safety"
    },
    "attachments": []
  }'

# Response:
# {
#   "evaluation_id": "eval789",
#   "trust_score": 85.0,
#   "risk_level": "LOW",
#   "action": "ALLOW",
#   "confidence": 0.92,
#   "explanation": {...}
# }
```

## 2. DOCKER COMPOSE FULL STACK

### One Command Deployment

```bash
cd backend

# Start all services (PostgreSQL, Redis, Elasticsearch, MinIO, App, Workers)
docker-compose up

# The application will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Grafana: http://localhost:3000 (admin/admin)
# - MinIO: http://localhost:9001 (minioadmin/minioadmin)

# To stop
docker-compose down

# To view logs
docker-compose logs -f app
docker-compose logs -f celery_worker
```

## 3. RUNNING TESTS

```bash
# Install test dependencies (already in requirements.txt)

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_auth.py

# Run in watch mode
pip install pytest-watch
ptw
```

## 4. FILE STRUCTURE OVERVIEW

```
backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── api/                 # API route handlers
│   ├── services/            # Business logic
│   ├── repositories/        # Database queries
│   ├── models/              # Pydantic + SQLAlchemy models
│   ├── schemas/             # Request/response schemas
│   ├── auth/                # Authentication utilities
│   ├── middleware/          # Express middleware
│   ├── core/                # Configuration
│   ├── ai/                  # AI orchestration
│   ├── trust_engine/        # Trust scoring
│   ├── policy_engine/       # Policy evaluation
│   ├── workers/             # Celery tasks
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── migrations/              # Database migrations
├── docker/                  # Docker config
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # Full stack config
├── README.md                # Full documentation
├── .env.example             # Environment template
└── alembic.ini              # Migration config
```

## 5. KEY ENDPOINTS

### Authentication
- POST /auth/register       - Register user
- POST /auth/login          - Login user
- POST /auth/refresh        - Refresh access token
- POST /auth/logout         - Logout user
- GET /auth/me              - Get current user

### Trust Evaluation (Main API)
- POST /v1/trust/evaluate   - Evaluate content
- GET /v1/trust/evaluations/{id} - Get evaluation
- GET /v1/trust/users/{id}/evaluations - Get user history

### System
- GET /                     - System info
- GET /health               - Health check
- GET /metrics              - Prometheus metrics

## 6. DATABASE MANAGEMENT

### Run Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Your description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1

# Reset database (development only!)
# Uncomment and run:
# python -c "from app.db import drop_db; drop_db()"
# alembic upgrade head
```

## 7. EDITING CODE

### Add New Service

```python
# app/services/myservice.py
from app.core.logger import get_logger

logger = get_logger(__name__)

class MyService:
    def __init__(self, db):
        self.db = db

    def do_something(self):
        logger.info("Doing something")
        return "result"
```

### Add New API Endpoint

```python
# app/api/myapi.py
from fastapi import APIRouter

router = APIRouter(prefix="/v1/myapi", tags=["myapi"])

@router.get("/example")
async def example():
    return {"message": "Hello"}

# In app/main.py:
from app.api import myapi
app.include_router(myapi.router)
```

### Add New Repository

```python
# app/repositories/mymodel.py
from app.repositories.base import BaseRepository
from app.models import MyModel

class MyModelRepository(BaseRepository[MyModel]):
    def custom_query(self):
        return self.db.query(MyModel).filter(...).all()
```

## 8. COMMON TASKS

### Debug an Issue
```python
# Enable debug logging in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Add logging in code
from app.core.logger import get_logger
logger = get_logger(__name__)
logger.debug("Variable value:", var=value)

# Check logs
docker-compose logs -f app
```

### Add a Database Migration
```bash
# Make changes to models in app/models/__init__.py

# Auto-generate migration
alembic revision --autogenerate -m "Add user status column"

# Review migration in migrations/versions/

# Apply
alembic upgrade head
```

### Deploy Locally with Docker
```bash
docker-compose up --build

# Wait for all services to start (30-60 seconds)

# Initialize database
docker-compose exec app python scripts/init_app.py

# Check status
docker-compose ps
```

## 9. TROUBLESHOOTING

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
uvicorn app.main:app --port 8001
```

### Database Connection Error
```bash
# Check connection string in .env
# Make sure PostgreSQL is running
# For Docker: docker-compose up postgres

# Test connection
python -c "from app.db import engine; print(engine.connect())"
```

### Redis Connection Error
```bash
# For Docker: docker-compose up redis
# For local: redis-server

# Test connection
python -c "import redis; r=redis.from_url('redis://localhost:6379'); print(r.ping())"
```

## 10. NEXT STEPS

1. Read full README.md for detailed documentation
2. Check out /docs endpoint for API documentation
3. Look at tests/ for usage examples
4. Review IMPLEMENTATION.md for service patterns
5. Check DEPLOYMENT.md for production setup

---

Questions? Check the documentation or create an issue.

Happy coding! 🚀

EOF
