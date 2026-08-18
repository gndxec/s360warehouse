import hashlib
import hmac
import time
from urllib.parse import urlencode

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DatawarehouseClient:
    base_path = "/api/v1/integrations/datawarehouse/"

    def __init__(self, host=None, token=None, timeout=60):
        self.host = (host or settings.DW_API_HOST).rstrip("/")
        self.token = token or settings.DW_API_TOKEN
        self.timeout = timeout
        self.session = requests.Session()
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def iter_resource(self, resource, filters=None, page_size=None):
        if not self.host:
            raise ValueError("DW_API_HOST no esta configurado.")
        if not self.token:
            raise ValueError("DW_API_TOKEN no esta configurado.")

        page = 1
        page_size = page_size or settings.SYNC_PAGE_SIZE
        filters = filters or {}
        while True:
            params = {"page": page, "page_size": page_size, **filters}
            payload = self._get(resource, params)
            data = payload["data"]
            yield from data.get("items", [])
            if not data.get("meta", {}).get("has_next"):
                break
            page += 1

    def _get(self, resource, params):
        path = f"{self.base_path}{resource}/"
        query = urlencode(params)
        headers = {"Authorization": f"Token {self.token}"}
        if settings.DW_HMAC_ENABLED:
            headers["X-DW-Signature"] = self._signature("GET", path, query)
        response = self.session.get(f"{self.host}{path}", params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def _signature(self, method, path, query):
        secret = settings.SECRET_DW_TO_ERP_SECRET
        if not secret:
            raise ValueError("SECRET_DW_TO_ERP_SECRET es requerido cuando DW_HMAC_ENABLED=True.")
        timestamp = str(int(time.time()))
        message = f"{timestamp}.{method}\n{path}\n{query}".encode()
        digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        return f"t={timestamp},v1={digest}"
