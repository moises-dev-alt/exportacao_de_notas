from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests

from .config import Settings


class ApiError(RuntimeError):
    pass


def _value_at(payload: Any, path: str) -> Any:
    value = payload
    if not path:
        return value
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ApiError(f"Caminho '{path}' não encontrado na resposta da API.")
        value = value[part]
    return value


class DataClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch_updated(self, last_sync: str | None) -> list[dict[str, Any]]:
        if self.settings.data_source == "mock":
            return self._mock_records(last_sync)
        return self._api_records(last_sync)

    def _mock_records(self, last_sync: str | None) -> list[dict[str, Any]]:
        records = [
            {"id": "1001", "nome": "Ana Souza", "status": "Ativo", "valor": 1250.50, "updated_at": "2026-10-20T09:00:00+00:00"},
            {"id": "1002", "nome": "Bruno Lima", "status": "Pendente", "valor": 800.00, "updated_at": "2026-10-20T10:00:00+00:00"},
        ]
        return [row for row in records if not last_sync or row["updated_at"] > last_sync]

    def _api_records(self, last_sync: str | None) -> list[dict[str, Any]]:
        headers = {"Accept": "application/json"}
        token = f"{self.settings.api_token_prefix} {self.settings.api_token}".strip()
        headers[self.settings.api_token_header] = token
        url = f"{self.settings.api_base_url}/{self.settings.api_endpoint.lstrip('/')}"
        page = 1
        records: list[dict[str, Any]] = []

        while url:
            params: dict[str, Any] = {}
            if last_sync and self.settings.api_updated_since_param:
                params[self.settings.api_updated_since_param] = last_sync
            if self.settings.api_page_param:
                params[self.settings.api_page_param] = page
            if self.settings.api_page_size_param:
                params[self.settings.api_page_size_param] = self.settings.api_page_size
            try:
                response = requests.get(url, headers=headers, params=params, timeout=self.settings.api_timeout_seconds)
                response.raise_for_status()
                payload = response.json()
            except requests.Timeout as error:
                raise ApiError("A consulta à API excedeu o tempo limite.") from error
            except requests.ConnectionError as error:
                raise ApiError("Não foi possível conectar à API.") from error
            except requests.HTTPError as error:
                raise ApiError(f"A API retornou HTTP {error.response.status_code}.") from error
            except ValueError as error:
                raise ApiError("A API não retornou JSON válido.") from error

            page_records = _value_at(payload, self.settings.api_records_path)
            if not isinstance(page_records, list) or not all(isinstance(row, dict) for row in page_records):
                raise ApiError("Os registros da API devem ser uma lista de objetos JSON.")
            records.extend(page_records)
            next_page = _value_at(payload, self.settings.api_next_page_path) if self.settings.api_next_page_path else None
            if not next_page:
                break
            if not isinstance(next_page, str):
                raise ApiError("O próximo link de paginação precisa ser texto.")
            url, page = next_page, page + 1
        return records
