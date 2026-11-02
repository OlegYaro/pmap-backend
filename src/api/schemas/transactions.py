import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TransactionFilters(BaseModel):
    """Filters of every query over transactions; a filter that is not passed is not applied."""

    model_config = ConfigDict(extra="forbid")

    run_id: uuid.UUID | None = None
    voivodeship_code: str | None = None
    powiat_code: str | None = None
    gmina_code: str | None = None
    city_name: str | None = None
    district_name: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    area_min: float | None = Field(default=None, ge=0)
    area_max: float | None = Field(default=None, ge=0)
    rooms: list[int] | None = None
    floor_min: int | None = None
    floor_max: int | None = None
    market_type: str | None = None
    function: str | None = None
    address: str | None = None
    exclusion_reason: list[str] | None = None


class TransactionListQuery(TransactionFilters):
    """Filters plus one page; the next page starts after the last row's sort value and id."""

    limit: int = Field(default=100, ge=1, le=1000)
    sort: Literal[
        "id",
        "transaction_date",
        "price_premises",
        "area_usable",
        "rooms",
        "floor",
        "market_type",
        "function",
        "address",
        "powiat_code",
        "gmina_code",
        "city_name",
        "district_name",
        "updated_at",
    ] = "id"
    order: Literal["asc", "desc"] = "asc"
    after_value: str | None = None
    after_id: int | None = None


class TransactionResponse(BaseModel):
    """A transaction from Extraction with the three price levels as separate fields."""

    id: int
    run_id: uuid.UUID | None = None
    external_transaction_identifier: str
    external_building_id: str | None = None
    date_source_version: str | None = None
    transaction_date: date | None = None
    price_premises: float | None = None
    price_property: float | None = None
    price_transaction: float | None = None
    area_usable: float | None = None
    rooms: int | None = None
    floor: int | None = None
    market_type: str | None = None
    function: str | None = None
    address: str | None = None
    powiat_code: str
    gmina_code: str | None = None
    city_name: str | None = None
    district_name: str | None = None
    exclusion_reason: str | None = None
    attributes: dict[str, Any]
    updated_at: datetime

    @model_validator(mode="before")
    @classmethod
    def take_prices_from_attributes(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Extraction keeps the property and transaction prices in attributes."""
        attributes = data.get("attributes") or {}
        return {
            **data,
            "price_property": attributes.get("nier_cena_brutto"),
            "price_transaction": attributes.get("tran_cena_brutto"),
        }
