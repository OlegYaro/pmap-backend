from core import settings

STATS_URL = f"{settings.EXTRACTION_URL}/analytics/stats"


def mock_stats(respx_mock, group_by, date_from, rows):
    params = {"group_by": group_by, "date_from": date_from}
    return respx_mock.get(STATS_URL, params__contains=params).respond(json=rows)


def row(group, count, median=None):
    return {"group": group, "count": count, "p25": None, "median": median, "p75": None}


async def test_summary_compares_with_the_same_dates_a_year_earlier(client, respx_mock):
    current = mock_stats(respx_mock, "none", "2026-01-01", [row(None, 40, 11000.0)])
    previous = mock_stats(respx_mock, "none", "2025-01-01", [row(None, 30, 10000.0)])
    mock_stats(respx_mock, "rooms", "2026-01-01", [row("2", 25), row("3", 15)])
    mock_stats(respx_mock, "floor", "2026-01-01", [row("0", 40)])

    response = await client.get(
        "/analytics/summary",
        params={"powiat_code": "0264", "date_from": "2026-01-01", "date_to": "2026-06-30"},
    )

    body = response.json()
    assert response.status_code == 200
    assert (body["median"], body["count"], body["previous_count"]) == (11000.0, 40, 30)
    assert body["change_pct"] == 10.0
    assert body["rooms"] == [{"group": "2", "count": 25}, {"group": "3", "count": 15}]
    assert body["floors"] == [{"group": "0", "count": 40}]
    assert current.calls.last.request.url.params["powiat_code"] == "0264"
    assert previous.calls.last.request.url.params["date_to"] == "2025-06-30"
