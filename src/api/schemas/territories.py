from pydantic import BaseModel


class TerritoryResponse(BaseModel):
    voivodeship_teryt: str
    voivodeship_name: str
    powiat_teryt: str | None
    powiat_name: str | None
    gmina_teryt: str | None
    gmina_name: str | None
