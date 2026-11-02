import uuid
from typing import Any

from fastapi import APIRouter, Query, status

from api.schemas.transactions import TransactionCreate, TransactionResponse, TransactionUpdate
from integrations.extraction import extraction_http_client

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/runs", status_code=status.HTTP_200_OK)
async def list_runs(limit: int = Query(default=20, ge=1, le=100)) -> list[dict[str, Any]]:
    """The latest Extraction runs with task counts by status."""
    return await extraction_http_client.list_runs(limit)


@router.get("/runs/{run_id}", status_code=status.HTTP_200_OK)
async def get_run(run_id: uuid.UUID) -> dict[str, Any]:
    """One run with failed tasks and their traces."""
    return await extraction_http_client.get_run(str(run_id))


@router.post("/runs", status_code=status.HTTP_202_ACCEPTED)
async def start_run(territory_code: str | None = None) -> dict[str, Any]:
    """Start a sync for one powiat, or for all of them."""
    return await extraction_http_client.start_run(territory_code)


@router.post("/transactions", status_code=status.HTTP_201_CREATED)
async def create_transaction(data: TransactionCreate) -> TransactionResponse:
    """Add a transaction by hand."""
    created = await extraction_http_client.create_transaction(data.model_dump(mode="json"))
    return TransactionResponse.model_validate(created)


@router.patch("/transactions/{transaction_id}", status_code=status.HTTP_200_OK)
async def update_transaction(transaction_id: int, data: TransactionUpdate) -> TransactionResponse:
    """Correct a transaction by hand; only the passed fields change."""
    updated = await extraction_http_client.update_transaction(
        transaction_id, data.model_dump(mode="json", exclude_unset=True)
    )
    return TransactionResponse.model_validate(updated)
