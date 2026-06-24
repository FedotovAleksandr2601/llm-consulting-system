from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "bot_service",
    broker=settings.RABBITMQ_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_default_queue="celery",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)

import app.tasks.llm_tasks  # noqa: F401