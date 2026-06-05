"""
Database configuration and utilities.
"""

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool
from app.core.config import get_settings

settings = get_settings()

# SQLAlchemy base model
Base = declarative_base()


def get_engine() -> Engine:
    """Create database engine with connection pooling."""
    engine_args = {
        "poolclass": QueuePool,
        "pool_size": settings.database_pool_size,
        "max_overflow": settings.database_max_overflow,
        "echo": settings.database_echo,
        "future": True,
    }

    # Only add connect_args for PostgreSQL, not SQLite
    if "postgresql" in settings.database_url:
        engine_args["connect_args"] = {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000"  # 30 seconds
        }

    return create_engine(settings.database_url, **engine_args)


# Create engine
engine = get_engine()

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
    autoflush=False
)


def get_db_session() -> Session:
    """Get database session.

    Used as dependency injection in FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all tables."""
    Base.metadata.drop_all(bind=engine)
