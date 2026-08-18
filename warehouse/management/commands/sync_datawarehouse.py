from django.core.management.base import BaseCommand

from warehouse.services import sync_datawarehouse


class Command(BaseCommand):
    help = "Sincroniza manualmente todos los recursos del Data Warehouse S360."

    def add_arguments(self, parser):
        parser.add_argument(
            "--resource",
            action="append",
            default=[],
            help="Recurso puntual a sincronizar. Puede repetirse.",
        )
        parser.add_argument(
            "--exclude-resource",
            action="append",
            default=[],
            help="Recurso a excluir de la sincronizacion. Puede repetirse.",
        )
        parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continua con los siguientes recursos si uno falla.",
        )

    def handle(self, *args, **options):
        run = sync_datawarehouse(
            resource_names=options["resource"],
            exclude_resource_names=options["exclude_resource"],
            continue_on_error=options["continue_on_error"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Sync {run.id} finalizada: {run.total_created} creados, "
                f"{run.total_updated} actualizados, {run.total_deleted} desactivados."
            )
        )
