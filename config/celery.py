import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("s360_warehouse")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "sync-datawarehouse-every-30-minutes": {
        "task": "warehouse.tasks.sync_datawarehouse",
        "schedule": crontab(minute="*/30"),
    }
}
