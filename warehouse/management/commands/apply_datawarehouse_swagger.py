from django.core.management.base import BaseCommand, CommandError

from warehouse.swagger_schema import apply_datawarehouse_schema, extract_datawarehouse_schema, load_swagger


class Command(BaseCommand):
    help = "Crea columnas fisicas en tablas s360_* desde el Swagger/OpenAPI de Data Warehouse."

    def add_arguments(self, parser):
        parser.add_argument("swagger_path", help="Ruta local al archivo Swagger/OpenAPI JSON o JSONC.")

    def handle(self, *args, **options):
        try:
            swagger = load_swagger(options["swagger_path"])
        except Exception as exc:
            raise CommandError(f"No se pudo leer el Swagger: {exc}") from exc

        resources = extract_datawarehouse_schema(swagger)
        if not resources:
            raise CommandError("No se encontraron endpoints /integrations/datawarehouse/ en el Swagger.")

        applied = apply_datawarehouse_schema(resources)
        for resource, created in sorted(applied.items()):
            self.stdout.write(f"{resource}: {len(created)} columnas nuevas")
        self.stdout.write(self.style.SUCCESS(f"Schema aplicado para {len(applied)} recursos."))
