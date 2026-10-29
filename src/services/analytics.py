import asyncio
from datetime import timedelta

from api.schemas.analytics import DistributionRow, SummaryQuery, SummaryResponse
from integrations.extraction import extraction_http_client


class AnalyticsService:
    """Figures that need several Extraction stats calls."""

    @staticmethod
    async def summary(query: SummaryQuery) -> SummaryResponse:
        """The chosen period against the same dates a year earlier."""
        params = query.model_dump(mode="json", exclude_none=True)
        year_ago = {
            **params,
            "date_from": (query.date_from - timedelta(days=365)).isoformat(),
            "date_to": (query.date_to - timedelta(days=365)).isoformat(),
        }

        totals, previous_totals, rooms, floors = await asyncio.gather(
            extraction_http_client.price_stats({**params, "group_by": "none"}),
            extraction_http_client.price_stats({**year_ago, "group_by": "none"}),
            extraction_http_client.price_stats({**params, "group_by": "rooms"}),
            extraction_http_client.price_stats({**params, "group_by": "floor"}),
        )
        total, previous_total = totals[0], previous_totals[0]

        return SummaryResponse(
            median=total["median"],
            count=total["count"],
            previous_median=previous_total["median"],
            previous_count=previous_total["count"],
            change_pct=_change_pct(total["median"], previous_total["median"]),
            rooms=[DistributionRow(group=row["group"], count=row["count"]) for row in rooms],
            floors=[DistributionRow(group=row["group"], count=row["count"]) for row in floors],
        )


def _change_pct(current: float | None, previous: float | None) -> float | None:
    if current is None or not previous:
        return None
    return round((current / previous - 1) * 100, 1)
