import httpx
import pytest
from taskiq import TaskiqResult

from core import settings
from core.storage import storage
from jobs.broker import broker
from services import exports
from services.exports import ExportService

TRANSACTIONS_URL = f"{settings.EXTRACTION_URL}/transactions"


def transaction(id_):
    return {
        "id": id_,
        "external_transaction_identifier": f"tx-{id_}",
        "powiat_code": "0264",
        "address": "Wrocław, ul. Łąkowa 1",
        "attributes": {"nier_cena_brutto": 600000.0},
        "updated_at": "2026-03-02T10:00:00Z",
    }


async def test_export_writes_every_page_to_s3(respx_mock, monkeypatch):
    monkeypatch.setattr(exports, "PAGE_SIZE", 2)
    route = respx_mock.get(TRANSACTIONS_URL).mock(
        side_effect=[
            httpx.Response(200, json=[transaction(1), transaction(2)]),
            httpx.Response(200, json=[transaction(3)]),
        ]
    )
    uploaded = {}

    async def put_file(key, path):
        uploaded[key] = path.read_text(encoding="utf-8")

    monkeypatch.setattr(storage, "put_file", put_file)

    key = await ExportService.export_transactions({"powiat_code": "0264"})

    lines = uploaded[key].splitlines()
    assert key.startswith("exports/") and key.endswith(".csv")
    assert lines[0].startswith("id,")
    assert len(lines) == 4
    assert "Łąkowa" in lines[1]
    assert route.calls[0].request.url.params["powiat_code"] == "0264"
    assert route.calls[1].request.url.params["after_id"] == "2"


class FakeResults:
    def __init__(self, result=None):
        self.result = result

    async def is_result_ready(self, task_id):
        return self.result is not None

    async def get_result(self, task_id):
        return self.result


def result(**fields):
    return TaskiqResult(execution_time=0.1, **fields)


@pytest.mark.parametrize(
    ("task_result", "expected"),
    [
        (None, {"status": "pending"}),
        (
            result(is_err=True, return_value=None, error=ValueError("boom")),
            {"status": "failed", "error": "boom"},
        ),
        (
            result(is_err=False, return_value="exports/a.csv"),
            {"status": "done", "url": "https://s3/exports/a.csv"},
        ),
    ],
)
async def test_export_status(client, monkeypatch, task_result, expected):
    monkeypatch.setattr(broker, "result_backend", FakeResults(task_result))
    monkeypatch.setattr(storage, "download_url", lambda key: f"https://s3/{key}")

    response = await client.get("/exports/some-id")

    assert response.json() == expected
