from decimal import Decimal

from app.services.discord import AlertMessage, build_payload


def make_message(foil: bool = False, any_printing: bool = False) -> AlertMessage:
    return AlertMessage(
        card_name="Sol Ring",
        set_name="Commander Masters",
        any_printing=any_printing,
        foil=foil,
        price=Decimal("0.48"),
        target_price=Decimal("1.00"),
        cardmarket_url="https://www.cardmarket.com/en/Magic/Products?idProduct=721733",
    )


def test_build_payload():
    embed = build_payload(make_message())["embeds"][0]
    assert embed["title"] == "💰 PRICE DROP: Sol Ring"
    assert embed["description"] == "Commander Masters"
    assert embed["url"].endswith("idProduct=721733")
    assert [field["value"] for field in embed["fields"]] == ["€0.48", "€1.00"]


def test_build_payload_marks_foil():
    embed = build_payload(make_message(foil=True))["embeds"][0]
    assert embed["title"] == "💰 PRICE DROP: Sol Ring (Foil)"


def test_build_payload_names_cheapest_printing():
    embed = build_payload(make_message(any_printing=True))["embeds"][0]
    assert embed["description"] == "Goedkoopste printing: Commander Masters"
