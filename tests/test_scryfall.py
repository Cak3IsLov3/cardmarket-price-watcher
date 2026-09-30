import pytest

from app.services.scryfall import NotOnCardmarketError, parse_card

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