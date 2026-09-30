import time
from dataclasses import dataclass

import httpx

from app.config import SCRYFALL_USER_AGENT

SCRYFALL_API = "https://api.scryfall.com"
HEADERS = {"User-Agent": SCRYFALL_USER_AGENT, "Accept": "application/json"}
PAGE_DELAY_SECONDS = 0.1  # Scryfall asks for 50-100 ms between requests


class ScryfallError(Exception):
    """Scryfall could not be reached or returned an unexpected response."""


class CardNotFoundError(ScryfallError):
    """No card with this name exists (in this set)."""


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


def parse_printings(cards: list[dict]) -> list[CardInfo]:
    """Keep printings that Cardmarket sells, one per Cardmarket product."""
    printings: dict[int, CardInfo] = {}
    for data in cards:
        if data.get("cardmarket_id") is None:
            continue  # digital-only or not linked to Cardmarket
        info = parse_card(data)
        printings.setdefault(info.cardmarket_id, info)
    return list(printings.values())


def _get(url: str, params: dict | None = None) -> httpx.Response:
    try:
        return httpx.get(url, params=params, headers=HEADERS, timeout=10)
    except httpx.RequestError as exc:
        raise ScryfallError(f"Could not reach Scryfall: {exc}") from exc


def lookup_card(name: str, set_code: str) -> CardInfo:
    response = _get(f"{SCRYFALL_API}/cards/named", params={"exact": name, "set": set_code.lower()})
    if response.status_code == 404:
        raise CardNotFoundError(f"No card named '{name}' in set '{set_code}'")
    if response.status_code != 200:
        raise ScryfallError(f"Scryfall returned status {response.status_code}")
    return parse_card(response.json())


def lookup_printings(name: str) -> list[CardInfo]:
    """All printings of a card that are sold on Cardmarket, across every set."""
    url: str | None = f"{SCRYFALL_API}/cards/search"
    params: dict | None = {"q": f'!"{name}" unique:prints'}
    cards: list[dict] = []

    while url:
        response = _get(url, params)
        if response.status_code == 404:
            raise CardNotFoundError(f"No card named '{name}'")
        if response.status_code != 200:
            raise ScryfallError(f"Scryfall returned status {response.status_code}")
        data = response.json()
        cards.extend(data["data"])
        url = data.get("next_page")
        params = None  # next_page already contains the query
        if url:
            time.sleep(PAGE_DELAY_SECONDS)

    printings = parse_printings(cards)
    if not printings:
        raise NotOnCardmarketError(f"No printing of '{name}' is listed on Cardmarket")
    return printings
