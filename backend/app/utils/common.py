"""
Utility functions.
"""

from typing import Any, Dict, List
import json
from datetime import datetime


def serialize_datetime(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.decode('utf-8')
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def to_dict(obj: Any) -> Dict:
    """Convert SQLAlchemy model to dict."""
    if hasattr(obj, '__dict__'):
        return {
            c.name: getattr(obj, c.name)
            for c in obj.__table__.columns
        }
    return {}


def paginate(items: List, skip: int = 0, limit: int = 100) -> Dict:
    """Paginate a list of items."""
    total = len(items)
    paginated = items[skip:skip + limit]

    return {
        "items": paginated,
        "total": total,
        "skip": skip,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


def get_ip_from_request(request) -> str:
    """Extract IP address from request."""
    if request.client:
        return request.client.host
    return "unknown"


def get_user_agent_from_request(request) -> str:
    """Extract user agent from request."""
    return request.headers.get("user-agent", "unknown")
