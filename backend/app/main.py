"""
Main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from prometheus_client import make_asgi_app

from app.core.config import get_settings
from app.core.logger import configure_logging
from app.core.errors import setup_error_handlers
from app.middleware import setup_middleware
from app.db import init_db
from app.api import auth, trust, health

settings = get_settings()

# Configure logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Multimodal Trust & Safety Infrastructure Platform",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Setup middleware
setup_middleware(app)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Setup error handlers
setup_error_handlers(app)

# Health check should be routed to separate app
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(trust.router)

# Initialize database
@app.on_event("startup")
async def startup():
    """Initialize database on startup."""
    try:
        init_db()
        print(f"[OK] Database initialized")
        print(f"[OK] OmniTrust AI {settings.app_version} started in {settings.environment} mode")
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    print("[OK] OmniTrust AI shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
