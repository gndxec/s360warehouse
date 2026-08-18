from django.contrib import admin

from .models import SyncRun, WarehouseRecord


@admin.register(SyncRun)
class SyncRunAdmin(admin.ModelAdmin):
    list_display = ("id", "started_at", "finished_at", "status", "total_created", "total_updated", "total_deleted")
    list_filter = ("status",)
    search_fields = ("error",)


@admin.register(WarehouseRecord)
class WarehouseRecordAdmin(admin.ModelAdmin):
    list_display = ("resource", "external_id", "resource_kind", "is_active", "last_seen_at")
    list_filter = ("resource", "resource_kind", "is_active")
    search_fields = ("external_id",)
