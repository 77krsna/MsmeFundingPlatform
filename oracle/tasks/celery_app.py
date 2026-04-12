# oracle/tasks/celery_app.py
"""
Celery application configuration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    'msme_oracle',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'tasks.monitor_gem',
        'tasks.verify_gstn',
        'tasks.process_orders'
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Kolkata',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks (cron-like scheduling)
celery_app.conf.beat_schedule = {
    # Monitor GeM portal every 15 minutes
    'monitor-gem-portal': {
        'task': 'tasks.monitor_gem.scrape_gem_orders',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    # Verify pending GSTN every hour
    'verify-gstn-invoices': {
        'task': 'tasks.verify_gstn.verify_pending_invoices',
        'schedule': crontab(minute=0),  # Every hour
    },
    # Check delivery status daily
    'check-delivery-status': {
        'task': 'tasks.process_orders.check_delivery_status',
        'schedule': crontab(hour=9, minute=0),  # 9 AM daily
    },
    # Reconcile payments twice daily
    'reconcile-payments': {
        'task': 'tasks.process_orders.reconcile_payments',
        'schedule': crontab(hour='9,17', minute=0),  # 9 AM and 5 PM
    },
}

if __name__ == '__main__':
    celery_app.start()