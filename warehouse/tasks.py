from celery import shared_task

from .services import sync_datawarehouse as run_sync


@shared_task(name="warehouse.tasks.sync_datawarehouse")
def sync_datawarehouse():
    run = run_sync()
    return {
        "sync_run_id": run.id,
        "created": run.total_created,
        "updated": run.total_updated,
        "deleted": run.total_deleted,
    }
