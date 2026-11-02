from pydantic import BaseModel


class TimeseriesPoint(BaseModel):
    """Price per m2 of clean transactions in one month."""

    month: str
    count: int
    p25: float | None
    median: float | None
    p75: float | None
    low_sample: bool
    provisional: bool
