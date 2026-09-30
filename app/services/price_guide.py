from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.config import PRICE_GUIDE_URL

CENT = Decimal("0.01")


class PriceGuideError(Exception):
    """The price guide could not be downloaded or read."""


@dataclass(frozen=True)
class Prices:
    low: Decimal | None
    trend: Decimal | None
    avg30: Decimal | None


@dataclass(frozen=True)
class PriceGuide:
    created_at: str
    entries: dict[int, dict]


def to_decimal(value: float | None) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value)).quantize(CENT)


def extract_prices(entry: dict, foil: bool) -> Prices:
    suffix = "-foil" if foil else ""
    return Prices(
        low=to_decimal(entry.get(f"low{suffix}")),
        trend=to_decimal(entry.get(f"trend{suffix}")),
        avg30=to_decimal(entry.get(f"avg30{suffix}")),
    )


def parse_price_guide(data: dict, wanted_ids: set[int]) -> PriceGuide:
    try:
        entries = {            entry["idProduct"]: entry
            for entry in data["priceGuides"]
            if entry["idProduct"] in wanted_ids
        }
        return PriceGuide(created_at=data["createdAt"], entries=entries)
    except (KeyError, TypeError) as exc:
        raise PriceGuideError(f"Unexpected price guide format: {exc}") from exc


async def fetch_price_guide() -> dict:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(PRICE_GUIDE_URL)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise PriceGuideError(f"Could not download price guide: {exc}") from exc
    return response.json()