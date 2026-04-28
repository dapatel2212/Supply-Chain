from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    'shiptrack',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['tasks.tracking_tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
)

celery_app.conf.beat_schedule = {
    'check-active-shipments': {
        'task': 'tasks.tracking_tasks.check_all_active',
        'schedule': crontab(minute='*/15'),
    },
    'update-positions': {
        'task': 'tasks.tracking_tasks.update_positions',
        'schedule': crontab(minute='*/5'),
    },
    'retrain-models-daily': {
        'task': 'tasks.tracking_tasks.retrain_models',
        'schedule': crontab(hour=3, minute=0),
    },
}
