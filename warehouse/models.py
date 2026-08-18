from django.db import models


class SyncRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "En ejecucion"
        SUCCESS = "success", "Correcta"
        FAILED = "failed", "Fallida"

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    total_created = models.PositiveIntegerField(default=0)
    total_updated = models.PositiveIntegerField(default=0)
    total_deleted = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.started_at:%Y-%m-%d %H:%M} - {self.status}"


class WarehouseRecord(models.Model):
    resource = models.CharField(max_length=80, db_index=True)
    resource_kind = models.CharField(max_length=20, db_index=True)
    external_id = models.CharField(max_length=120, db_index=True)
    raw_data = models.JSONField()
    normalized_data = models.JSONField()
    row_hash = models.CharField(max_length=64, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    last_sync = models.ForeignKey(SyncRun, related_name="records", on_delete=models.PROTECT)

    class Meta:
        ordering = ["resource", "external_id"]
        constraints = [
            models.UniqueConstraint(fields=["resource", "external_id"], name="uniq_resource_external_id")
        ]
        indexes = [
            models.Index(fields=["resource", "is_active"], name="wh_rec_resource_active_idx"),
            models.Index(fields=["resource_kind", "is_active"], name="wh_rec_kind_active_idx"),
        ]

    def __str__(self):
        return f"{self.resource}:{self.external_id}"


class S360ResourceRecord(models.Model):
    external_id = models.CharField(max_length=120, unique=True, db_index=True)
    raw_data = models.JSONField()
    normalized_data = models.JSONField()
    row_hash = models.CharField(max_length=64, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    last_sync = models.ForeignKey(SyncRun, related_name="%(class)s_records", on_delete=models.PROTECT)

    class Meta:
        abstract = True
        ordering = ["external_id"]

    def __str__(self):
        return self.external_id


class ClienteRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_cliente"


class LineaServicioRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_linea_servicio"


class ContratoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_contrato"


class PreventaRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_preventa"


class SolicitudServicioRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_solicitud_servicio"


class ProspectoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_prospecto"


class EncuestaProspectoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_encuesta_prospecto"


class ConsultaBuroRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_consulta_buro"


class SistemaReferidosRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_sistema_referidos"


class TrazabilidadVentaRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_trazabilidad_venta"


class AgendamientoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_agendamiento"


class OrdenTrabajoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_orden_trabajo"


class TicketTecnicoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_ticket_tecnico"


class TransaccionRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_transaccion"


class AlquilerRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_alquiler"


class UsuarioRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_usuario"


class CanalVentaRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_canal_venta"


class MotivoRechazoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_motivo_rechazo"


class MetodoPagoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_metodo_pago"


class CiudadRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_ciudad"


class ZonaRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_zona"


class SectorRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_sector"


class ConfigPlantillaClienteRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_config_plantilla_cliente"


class PlanInternetRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_plan_internet"


class ProductoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_producto"


class NodoRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_nodo"


class NapRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_nap"


class NapPrimariaRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_nap_primaria"


class AsuntoTicketRecord(S360ResourceRecord):
    class Meta(S360ResourceRecord.Meta):
        db_table = "s360_asunto_ticket"


RESOURCE_MODEL_MAP = {
    "cliente": ClienteRecord,
    "linea-servicio": LineaServicioRecord,
    "contrato": ContratoRecord,
    "preventa": PreventaRecord,
    "solicitud-servicio": SolicitudServicioRecord,
    "prospecto": ProspectoRecord,
    "encuesta-prospecto": EncuestaProspectoRecord,
    "consulta-buro": ConsultaBuroRecord,
    "sistema-referidos": SistemaReferidosRecord,
    "trazabilidad-venta": TrazabilidadVentaRecord,
    "agendamiento": AgendamientoRecord,
    "orden-trabajo": OrdenTrabajoRecord,
    "ticket-tecnico": TicketTecnicoRecord,
    "transaccion": TransaccionRecord,
    "alquiler": AlquilerRecord,
    "usuario": UsuarioRecord,
    "canal-venta": CanalVentaRecord,
    "motivo-rechazo": MotivoRechazoRecord,
    "metodo-pago": MetodoPagoRecord,
    "ciudad": CiudadRecord,
    "zona": ZonaRecord,
    "sector": SectorRecord,
    "config-plantilla-cliente": ConfigPlantillaClienteRecord,
    "plan-internet": PlanInternetRecord,
    "producto": ProductoRecord,
    "nodo": NodoRecord,
    "nap": NapRecord,
    "nap-primaria": NapPrimariaRecord,
    "asunto-ticket": AsuntoTicketRecord,
}
