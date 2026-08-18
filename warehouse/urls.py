from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import S360ResourceRecordViewSet, SyncRunViewSet, WarehouseRecordViewSet

router = DefaultRouter()
router.register("records", WarehouseRecordViewSet, basename="records")
router.register("sync-runs", SyncRunViewSet, basename="sync-runs")

s360_resource_list = S360ResourceRecordViewSet.as_view({"get": "list"})
s360_resource_detail = S360ResourceRecordViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("s360/<slug:resource>/", s360_resource_list, name="s360-resource-list"),
    path("s360/<slug:resource>/<int:pk>/", s360_resource_detail, name="s360-resource-detail"),
    *router.urls,
]
