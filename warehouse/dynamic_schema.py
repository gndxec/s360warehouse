import hashlib
import json

from django.db import connection
from django.utils import timezone
from psycopg import sql
from psycopg.types.json import Jsonb

METADATA_COLUMNS = {
    "id",
    "external_id",
    "raw_data",
    "normalized_data",
    "row_hash",
    "is_active",
    "first_seen_at",
    "last_seen_at",
    "last_sync_id",
}

_COLUMN_CACHE = {}


def source_column_name(key):
    column = key
    if column in METADATA_COLUMNS:
        column = f"src_{column}"
    if len(column) <= 63:
        return column
    digest = hashlib.sha1(column.encode()).hexdigest()[:8]
    return f"{column[:54]}_{digest}"


def source_value(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return Jsonb(value)
    return value


def table_name(model):
    return model._meta.db_table


def existing_columns(table):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            """,
            [table],
        )
        return {row[0] for row in cursor.fetchall()}


def ensure_source_columns(model, normalized):
    table = table_name(model)
    present = _COLUMN_CACHE.setdefault(table, existing_columns(table))
    columns = {}

    with connection.cursor() as cursor:
        for key in normalized:
            column = source_column_name(key)
            columns[key] = column
            if column in present:
                continue
            cursor.execute(
                sql.SQL("ALTER TABLE {} ADD COLUMN {} TEXT").format(
                    sql.Identifier(table),
                    sql.Identifier(column),
                )
            )
            present.add(column)

    return columns


def upsert_source_row(model, external_id, raw, normalized, row_hash, sync_run_id):
    table = table_name(model)
    source_columns = ensure_source_columns(model, normalized)
    dynamic_columns = [source_columns[key] for key in normalized]

    now = timezone.now()
    base_columns = [
        "external_id",
        "raw_data",
        "normalized_data",
        "row_hash",
        "is_active",
        "first_seen_at",
        "last_seen_at",
        "last_sync_id",
    ]
    columns = base_columns + dynamic_columns
    values = [
        external_id,
        Jsonb(raw),
        Jsonb(normalized),
        row_hash,
        True,
        now,
        now,
        sync_run_id,
        *[source_value(normalized[key]) for key in normalized],
    ]

    update_columns = ["raw_data", "normalized_data", "row_hash", "is_active", "last_sync_id", *dynamic_columns]
    set_parts = [
        sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(column), sql.Identifier(column))
        for column in update_columns
    ]
    set_parts.append(sql.SQL("last_seen_at = NOW()"))

    query = sql.SQL(
        """
        INSERT INTO {} ({})
        VALUES ({})
        ON CONFLICT (external_id) DO UPDATE SET {}
        WHERE {}.row_hash IS DISTINCT FROM EXCLUDED.row_hash
           OR {}.is_active IS FALSE
        RETURNING xmax = 0 AS inserted
        """
    ).format(
        sql.Identifier(table),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
        sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        sql.SQL(", ").join(set_parts),
        sql.Identifier(table),
        sql.Identifier(table),
    )

    with connection.cursor() as cursor:
        cursor.execute(query, values)
        result = cursor.fetchone()

    if result is None:
        return "unchanged"
    return "created" if result[0] else "updated"


def deactivate_missing_rows(model, seen_ids, sync_run_id):
    table = table_name(model)
    if not seen_ids:
        query = sql.SQL(
            "UPDATE {} SET is_active = FALSE, last_sync_id = %s, last_seen_at = NOW() WHERE is_active IS TRUE"
        ).format(sql.Identifier(table))
        params = [sync_run_id]
    else:
        query = sql.SQL(
            """
            UPDATE {}
            SET is_active = FALSE, last_sync_id = %s, last_seen_at = NOW()
            WHERE is_active IS TRUE AND NOT (external_id = ANY(%s))
            """
        ).format(sql.Identifier(table))
        params = [sync_run_id, list(seen_ids)]

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.rowcount
