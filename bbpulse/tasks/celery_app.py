"""
Celery application configuration.
"""
from celery import Celery
from ..settings import settings
import logging

logger = logging.getLogger(__name__)

# Create Celery instance
celery_app = Celery(
    "bbpulse",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "bbpulse.tasks.document_processing",
        "bbpulse.tasks.email_tasks",
        "bbpulse.tasks.operator_tasks"
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Optional: Configure result backend settings
celery_app.conf.result_expires = 3600  # 1 hour

logger.info("Celery application configured successfully")

