from rest_framework import serializers

from .models import SyncRun, WarehouseRecord


class WarehouseRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseRecord
        fields = [
            "id",
            "resource",
            "resource_kind",
            "external_id",
            "normalized_data",
            "raw_data",
            "is_active",
            "first_seen_at",
            "last_seen_at",
        ]


class S360ResourceRecordSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    external_id = serializers.CharField()
    normalized_data = serializers.JSONField()
    raw_data = serializers.JSONField()
    is_active = serializers.BooleanField()
    first_seen_at = serializers.DateTimeField()
    last_seen_at = serializers.DateTimeField()


class SyncRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncRun
        fields = [
            "id",
            "started_at",
            "finished_at",
            "status",
            "total_created",
            "total_updated",
            "total_deleted",
            "error",
        ]
