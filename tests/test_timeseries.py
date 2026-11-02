from core import settings

STATS_URL = f"{settings.EXTRACTION_URL}/analytics/stats"


async def test_timeseries_is_monthly_stats_from_extraction(client, respx_mock):
    row = {"group": "2024-01", "count": 9, "p25": 9000.0, "median": 10000.0, "p75": 11000.0}
    route = respx_mock.get(STATS_URL).respond(json=[row])

    response = await client.get(
        "/analytics/timeseries", params={"powiat_code": "0264", "rooms": [2, 3]}
    )

    assert response.status_code == 200
    assert response.json() == [
        {"month": "2024-01", "count": 9, "p25": 9000.0, "median": 10000.0, "p75": 11000.0}
    ]
    params = route.calls.last.request.url.params
    assert params["group_by"] == "month"
    assert params["powiat_code"] == "0264"
    assert params.get_list("rooms") == ["2", "3"]
