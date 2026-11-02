from datetime import date

from core.config import settings


def first_provisional_month(today: date) -> str:
    """The first of the last PROVISIONAL_MONTHS months as YYYY-MM, the current one included."""
    months = today.year * 12 + today.month - settings.PROVISIONAL_MONTHS
    return f"{months // 12:04d}-{months % 12 + 1:02d}"
