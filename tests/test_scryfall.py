import httpx
import pytest
import respx

from app.services.scryfall import (
    SCRYFALL_API,
    CardNotFoundError,
    NotOnCardmarketError,
    ScryfallError,
    lookup_card,
    parse_card,
)

NAMED_URL = f"{SCRYFALL_API}/cards/named"

SOL_RING = {
    "object": "card",
    "id": "46ca0b66-a000-4483-b916-f5b89e710244",
    "name": "Sol Ring",
    "set": "cmm",
    "set_name": "Commander Masters",
    "cardmarket_id": 721733,
}


def test_parse_card():
    info = parse_card(SOL_RING)
    assert info.name == "Sol Ring"
    assert info.set_code == "cmm"
    assert info.set_name == "Commander Masters"
    assert info.cardmarket_id == 721733
    assert info.scryfall_id == "46ca0b66-a000-4483-b916-f5b89e710244"


def test_parse_card_without_cardmarket_id():
    data = {key: value for key, value in SOL_RING.items() if key != "cardmarket_id"}
    with pytest.raises(NotOnCardmarketError):
        parse_card(data)


@respx.mock
def test_lookup_card_success():
    route = respx.get(NAMED_URL).mock(return_value=httpx.Response(200, json=SOL_RING))
    info = lookup_card("Sol Ring", "CMM")
    assert info.cardmarket_id == 721733
    assert route.calls.last.request.url.params["set"] == "cmm"


@respx.mock
def test_lookup_card_not_found():
    respx.get(NAMED_URL).mock(return_value=httpx.Response(404))
    with pytest.raises(CardNotFoundError):
        lookup_card("Rhystic Study", "cmm")


@respx.mock
def test_lookup_card_server_error():
    respx.get(NAMED_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(ScryfallError):
        lookup_card("Sol Ring", "cmm")


@respx.mock
def test_lookup_card_network_error():
    respx.get(NAMED_URL).mock(side_effect=httpx.ConnectError("connection refused"))
    with pytest.raises(ScryfallError):
        lookup_card("Sol Ring", "cmm")
