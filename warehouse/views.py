from rest_framework import filters, mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import RESOURCE_MODEL_MAP, SyncRun, WarehouseRecord
from .resources import RESOURCES
from .serializers import S360ResourceRecordSerializer, SyncRunSerializer, WarehouseRecordSerializer
from .tasks import sync_datawarehouse


class WarehouseRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = WarehouseRecordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["external_id", "resource", "normalized_data"]
    ordering_fields = ["resource", "external_id", "last_seen_at"]
    ordering = ["resource", "external_id"]

    def get_queryset(self):
        queryset = WarehouseRecord.objects.all()
        resource = self.request.query_params.get("resource")
        active = self.request.query_params.get("active")
        if resource:
            queryset = queryset.filter(resource=resource)
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() in {"1", "true", "yes"})
        return queryset

    @action(detail=False, methods=["get"])
    def resources(self, request):
        return Response(RESOURCES)


class S360ResourceRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = S360ResourceRecordSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["external_id", "last_seen_at"]
    ordering = ["external_id"]

    def get_queryset(self):
        resource = self.kwargs["resource"]
        model = RESOURCE_MODEL_MAP[resource]
        queryset = model.objects.all()
        active = self.request.query_params.get("active")
        if active is not None:
            queryset = queryset.filter(is_active=active.lower() in {"1", "true", "yes"})
        return queryset


class SyncRunViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = SyncRun.objects.all()
    serializer_class = SyncRunSerializer

    @action(detail=False, methods=["post"])
    def trigger(self, request):
        task = sync_datawarehouse.delay()
        return Response({"task_id": task.id, "status": "queued"}, status=202)
