"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.core.logfire_setup import instrument_celery

celery_app = Celery(
    "my_ai_agent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Americas/Los_Angeles",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

celery_app.autodiscover_tasks(["app.worker.tasks"])

celery_app.conf.beat_schedule = {
    "rag-sync-check": {
        "task": "app.worker.tasks.rag_tasks.check_scheduled_syncs",
        "schedule": 60.0,
    },
    "weekly-summary": {
        "task": "weekly_summary.generate_weekly_summary",
        "schedule": crontab(hour=9, minute=0, day_of_week=0),
    },
    "reflection-loop": {
        "task": "reflection.run_reflection_loop",
        "schedule": 1800.0,  # every 30 minutes
    },
    "morning-briefing": {
        "task": "reflection.generate_morning_briefing",
        "schedule": crontab(hour=7, minute=0),
    },
    "weekly-digest": {
        "task": "digest.send_weekly_digest",
        "schedule": crontab(hour=9, minute=0, day_of_week=1),  # Monday 9 AM
    },
}


instrument_celery()
