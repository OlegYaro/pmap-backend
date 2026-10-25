import logging
from typing import Any

import httpx

from core import settings

log = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Extraction did not give the data; status_code is what Backend answers its own client."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class ExtractionClient:
    """Calls the Extraction API, which owns the transactions."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def list_transactions(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._get("/transactions", params)

    async def get_transaction(self, transaction_id: int) -> dict[str, Any]:
        return await self._get(f"/transactions/{transaction_id}")

    async def list_territories(self) -> list[dict[str, Any]]:
        return await self._get("/territories")

    async def price_stats(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._get("/analytics/stats", params)

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = await self._http.get(path, params=params)
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


extraction_client = ExtractionClient(
    httpx.AsyncClient(
        base_url=settings.EXTRACTION_URL,
        headers=_headers(),
        timeout=settings.EXTRACTION_TIMEOUT_S,
    )
)
