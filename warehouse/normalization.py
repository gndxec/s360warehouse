import hashlib
import json
import re
import unicodedata
from datetime import datetime
from decimal import Decimal, InvalidOperation

TRUE_VALUES = {"true", "t", "yes", "y", "si", "1", "activo"}
FALSE_VALUES = {"false", "f", "no", "n", "0", "inactivo"}
DATE_FORMATS = ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z")


def normalize_key(key):
    text = unicodedata.normalize("NFKD", str(key)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text or "field"


def normalize_string(value):
    value = " ".join(value.strip().split())
    return value or None


def maybe_number(value):
    if not re.fullmatch(r"-?\d+([.,]\d+)?", value):
        return value
    try:
        return float(Decimal(value.replace(",", ".")))
    except InvalidOperation:
        return value


def maybe_datetime(value):
    candidate = value.replace("Z", "+00:00")
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(candidate, fmt).isoformat()
        except ValueError:
            continue
    return value


def normalize_value(value):
    if isinstance(value, dict):
        return normalize_record(value)
    if isinstance(value, list):
        return [normalize_value(item) for item in value]
    if isinstance(value, str):
        text = normalize_string(value)
        if text is None:
            return None
        lowered = text.lower()
        if lowered in TRUE_VALUES:
            return True
        if lowered in FALSE_VALUES:
            return False
        dated = maybe_datetime(text)
        if dated != text:
            return dated
        return maybe_number(text)
    return value


def normalize_record(record):
    return {normalize_key(key): normalize_value(value) for key, value in record.items()}


def stable_hash(payload):
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()
