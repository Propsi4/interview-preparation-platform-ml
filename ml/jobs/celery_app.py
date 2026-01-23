"""Celery application configuration for background jobs.

Examples
--------
>>> from ml.jobs.celery_app import celery_app
>>> print(celery_app.main)
tasks
"""


from celery import Celery
from ml.config.redis import redis_config

celery_app = Celery("tasks", broker=redis_config.REDIS_URL)
celery_app.conf.update(
    task_ignore_result=True,
    task_acks_late=True,
    worker_concurrency=5,
    worker_prefetch_multiplier=1
)

celery_app.autodiscover_tasks(["ml.jobs.tasks"])
