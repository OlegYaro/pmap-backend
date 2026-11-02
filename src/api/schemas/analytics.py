from datetime import date

from pydantic import BaseModel, Field

from api.schemas.transactions import TransactionFilters


class TimeseriesPoint(BaseModel):
    """Price per m2 of clean transactions in one month."""

    month: str | None = Field(validation_alias="group")
    count: int
    p25: float | None
    median: float | None
    p75: float | None


class DistributionRow(BaseModel):
    """Number of clean transactions with one value of rooms or floor."""

    group: str | None
    count: int


class SummaryQuery(TransactionFilters):
    """Filters with a required period it is compared with the same dates a year earlier."""

    date_from: date
    date_to: date


class SummaryResponse(BaseModel):
    """An areas market in the period against the same dates a year earlier."""

    median: float | None
    count: int
    previous_median: float | None
    previous_count: int
    change_pct: float | None
    rooms: list[DistributionRow]
    floors: list[DistributionRow]
