import httpx

from core import settings

EXTRACTION = settings.EXTRACTION_URL

TRANSACTION = {
    "id": 1,
    "run_id": None,
    "external_transaction_identifier": "tx-1",
    "transaction_date": "2026-03-01",
    "price_premises": 500000.0,
    "area_usable": 50.0,
    "rooms": 2,
    "floor": 3,
    "powiat_code": "0264",
    "exclusion_reason": None,
    "attributes": {"tran_cena_brutto": 900000.0, "nier_cena_brutto": 600000.0},
    "updated_at": "2026-03-02T10:00:00Z",
}


async def test_card_shows_three_price_levels(client, respx_mock):
    respx_mock.get(f"{EXTRACTION}/transactions/1").respond(json=TRANSACTION)

    response = await client.get("/transactions/1")

    body = response.json()
    assert response.status_code == 200
    assert body["price_premises"] == 500000.0
    assert body["price_property"] == 600000.0
    assert body["price_transaction"] == 900000.0


async def test_invalid_filter_is_rejected_before_extraction(client, respx_mock):
    response = await client.get("/transactions", params={"unknown": "x"})

    assert response.status_code == 422
    assert not respx_mock.calls


async def test_territories_are_returned(client, respx_mock):
    territory = {
        "voivodeship_teryt": "02",
        "voivodeship_name": "dolnośląskie",
        "powiat_teryt": "0264",
        "powiat_name": "Wrocław",
        "gmina_teryt": None,
        "gmina_name": None,
    }
    respx_mock.get(f"{EXTRACTION}/territories").respond(json=[territory])

    response = await client.get("/territories")

    assert response.status_code == 200
    assert response.json() == [territory]


async def test_not_found_in_extraction_is_404(client, respx_mock):
    respx_mock.get(f"{EXTRACTION}/transactions/2").respond(404, json={"detail": "Not found"})

    response = await client.get("/transactions/2")

    assert response.status_code == 404


async def test_extraction_error_is_502(client, respx_mock):
    respx_mock.get(f"{EXTRACTION}/transactions/1").respond(500)

    response = await client.get("/transactions/1")

    assert response.status_code == 502


async def test_extraction_unavailable_is_502(client, respx_mock):
    respx_mock.get(f"{EXTRACTION}/transactions/1").mock(side_effect=httpx.ConnectError("refused"))

    response = await client.get("/transactions/1")

    assert response.status_code == 502
