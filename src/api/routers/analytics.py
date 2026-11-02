from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.analytics import SummaryQuery, SummaryResponse, TimeseriesPoint
from api.schemas.transactions import TransactionFilters
from integrations.extraction import extraction_http_client
from services.analytics import AnalyticsService

router = APIRouter(tags=["analytics"])


@router.get("/analytics/timeseries", status_code=status.HTTP_200_OK)
async def get_timeseries(
    filters: Annotated[TransactionFilters, Query()],
) -> list[TimeseriesPoint]:
    """Monthly median price per m2 with quartiles and the number of transactions."""
    params = filters.model_dump(mode="json", exclude_none=True)
    rows = await extraction_http_client.price_stats({**params, "group_by": "month"})
    return [TimeseriesPoint.model_validate(row) for row in rows]


@router.get("/analytics/summary", status_code=status.HTTP_200_OK)
async def get_summary(query: Annotated[SummaryQuery, Query()]) -> SummaryResponse:
    """Price level, change against a year earlier, volume and distributions by rooms and floor."""
    return await AnalyticsService.summary(query)
