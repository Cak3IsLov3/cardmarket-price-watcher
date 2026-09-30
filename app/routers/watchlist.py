from dataclasses import asdict
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Engine
from sqlmodel import Session, col, select

from app.config import CARDMARKET_PRODUCT_URL, CARDMARKET_SEARCH_URL
from app.database import get_engine, get_session
from app.models import Alert, Card, CardPrinting, PriceCheck
from app.schemas import (
    AlertRead,
    CardCreate,
    CardHistory,
    CardRead,
    CheckResponse,
    ErrorResponse,
    LatestPrice,
)
from app.services.checker import run_price_check
from app.services.price_guide import PriceGuideError
from app.services.scryfall import (
    CardNotFoundError,
    NotOnCardmarketError,
    ScryfallError,
    lookup_card,
    lookup_printings,
)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def error_response(description: str) -> dict:
    return {"model": ErrorResponse, "description": description}


CARD_NOT_FOUND = {404: error_response("No card with this id on the watchlist")}


def to_latest_price(check: PriceCheck, card: Card) -> LatestPrice:
    set_names = {printing.cardmarket_id: printing.set_name for printing in card.printings}
    return LatestPrice(**check.model_dump(), set_name=set_names.get(check.cardmarket_id))


def cardmarket_url(card: Card, latest: PriceCheck | None) -> str:
    """Link to the cheapest printing if we know it, otherwise to a Cardmarket search."""
    if latest and latest.cardmarket_id:
        return CARDMARKET_PRODUCT_URL.format(id=latest.cardmarket_id)
    if len(card.printings) == 1:
        return CARDMARKET_PRODUCT_URL.format(id=card.printings[0].cardmarket_id)
    return CARDMARKET_SEARCH_URL.format(query=quote_plus(card.name))


def to_card_read(card: Card, session: Session) -> CardRead:
    latest = session.exec(
        select(PriceCheck)
        .where(PriceCheck.card_id == card.id)
        .order_by(col(PriceCheck.checked_at).desc())
    ).first()
    return CardRead(
        **card.model_dump(),
        printing_count=len(card.printings),
        cardmarket_url=cardmarket_url(card, latest),
        latest_price=to_latest_price(latest, card) if latest else None,
    )


@router.post(
    "",
    response_model=CardRead,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: error_response("Scryfall has no card with this name (in this set)"),
        409: error_response("This card is already on the watchlist"),
        502: error_response("Scryfall could not be reached"),
    },
)
def add_card(payload: CardCreate, session: Session = Depends(get_session)) -> CardRead:
    try:
        if payload.set_code:
            printings = [lookup_card(payload.name, payload.set_code)]
        else:
            printings = lookup_printings(payload.name)
    except CardNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotOnCardmarketError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except ScryfallError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    name = printings[0].name  # Scryfall's spelling, e.g. "sol ring" becomes "Sol Ring"
    set_code = printings[0].set_code if payload.set_code else None
    set_name = printings[0].set_name if payload.set_code else None

    same_set = Card.set_code == set_code if set_code else col(Card.set_code).is_(None)
    existing = session.exec(
        select(Card).where(Card.name == name, same_set, Card.foil == payload.foil)
    ).first()
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Card is already on your watchlist (id {existing.id})",
        )

    card = Card(
        name=name,
        set_code=set_code,
        set_name=set_name,
        foil=payload.foil,
        target_price=payload.target_price,
        printings=[
            CardPrinting(
                cardmarket_id=printing.cardmarket_id,
                scryfall_id=printing.scryfall_id,
                set_code=printing.set_code,
                set_name=printing.set_name,
            )
            for printing in printings
        ],
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return to_card_read(card, session)


@router.get("", response_model=list[CardRead])
def list_cards(session: Session = Depends(get_session)) -> list[CardRead]:
    cards = session.exec(select(Card)).all()
    return [to_card_read(card, session) for card in cards]


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT, responses=CARD_NOT_FOUND)
def delete_card(card_id: int, session: Session = Depends(get_session)) -> None:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Card not found")
    session.delete(card)
    session.commit()


@router.post(
    "/check",
    response_model=CheckResponse,
    responses={502: error_response("The Cardmarket price guide could not be downloaded")},
)
async def check_prices(db_engine: Engine = Depends(get_engine)) -> CheckResponse:
    try:
        result = await run_price_check(db_engine)
    except PriceGuideError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return CheckResponse(**asdict(result))


@router.get("/{card_id}/history", response_model=CardHistory, responses=CARD_NOT_FOUND)
def card_history(card_id: int, session: Session = Depends(get_session)) -> CardHistory:
    card = session.get(Card, card_id)
    if card is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Card not found")

    checks = session.exec(
        select(PriceCheck).where(PriceCheck.card_id == card_id).order_by(col(PriceCheck.checked_at))
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
        checks=[to_latest_price(check, card) for check in checks],
        alerts=[AlertRead(**alert.model_dump()) for alert in alerts],
    )
