from dataclasses import dataclass, field

from sqlalchemy import Engine
from sqlmodel import Session, col, select

from app.config import CARDMARKET_PRODUCT_URL
from app.database import engine as default_engine
from app.models import Alert, Card, PriceCheck
from app.services.alerts import should_alert
from app.services.discord import AlertMessage, send_alert
from app.services.price_guide import extract_prices, fetch_price_guide, parse_price_guide


@dataclass(frozen=True)
class CheckResult:
    price_guide_created_at: str | None
    checked: int = 0
    skipped: int = 0
    missing: list[int] = field(default_factory=list)
    alerts_sent: int = 0


def active_cards(session: Session) -> list[Card]:
    return list(session.exec(select(Card).where(col(Card.active).is_(True))).all())


def latest_check(session: Session, card_id: int) -> PriceCheck | None:
    return session.exec(
        select(PriceCheck)
        .where(PriceCheck.card_id == card_id)
        .order_by(col(PriceCheck.checked_at).desc())
    ).first()


async def run_price_check(engine: Engine = default_engine) -> CheckResult:
    with Session(engine) as session:
        wanted_ids = {card.cardmarket_id for card in active_cards(session)}
    if not wanted_ids:
        return CheckResult(price_guide_created_at=None)

    guide = parse_price_guide(await fetch_price_guide(), wanted_ids)

    checked, skipped, missing = 0, 0, []
    pending: list[tuple[int, AlertMessage]] = []

    with Session(engine) as session:
        for card in active_cards(session):
            entry = guide.entries.get(card.cardmarket_id)
            if entry is None:
                missing.append(card.id)
                continue

            previous = latest_check(session, card.id)
            if previous and previous.price_guide_created_at == guide.created_at:
                skipped += 1
                continue

            prices = extract_prices(entry, card.foil)
            session.add(
                PriceCheck(
                    card_id=card.id,
                    low=prices.low,
                    trend=prices.trend,
                    avg30=prices.avg30,
                    price_guide_created_at=guide.created_at,
                )
            )
            checked += 1

            previous_low = previous.low if previous else None
            if should_alert(previous_low, prices.low, card.target_price):
                pending.append(
                    (
                        card.id,
                        AlertMessage(
                            card_name=card.name,
                            set_name=card.set_name,
                            foil=card.foil,
                            price=prices.low,
                            target_price=card.target_price,
                            cardmarket_url=CARDMARKET_PRODUCT_URL.format(id=card.cardmarket_id),
                        ),
                    )
                )
        session.commit()

    alerts_sent = 0
    for card_id, message in pending:
        if await send_alert(message):
            with Session(engine) as session:
                session.add(
                    Alert(
                        card_id=card_id,
                        price_at_alert=message.price,
                        target_price=message.target_price,
                    )
                )
                session.commit()
            alerts_sent += 1

    return CheckResult(guide.created_at, checked, skipped, missing, alerts_sent)