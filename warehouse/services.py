from django.utils import timezone

from .client import DatawarehouseClient
from .dynamic_schema import deactivate_missing_rows, upsert_source_row
from .models import RESOURCE_MODEL_MAP, SyncRun
from .normalization import normalize_record, stable_hash
from .resources import RESOURCES


def record_external_id(row):
    for key in ("uuid", "id", "pk"):
        value = row.get(key)
        if value is not None:
            return str(value)
    return stable_hash(row)


def sync_datawarehouse(resource_names=None, exclude_resource_names=None, continue_on_error=False):
    run = SyncRun.objects.create()
    client = DatawarehouseClient()
    created = updated = 0
    seen_by_resource = {}
    errors = []
    resource_names = set(resource_names or [])
    exclude_resource_names = set(exclude_resource_names or [])

    try:
        for resource in RESOURCES:
            name = resource["name"]
            if resource_names and name not in resource_names:
                continue
            if name in exclude_resource_names:
                continue
            model = RESOURCE_MODEL_MAP[name]
            seen_by_resource[name] = set()
            try:
                for row in client.iter_resource(name):
                    external_id = record_external_id(row)
                    normalized = normalize_record(row)
                    row_hash = stable_hash(normalized)
                    seen_by_resource[name].add(external_id)

                    result = upsert_source_row(model, external_id, row, normalized, row_hash, run.id)
                    if result == "created":
                        created += 1
                    elif result == "updated":
                        updated += 1
            except Exception as exc:
                if not continue_on_error:
                    raise
                errors.append(f"{name}: {exc}")

        deleted = 0
        for resource_name, seen_ids in seen_by_resource.items():
            model = RESOURCE_MODEL_MAP[resource_name]
            deleted += deactivate_missing_rows(model, seen_ids, run.id)

        run.status = SyncRun.Status.FAILED if errors else SyncRun.Status.SUCCESS
        run.finished_at = timezone.now()
        run.total_created = created
        run.total_updated = updated
        run.total_deleted = deleted
        run.error = "\n".join(errors)
        run.save(update_fields=["status", "finished_at", "total_created", "total_updated", "total_deleted", "error"])
        return run
    except Exception as exc:
        run.status = SyncRun.Status.FAILED
        run.finished_at = timezone.now()
        run.error = str(exc)
        run.save(update_fields=["status", "finished_at", "error"])
        raise
