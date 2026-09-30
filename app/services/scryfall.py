from dataclasses import dataclass

import httpx

from app.config import SCRYFALL_USER_AGENT

SCRYFALL_API = "https://api.scryfall.com"
HEADERS = {"User-Agent": SCRYFALL_USER_AGENT, "Accept": "application/json"}


class ScryfallError(Exception):
    """Scryfall could not be reached or returned an unexpected response."""


class CardNotFoundError(ScryfallError):
    """No card with this name exists in this set."""


class NotOnCardmarketError(ScryfallError):
    """The card exists, but Cardmarket does not sell this printing."""


@dataclass(frozen=True)
class CardInfo:
    name: str
    set_code: str
    set_name: str
    cardmarket_id: int
    scryfall_id: str


def parse_card(data: dict) -> CardInfo:
    cardmarket_id = data.get("cardmarket_id")
    if cardmarket_id is None:
        raise NotOnCardmarketError(
            f"{data['name']} ({data['set_name']}) is not listed on Cardmarket"
        )
    return CardInfo(
        name=data["name"],
        set_code=data["set"],
        set_name=data["set_name"],
        cardmarket_id=cardmarket_id,
        scryfall_id=data["id"],
    )


def lookup_card(name: str, set_code: str) -> CardInfo:
    try:
        response = httpx.get(
            f"{SCRYFALL_API}/cards/named",
            params={"exact": name, "set": set_code.lower()},
            headers=HEADERS,
            timeout=10,
        )
    except httpx.RequestError as exc:
        raise ScryfallError(f"Could not reach Scryfall: {exc}") from exc

    if response.status_code == 404:
        raise CardNotFoundError(f"No card named '{name}' in set '{set_code}'")
    if response.status_code != 200:
        raise ScryfallError(f"Scryfall returned status {response.status_code}")

    return parse_card(response.json())