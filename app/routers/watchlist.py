from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Engine
from sqlmodel import Session, col, select

from app.config import CARDMARKET_PRODUCT_URL
from app.database import get_engine, get_session
from app.models import Alert, Card, PriceCheck
from app.schemas import AlertRead, CardCreate, CardHistory, CardRead, LatestPrice
from app.services.checker import run_price_check
from app.services.price_guide import PriceGuideError
from app.services.scryfall import (
    CardNotFoundError,
    NotOnCardmarketError,
    ScryfallError,
    lookup_card,
)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])



def to_card_read(card: Card, session: Session) -> CardRead:
    latest = session.exec(
        select(PriceCheck)
        .where(PriceCheck.card_id == card.id)
        .order_by(col(PriceCheck.checked_at).desc())
    ).first()
    return CardRead(
        **card.model_dump(),
        cardmarket_url=CARDMARKET_PRODUCT_URL.format(id=card.cardmarket_id),
        latest_price=LatestPrice(**latest.model_dump()) if latest else None,
    )


@router.post("", response_model=CardRead, status_code=status.HTTP_201_CREATED)
def add_card(payload: CardCreate, session: Session = Depends(get_session)) -> CardRead:
    try:
        info = lookup_card(payload.name, payload.set_code)
    except CardNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    except NotOnCardmarketError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except ScryfallError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    existing = session.exec(
        select(Card).where(
            Card.cardmarket_id == info.cardmarket_id, Card.foil == payload.foil
        )
    ).first()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Card is already on your watchlist (id {existing.id})",
        )

    card = Card(
        name=info.name,
        set_code=info.set_code,
        set_name=info.set_name,
        cardmarket_id=info.cardmarket_id,
        scryfall_id=info.scryfall_id,
        foil=payload.foil,
        target_price=payload.target_price,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return to_card_read(card, session)


@router.get("", response_model=list[CardRead])
def list_cards(session: Session = Depends(get_session)) -> list[CardRead]:
    cards = session.exec(select(Card)).all()
    return [to_card_read(card, session) for card in cards]


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, session: Session = Depends(get_session)) -> None:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Card not found")
    session.delete(card)
    session.commit()


@router.post("/check")
async def check_prices(db_engine: Engine = Depends(get_engine)) -> dict:
    try:
        result = await run_price_check(db_engine)
    except PriceGuideError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return asdict(result)

@router.get("/{card_id}/history", response_model=CardHistory)
def card_history(card_id: int, session: Session = Depends(get_session)) -> CardHistory:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Card not found")

    checks = session.exec(
        select(PriceCheck)
        .where(PriceCheck.card_id == card_id)
        .order_by(col(PriceCheck.checked_at))
    ).all()
    alerts = session.exec(
        select(Alert).where(Alert.card_id == card_id).order_by(col(Alert.sent_at))
    ).all()

    return CardHistory(
        card_id=card.id,
        name=card.name,
        set_name=card.set_name,
        foil=card.foil,
        target_price=card.target_price,
        checks=[LatestPrice(**check.model_dump()) for check in checks],
        alerts=[AlertRead(**alert.model_dump()) for alert in alerts],
    )
