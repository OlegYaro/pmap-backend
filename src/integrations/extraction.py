import logging
from typing import Any

import httpx

from core import settings

log = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Extraction did not give the data status_code is what Backend answers its own client."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ExtractionHttpClient:
    """Calls the Extraction API which owns the transactions."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def list_transactions(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._request("GET", "/transactions", params=params)

    async def get_transaction(self, transaction_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/transactions/{transaction_id}")

    async def list_territories(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/territories")

    async def price_stats(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._request("GET", "/analytics/stats", params=params)

    async def create_transaction(self, data: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/transactions", json=data)

    async def update_transaction(self, transaction_id: int, data: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PATCH", f"/transactions/{transaction_id}", json=data)

    async def list_runs(self, limit: int) -> list[dict[str, Any]]:
        return await self._request("GET", "/runs", params={"limit": limit})

    async def get_run(self, run_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/runs/{run_id}")

    async def start_run(self, territory_code: str | None) -> dict[str, Any]:
        params = {"territory_code": territory_code} if territory_code else None
        return await self._request("POST", "/runs", params=params)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._http.request(method, path, params=params, json=json)
        except httpx.HTTPError as error:
            log.warning("Extraction is unavailable path=%s error=%r", path, error)
            raise ExtractionError(502, "Extraction is unavailable") from error

        if response.status_code == 404:
            raise ExtractionError(404, "Not found")
        if response.is_error:
            log.warning(
                "Extraction answered an error path=%s status=%s", path, response.status_code
            )
            raise ExtractionError(502, "Extraction request failed")
        return response.json()


def _headers() -> dict[str, str]:
    if settings.EXTRACTION_API_KEY is None:
        return {}
    return {"X-API-Key": settings.EXTRACTION_API_KEY.get_secret_value()}


extraction_http_client = ExtractionHttpClient(
    httpx.AsyncClient(
        base_url=settings.EXTRACTION_URL,
        headers=_headers(),
        timeout=settings.EXTRACTION_TIMEOUT_S,
    )
)
