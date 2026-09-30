from decimal import Decimal

import httpx
import pytest
import respx

from app.config import PRICE_GUIDE_URL
from app.services.price_guide import (
    PriceGuideError,
    extract_prices,
    fetch_price_guide,
    parse_price_guide,
    to_decimal,
)

# Real entry for Sol Ring (Commander Masters) from the spike
SOL_RING_ENTRY = {
    "idProduct": 721733,
    "idCategory": 1,
    "avg": 1.04,
    "low": 0.48,
    "trend": 0.92,
    "avg1": 0.75,
    "avg7": 1.01,
    "avg30": 1.04,
    "avg-foil": 3.53,
    "low-foil": 1.8,
    "trend-foil": 3.28,
    "avg1-foil": 2.99,
    "avg7-foil": 3.71,
    "avg30-foil": 2.97,
}

SAMPLE_GUIDE = {
    "version": 1,
    "createdAt": "2026-09-30T09:54:57+0200",
    "priceGuides": [SOL_RING_ENTRY, {"idProduct": 1, "low": 0.02}],
}


def test_to_decimal_rounds_to_cents():
    assert str(to_decimal(1.8)) == "1.80"
    assert str(to_decimal(0.1)) == "0.10"


def test_to_decimal_keeps_none():
    assert to_decimal(None) is None


def test_extract_prices_normal():
    prices = extract_prices(SOL_RING_ENTRY, foil=False)
    assert prices.low == Decimal("0.48")
    assert prices.trend == Decimal("0.92")
    assert prices.avg30 == Decimal("1.04")


def test_extract_prices_foil():
    prices = extract_prices(SOL_RING_ENTRY, foil=True)
    assert prices.low == Decimal("1.80")
    assert prices.trend == Decimal("3.28")
    assert prices.avg30 == Decimal("2.97")


def test_extract_prices_missing_fields_are_none():
    prices = extract_prices({"idProduct": 5}, foil=True)
    assert prices.low is None
    assert prices.trend is None
    assert prices.avg30 is None


def test_parse_price_guide_keeps_only_wanted_ids():
    guide = parse_price_guide(SAMPLE_GUIDE, {721733})
    assert guide.created_at == "2026-09-30T09:54:57+0200"
    assert list(guide.entries) == [721733]


def test_parse_price_guide_rejects_unexpected_format():
    with pytest.raises(PriceGuideError):
        parse_price_guide({"something": "else"}, {721733})

@pytest.mark.anyio
@respx.mock
async def test_fetch_price_guide_success():
    respx.get(PRICE_GUIDE_URL).mock(return_value=httpx.Response(200, json=SAMPLE_GUIDE))
    assert await fetch_price_guide() == SAMPLE_GUIDE


@pytest.mark.anyio
@respx.mock
async def test_fetch_price_guide_server_error():
    respx.get(PRICE_GUIDE_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(PriceGuideError):
        await fetch_price_guide()


@pytest.mark.anyio
@respx.mock
async def test_fetch_price_guide_network_error():
    respx.get(PRICE_GUIDE_URL).mock(side_effect=httpx.ConnectError("connection refused"))
    with pytest.raises(PriceGuideError):
        await fetch_price_guide()