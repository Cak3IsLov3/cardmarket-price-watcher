import httpx
import pytest
import respx

from app.services.scryfall import (
    SCRYFALL_API,
    CardNotFoundError,
    NotOnCardmarketError,
    ScryfallError,
    lookup_card,
    lookup_printings,
    parse_card,
    parse_printings,
)
from tests.sample_data import SOL_RING, SOL_RING_DIGITAL, SOL_RING_OTHER

NAMED_URL = f"{SCRYFALL_API}/cards/named"
SEARCH_URL = f"{SCRYFALL_API}/cards/search"


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


# --- Every printing of a card ---


@pytest.fixture
def no_page_delay(monkeypatch):
    monkeypatch.setattr("app.services.scryfall.PAGE_DELAY_SECONDS", 0)


def search_page(cards, next_page=None):
    return httpx.Response(
        200,
        json={"object": "list", "data": cards, "has_more": bool(next_page), "next_page": next_page},
    )


def test_parse_printings_skips_digital_and_duplicates():
    printings = parse_printings([SOL_RING, SOL_RING_DIGITAL, SOL_RING_OTHER, SOL_RING])
    assert [p.cardmarket_id for p in printings] == [721733, 555555]


@respx.mock
def test_lookup_printings_follows_pages(no_page_delay):
    route = respx.get(SEARCH_URL).mock(
        side_effect=[
            search_page([SOL_RING, SOL_RING_DIGITAL], next_page=f"{SEARCH_URL}?page=2"),
            search_page([SOL_RING_OTHER]),
        ]
    )
    printings = lookup_printings("Sol Ring")
    assert {p.set_code for p in printings} == {"cmm", "c21"}
    assert route.call_count == 2
    assert route.calls[0].request.url.params["q"] == '!"Sol Ring" unique:prints'


@respx.mock
def test_lookup_printings_not_found(no_page_delay):
    respx.get(SEARCH_URL).mock(return_value=httpx.Response(404))
    with pytest.raises(CardNotFoundError):
        lookup_printings("Not A Real Card")


@respx.mock
def test_lookup_printings_only_digital(no_page_delay):
    respx.get(SEARCH_URL).mock(return_value=search_page([SOL_RING_DIGITAL]))
    with pytest.raises(NotOnCardmarketError):
        lookup_printings("Sol Ring")
