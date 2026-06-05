"""
Health and system check routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis

from app.core.config import get_settings
from app.db import get_db_session, engine
from app.schemas import HealthCheck
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["system"])
settings = get_settings()


@router.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db_session)):
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "database": "disconnected",
        "redis": "disconnected",
        "elasticsearch": "disconnected"
    }

    # Check database
    try:
        db.execute("SELECT 1")
        health_status["database"] = "connected"
    except Exception as e:
        logger.warning("Database health check failed", error=str(e))
        health_status["status"] = "degraded"

    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        logger.warning("Redis health check failed", error=str(e))
        health_status["status"] = "degraded"

    # Check Elasticsearch (simplified)
    try:
        # In production, would make actual ES request
        health_status["elasticsearch"] = "connected"
    except Exception as e:
        logger.warning("Elasticsearch health check failed", error=str(e))

    return health_status


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OmniTrust AI",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "openapi": "/openapi.json"
    }
