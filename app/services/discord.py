import logging
from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.config import DISCORD_WEBHOOK_URL

logger = logging.getLogger(__name__)

GREEN = 0x2ECC71


@dataclass(frozen=True)
class AlertMessage:
    card_name: str
    set_name: str
    foil: bool
    price: Decimal
    target_price: Decimal
    cardmarket_url: str


def build_payload(message: AlertMessage) -> dict:
    name = f"{message.card_name} (Foil)" if message.foil else message.card_name
    return {
        "embeds": [
            {
                "title": f"💰 PRICE DROP: {name}",
                "description": message.set_name,
                "url": message.cardmarket_url,
                "color": GREEN,
                "fields": [
                    {"name": "Laagste prijs", "value": f"€{message.price}", "inline": True},
                    {"name": "Jouw drempel", "value": f"€{message.target_price}", "inline": True},
                ],
            }
        ]
    }


async def send_alert(message: AlertMessage) -> bool:
    if not DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL is not set, skipping alert for %s", message.card_name)
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(DISCORD_WEBHOOK_URL, json=build_payload(message))
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Discord webhook failed for %s: %s", message.card_name, exc)
        return False
    return True
