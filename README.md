# Replica S360 Data Warehouse

Backend en Django REST Framework con PostgreSQL, Redis y Celery para replicar los endpoints flat de S360 cada 30 minutos.

## Servicios

- `api`: DRF para consultar la replica local.
- `db`: PostgreSQL.
- `redis`: broker/result backend de Celery.
- `celery_worker`: ejecuta la sincronizacion.
- `celery_beat`: agenda la sincronizacion cada 30 minutos todos los dias.

## Configuracion

```bash
copy .env.example .env
```

Edita `.env`:

```bash
DW_API_HOST=https://tu-tenant.com
DW_API_TOKEN=tu-token-drf
DW_HMAC_ENABLED=False
SECRET_DW_TO_ERP_SECRET=
```

Si el origen exige HMAC, usa:

```bash
DW_HMAC_ENABLED=True
SECRET_DW_TO_ERP_SECRET=el-secreto-hmac
```

## Levantar

```bash
docker compose up --build
```

La API queda en:

```text
http://localhost:8000/api/
```

Endpoints locales:

- `GET /api/records/`: registros replicados.
- `GET /api/records/?resource=cliente&active=true`: filtrado por recurso.
- `GET /api/records/resources/`: catalogo de recursos configurados.
- `GET /api/sync-runs/`: historial de sincronizaciones.
- `POST /api/sync-runs/trigger/`: dispara una sincronizacion manual.

Tambien puedes ejecutar una sincronizacion manual desde consola:

```bash
docker compose run --rm api python manage.py sync_datawarehouse
```

## Normalizacion

Cada fila se guarda en dos formas:

- `raw_data`: fila original del endpoint.
- `normalized_data`: llaves en `snake_case`, textos recortados, espacios compactados, booleanos/fechas/numeros convertidos cuando aplica.

Ademas, durante la sincronizacion cada llave normalizada de la API se materializa como una
columna fisica dentro de su tabla `s360_*`. Por ejemplo, si `cliente/` devuelve
`uuid`, `name` y `estado`, la tabla `s360_cliente` recibe columnas `uuid`, `name` y
`estado` automaticamente. `raw_data` y `normalized_data` quedan como respaldo y auditoria,
no como unico almacenamiento de negocio.

Si tienes el Swagger/OpenAPI exportado, puedes crear las columnas antes de la primera
sincronizacion:

```bash
docker compose exec api python manage.py apply_datawarehouse_swagger "/ruta/al/swagger.jsonc"
```

La identidad local se toma de `uuid`, luego `id`, luego `pk`. Si no existe ninguna, se usa un hash estable de la fila.
