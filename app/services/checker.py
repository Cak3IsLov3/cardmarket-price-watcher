from dataclasses import dataclass, field

from sqlalchemy import Engine
from sqlmodel import Session, col, select

from app.database import engine as default_engine
from app.models import Card, PriceCheck
from app.services.price_guide import extract_prices, fetch_price_guide, parse_price_guide


@dataclass(frozen=True)
class CheckResult:
    price_guide_created_at: str | None
    checked: int = 0
    skipped: int = 0
    missing: list[int] = field(default_factory=list)


def active_cards(session: Session) -> list[Card]:
    return list(session.exec(select(Card).where(col(Card.active).is_(True))).all())


def last_guide_version(session: Session, card_id: int) -> str | None:
    return session.exec(
        select(PriceCheck.price_guide_created_at)
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
    with Session(engine) as session:
        for card in active_cards(session):
            entry = guide.entries.get(card.cardmarket_id)
            if entry is None:
                missing.append(card.id)
                continue
            if last_guide_version(session, card.id) == guide.created_at:
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
        session.commit()

    return CheckResult(guide.created_at, checked, skipped, missing)