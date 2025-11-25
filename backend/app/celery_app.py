"""
Celery Application Configuration

Celery worker for background task processing (batch de-identification jobs).
"""
import os
from celery import Celery
from app.core.config import settings

# Create Celery application
# Use defaults if not configured (for testing/development)
celery_app = Celery(
    "cogstack_nlp",
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
    include=["app.tasks.deidentification_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (prevent memory leaks)
)

# Task routes
celery_app.conf.task_routes = {
    "app.tasks.deidentification_tasks.*": {"queue": "deidentification"},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-jobs": {
        "task": "app.tasks.deidentification_tasks.cleanup_old_jobs",
        "schedule": 86400.0,  # Run daily
    },
}
