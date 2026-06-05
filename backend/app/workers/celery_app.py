"""
Celery configuration for background tasks.
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "omnitrust",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes hard limit
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-evaluations": {
        "task": "app.workers.tasks.cleanup_old_evaluations",
        "schedule": crontab(hour=2, minute=0),  # Run daily at 2 AM
    },
    "generate-daily-analytics": {
        "task": "app.workers.tasks.generate_daily_analytics",
        "schedule": crontab(hour=6, minute=0),  # Run daily at 6 AM
    },
    "process-review-queue": {
        "task": "app.workers.tasks.process_review_queue",
        "schedule": crontab(minute="*/5"),  # Run every 5 minutes
    },
}


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f"Request: {self.request!r}")
