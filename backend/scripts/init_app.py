"""
Script to initialize the application.
"""

import os
import sys
from app.db import init_db, SessionLocal
from app.models import *
from app.core.logger import configure_logging
from app.core.logger import get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)


def initialize_database():
    """Initialize database tables."""
    try:
        init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(1)


def create_sample_data():
    """Create sample data for development."""
    try:
        db = SessionLocal()

        # Check if data already exists
        from app.models import Tenant
        if db.query(Tenant).first():
            logger.info("Sample data already exists")
            db.close()
            return

        from uuid import uuid4
        from app.auth.utils import hash_password

        # Create sample tenant
        tenant = Tenant(
            id=str(uuid4()),
            name="Demo Tenant",
            slug="demo-tenant",
            description="Sample tenant for testing",
            is_active=True
        )
        db.add(tenant)
        db.commit()

        # Create sample project
        project = Project(
            id=str(uuid4()),
            tenant_id=tenant.id,
            name="Testing Project",
            description="Sample project",
            is_active=True
        )
        db.add(project)
        db.commit()

        # Create sample admin user
        admin = TenantUser(
            id=str(uuid4()),
            tenant_id=tenant.id,
            email="admin@demo.local",
            password_hash=hash_password("admin123"),
            first_name="Admin",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()

        # Create sample API key
        from app.auth.utils import hash_api_key, generate_api_key
        api_key = generate_api_key()
        api_key_obj = APIKey(
            id=str(uuid4()),
            tenant_id=tenant.id,
            project_id=project.id,
            name="demo-key",
            key_hash=hash_api_key(api_key),
            is_active=True
        )
        db.add(api_key_obj)
        db.commit()

        logger.info("Sample data created successfully")
        logger.info(f"Demo Admin Email: admin@demo.local")
        logger.info(f"Demo Admin Password: admin123")
        logger.info(f"Demo API Key: {api_key}")

        db.close()

    except Exception as e:
        logger.error(f"Failed to create sample data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    initialize_database()
    create_sample_data()

    print("\n✓ Application initialized successfully!")
    print("\nNext steps:")
    print("1. Start the application: uvicorn app.main:app --reload")
    print("2. Visit http://localhost:8000/docs for API documentation")
    print("3. Login with credentials printed above")
