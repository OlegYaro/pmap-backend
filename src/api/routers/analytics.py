from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Query, status

from api.schemas.analytics import TimeseriesPoint
from api.schemas.transactions import TransactionFilters
from clients.extraction import extraction_client
from core import settings

router = APIRouter(tags=["analytics"])


@router.get("/analytics/timeseries", status_code=status.HTTP_200_OK)
async def get_timeseries(
    filters: Annotated[TransactionFilters, Query()],
) -> list[TimeseriesPoint]:
    """Monthly median price per m2 with quartiles and the number of transactions."""
    params = filters.model_dump(mode="json", exclude_none=True)
    rows = await extraction_client.price_stats({**params, "group_by": "month"})

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


def first_provisional_month(today: date) -> str:
    """The first of the last PROVISIONAL_MONTHS months as YYYY-MM, the current one included."""
    months = today.year * 12 + today.month - settings.PROVISIONAL_MONTHS
    return f"{months // 12:04d}-{months % 12 + 1:02d}"
