import json
import re
from pathlib import Path

from django.db import connection
from psycopg import sql

from .dynamic_schema import METADATA_COLUMNS, existing_columns, source_column_name
from .models import RESOURCE_MODEL_MAP
from .normalization import normalize_key


def strip_jsonc_comments(content):
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
    return re.sub(r"(^|[^:])//.*", r"\1", content)


def load_swagger(path):
    content = Path(path).read_text(encoding="utf-8-sig")
    return json.loads(strip_jsonc_comments(content))


def response_item_properties(path_doc):
    schema = path_doc.get("get", {}).get("responses", {}).get("200", {}).get("schema", {})
    try:
        return schema["properties"]["data"]["properties"]["items"]["items"]["properties"]
    except KeyError:
        return {}


def postgres_type(property_schema):
    swagger_type = property_schema.get("type")
    swagger_format = property_schema.get("format")

    if swagger_type == "integer":
        return "BIGINT"
    if swagger_type == "number" or swagger_format == "decimal":
        return "NUMERIC"
    if swagger_type == "boolean":
        return "BOOLEAN"
    if swagger_type == "string" and swagger_format == "uuid":
        return "UUID"
    if swagger_type == "string" and swagger_format == "date":
        return "DATE"
    if swagger_type == "string" and swagger_format == "date-time":
        return "TIMESTAMPTZ"
    if swagger_type in {"object", "array"}:
        return "JSONB"
    return "TEXT"


def datawarehouse_resource_from_path(path):
    prefix = "/integrations/datawarehouse/"
    if not path.startswith(prefix) or path == prefix:
        return None
    resource = path.removeprefix(prefix).strip("/")
    if "/" in resource:
        return None
    return resource


def extract_datawarehouse_schema(swagger):
    resources = {}
    for path, path_doc in swagger.get("paths", {}).items():
        resource = datawarehouse_resource_from_path(path)
        if resource not in RESOURCE_MODEL_MAP:
            continue

        fields = []
        for raw_name, property_schema in response_item_properties(path_doc).items():
            normalized_name = normalize_key(raw_name)
            column_name = source_column_name(normalized_name)
            fields.append(
                {
                    "source": raw_name,
                    "normalized": normalized_name,
                    "column": column_name,
                    "type": postgres_type(property_schema),
                    "conflicts_metadata": normalized_name in METADATA_COLUMNS,
                }
            )
        resources[resource] = fields
    return resources


def apply_datawarehouse_schema(resources):
    applied = {}
    with connection.cursor() as cursor:
        for resource, fields in resources.items():
            model = RESOURCE_MODEL_MAP[resource]
            table = model._meta.db_table
            present = existing_columns(table)
            created = []

            for field in fields:
                column = field["column"]
                if column in present:
                    continue
                cursor.execute(
                    sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        sql.Identifier(table),
                        sql.Identifier(column),
                        sql.SQL(field["type"]),
                    )
                )
                present.add(column)
                created.append(field)
            applied[resource] = created
    return applied
