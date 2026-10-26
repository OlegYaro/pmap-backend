from fastapi import APIRouter, status

from api.schemas.territories import TerritoryResponse
from integrations.extraction import extraction_http_client

router = APIRouter(tags=["territories"])


@router.get("/territories", status_code=status.HTTP_200_OK)
async def list_territories() -> list[TerritoryResponse]:
    """Voivodeships powiats and gminas with their codes and names."""
    rows = await extraction_http_client.list_territories()
    return [TerritoryResponse.model_validate(row) for row in rows]
