from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.transactions import TransactionFilters
from core.storage import storage
from jobs.broker import broker
from jobs.tasks import export_transactions

router = APIRouter(tags=["exports"])


@router.post("/exports", status_code=status.HTTP_202_ACCEPTED)
async def start_export(filters: Annotated[TransactionFilters, Query()]) -> dict[str, str]:
    """Put an export of the filtered transactions in the queue."""
    task = await export_transactions.kiq(filters.model_dump(mode="json", exclude_none=True))
    return {"id": task.task_id}


@router.get("/exports/{export_id}", status_code=status.HTTP_200_OK)
async def get_export(export_id: str) -> dict[str, str]:
    """Status of an export; when it is done, a link to the file in S3."""
    if not await broker.result_backend.is_result_ready(export_id):
        return {"status": "pending"}
    result = await broker.result_backend.get_result(export_id)
    if result.is_err:
        return {"status": "failed", "error": getattr(result.error, "detail", str(result.error))}
    return {"status": "done", "url": storage.download_url(result.return_value)}
