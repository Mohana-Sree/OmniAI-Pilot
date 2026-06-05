"""
Base repository for common CRUD operations.
"""

from typing import TypeVar, Generic, Type, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from app.db import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Generic repository for CRUD operations."""

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def create(self, obj_in: dict) -> T:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_by_id(self, id: Any) -> Optional[T]:
        """Get record by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[dict] = None
    ) -> List[T]:
        """Get all records with pagination and filters."""
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.offset(skip).limit(limit).all()

    def update(self, id: Any, obj_in: dict) -> Optional[T]:
        """Update a record."""
        obj = self.get_by_id(id)
        if not obj:
            return None

        for field, value in obj_in.items():
            if hasattr(obj, field):
                setattr(obj, field, value)

        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, id: Any) -> bool:
        """Delete a record."""
        obj = self.get_by_id(id)
        if not obj:
            return False

        self.db.delete(obj)
        self.db.commit()
        return True

    def count(self, filters: Optional[dict] = None) -> int:
        """Count records."""
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()
