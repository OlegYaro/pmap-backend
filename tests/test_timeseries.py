from datetime import UTC, date, datetime

import pytest

from api.routers.analytics import first_provisional_month
from core import settings

STATS_URL = f"{settings.EXTRACTION_URL}/analytics/stats"


def row(month, count):
    return {"group": month, "count": count, "p25": 9000.0, "median": 10000.0, "p75": 11000.0}


async def test_filters_go_to_extraction_grouped_by_month(client, respx_mock):
    route = respx_mock.get(STATS_URL).respond(json=[])

    response = await client.get(
        "/analytics/timeseries", params={"powiat_code": "0264", "rooms": [2, 3]}
    )

    assert response.status_code == 200
    params = route.calls.last.request.url.params
    assert params["group_by"] == "month"
    assert params["powiat_code"] == "0264"
    assert params.get_list("rooms") == ["2", "3"]


async def test_small_sample_is_flagged(client, respx_mock, monkeypatch):
    monkeypatch.setattr(settings, "MIN_SAMPLE", 10)
    respx_mock.get(STATS_URL).respond(json=[row("2024-01", 9), row("2024-02", 10)])

    response = await client.get("/analytics/timeseries")

    assert [(p["month"], p["count"], p["low_sample"]) for p in response.json()] == [
        ("2024-01", 9, True),
        ("2024-02", 10, False),
    ]


async def test_last_months_are_provisional(client, respx_mock):
    current = datetime.now(UTC).strftime("%Y-%m")
    respx_mock.get(STATS_URL).respond(json=[row("2024-01", 50), row(current, 50)])

    response = await client.get("/analytics/timeseries")

    assert [p["provisional"] for p in response.json()] == [False, True]


async def test_transactions_without_date_are_skipped(client, respx_mock):
    respx_mock.get(STATS_URL).respond(json=[row(None, 3), row("2024-01", 50)])

    response = await client.get("/analytics/timeseries")

    assert [p["month"] for p in response.json()] == ["2024-01"]


@pytest.mark.parametrize(
    ("today", "months", "expected"),
    [
        (date(2026, 10, 25), 2, "2026-09"),
        (date(2026, 1, 5), 2, "2025-12"),
        (date(2026, 10, 25), 1, "2026-10"),
    ],
)
def test_first_provisional_month(monkeypatch, today, months, expected):
    monkeypatch.setattr(settings, "PROVISIONAL_MONTHS", months)

    assert first_provisional_month(today) == expected
