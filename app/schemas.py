from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CardCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Sol Ring", "set_code": "cmm", "target_price": "0.40", "foil": False},
                {"name": "Sol Ring", "set_code": None, "target_price": "0.40", "foil": False},
            ]
        }
    )

    name: str = Field(min_length=1)
    set_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=6,
        description="Scryfall set code. Leave empty to watch every printing of the card.",
    )
    target_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    foil: bool = False

    @field_validator("set_code", mode="before")
    @classmethod
    def blank_set_code_means_any(cls, value: str | None) -> str | None:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class LatestPrice(BaseModel):
    checked_at: datetime
    cardmarket_id: int | None = None
    set_name: str | None = None  # the printing these prices belong to
    low: Decimal | None
    trend: Decimal | None
    avg30: Decimal | None


class CardRead(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Sol Ring",
                    "set_code": None,
                    "set_name": None,
                    "printing_count": 127,
                    "foil": False,
                    "target_price": "0.40",
                    "active": True,
                    "created_at": "2026-09-30T08:08:54Z",
                    "cardmarket_url": "https://www.cardmarket.com/en/Magic/Products?idProduct=721733",
                    "latest_price": {
                        "checked_at": "2026-09-30T08:20:00Z",
                        "cardmarket_id": 721733,
                        "set_name": "Commander Masters",
                        "low": "0.48",
                        "trend": "1.00",
                        "avg30": "1.04",
                    },
                }
            ]
        }
    )

    id: int
    name: str
    set_code: str | None
    set_name: str | None
    printing_count: int
    foil: bool
    target_price: Decimal
    active: bool
    created_at: datetime
    cardmarket_url: str
    latest_price: LatestPrice | None


class AlertRead(BaseModel):
    sent_at: datetime
    price_at_alert: Decimal
    target_price: Decimal


class CardHistory(BaseModel):
    card_id: int
    name: str
    set_name: str | None
    foil: bool
    target_price: Decimal
    checks: list[LatestPrice]
    alerts: list[AlertRead]


class CheckResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "price_guide_created_at": "2026-09-30T09:54:57+0200",
                    "checked": 1,
                    "skipped": 0,
                    "missing": [],
                    "alerts_sent": 1,
                }
            ]
        }
    )

    price_guide_created_at: str | None
    checked: int
    skipped: int
    missing: list[int]
    alerts_sent: int


class ErrorResponse(BaseModel):
    detail: str
