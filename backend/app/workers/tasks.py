"""
Celery background tasks.
"""

from datetime import datetime, timedelta
from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.models import Evaluation, ReviewQueue
from app.core.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(name="app.workers.tasks.cleanup_old_evaluations")
def cleanup_old_evaluations(days: int = 90):
    """Clean up old evaluations."""
    db = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old evaluations
        old_evaluations = db.query(Evaluation).filter(
            Evaluation.created_at < cutoff_date
        ).all()

        count = len(old_evaluations)
        for eval in old_evaluations:
            db.delete(eval)

        db.commit()
        logger.info(f"Cleaned up {count} evaluations older than {days} days")
        return {"deleted": count}

    except Exception as e:
        logger.error(f"Error cleaning up evaluations: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.generate_daily_analytics")
def generate_daily_analytics():
    """Generate daily analytics."""
    db = SessionLocal()
    try:
        # Get today's evaluations
        today = datetime.utcnow().date()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())

        evaluations = db.query(Evaluation).filter(
            Evaluation.created_at >= start,
            Evaluation.created_at <= end
        ).all()

        # Calculate analytics
        analytics = {
            "date": str(today),
            "total_evaluations": len(evaluations),
            "high_risk": len([e for e in evaluations if e.risk_level.value == "HIGH"]),
            "critical": len([e for e in evaluations if e.risk_level.value == "CRITICAL"]),
            "avg_trust_score": sum(e.trust_score for e in evaluations) / len(evaluations) if evaluations else 0
        }

        logger.info(f"Generated daily analytics: {analytics}")
        return analytics

    except Exception as e:
        logger.error(f"Error generating daily analytics: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.process_review_queue")
def process_review_queue():
    """Process items in review queue."""
    db = SessionLocal()
    try:
        # Get pending reviews
        pending_reviews = db.query(ReviewQueue).filter(
            ReviewQueue.status == "PENDING"
        ).all()

        logger.info(f"Processing {len(pending_reviews)} pending reviews")
        return {"processed": len(pending_reviews)}

    except Exception as e:
        logger.error(f"Error processing review queue: {e}")
        raise
    finally:
        db.close()
