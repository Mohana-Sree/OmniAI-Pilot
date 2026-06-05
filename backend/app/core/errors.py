"""
Error handlers for FastAPI routes.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from app.core.constants import OmniTrustException, AuthenticationError
from app.core.logger import get_logger

logger = get_logger(__name__)


def setup_error_handlers(app: FastAPI):
    """Setup error handlers for the application."""

    @app.exception_handler(OmniTrustException)
    async def omnitrust_exception_handler(request: Request, exc: OmniTrustException):
        """Handle OmniTrust custom exceptions."""
        status_code = status.HTTP_400_BAD_REQUEST

        if isinstance(exc, AuthenticationError):
            status_code = status.HTTP_401_UNAUTHORIZED

        return JSONResponse(
            status_code=status_code,
            content={
                "detail": str(exc),
                "code": exc.__class__.__name__,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning("Validation error", errors=exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error("Unhandled exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "code": "INTERNAL_SERVER_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
