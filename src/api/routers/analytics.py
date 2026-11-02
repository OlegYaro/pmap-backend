from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.analytics import TimeseriesPoint
from api.schemas.transactions import TransactionFilters
from core import settings
from core.dates import first_provisional_month
from integrations.extraction import extraction_http_client

router = APIRouter(tags=["analytics"])


@router.get("/analytics/timeseries", status_code=status.HTTP_200_OK)
async def get_timeseries(
    filters: Annotated[TransactionFilters, Query()],
) -> list[TimeseriesPoint]:
    """Monthly median price per m2 with quartiles and the number of transactions."""
    params = filters.model_dump(mode="json", exclude_none=True)
    rows = await extraction_http_client.price_stats({**params, "group_by": "month"})

    first_provisional = first_provisional_month(datetime.now(UTC).date())
    return [
        TimeseriesPoint(
            month=row["group"],
            count=row["count"],
            p25=row["p25"],
            median=row["median"],
            p75=row["p75"],
            low_sample=row["count"] < settings.MIN_SAMPLE,
            provisional=row["group"] >= first_provisional,
        )
        for row in rows
        if row["group"] is not None
    ]
