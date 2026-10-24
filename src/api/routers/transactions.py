from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.transactions import TransactionListQuery, TransactionResponse
from clients.extraction import extraction_client

router = APIRouter(tags=["transactions"])


@router.get("/transactions", status_code=status.HTTP_200_OK)
async def list_transactions(
    query: Annotated[TransactionListQuery, Query()],
) -> list[TransactionResponse]:
    """One page of transactions filtered by the query."""
    rows = await extraction_client.list_transactions(
        query.model_dump(mode="json", exclude_none=True)
    )
    return [TransactionResponse.model_validate(row) for row in rows]


@router.get("/transactions/{transaction_id}", status_code=status.HTTP_200_OK)
async def get_transaction(transaction_id: int) -> TransactionResponse:
    """One transaction with every field and all three price levels."""
    row = await extraction_client.get_transaction(transaction_id)
    return TransactionResponse.model_validate(row)
