from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    set_code: str | None = None  # None means: watch every printing of this card
    set_name: str | None = None
    foil: bool = False
    target_price: Decimal = Field(max_digits=10, decimal_places=2)
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    printings: list["CardPrinting"] = Relationship(back_populates="card", cascade_delete=True)
    price_checks: list["PriceCheck"] = Relationship(back_populates="card", cascade_delete=True)
    alerts: list["Alert"] = Relationship(back_populates="card", cascade_delete=True)


class CardPrinting(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id", index=True, ondelete="CASCADE")
    cardmarket_id: int = Field(index=True)
    scryfall_id: str
    set_code: str
    set_name: str

    card: Card | None = Relationship(back_populates="printings")


class PriceCheck(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id", index=True, ondelete="CASCADE")
    checked_at: datetime = Field(default_factory=utcnow)
    cardmarket_id: int | None = None  # the printing these prices belong to (the cheapest one)
    low: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    trend: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    avg30: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    price_guide_created_at: str

    card: Card | None = Relationship(back_populates="price_checks")


class Alert(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id", index=True, ondelete="CASCADE")
    sent_at: datetime = Field(default_factory=utcnow)
    price_at_alert: Decimal = Field(max_digits=10, decimal_places=2)
    target_price: Decimal = Field(max_digits=10, decimal_places=2)

    card: Card | None = Relationship(back_populates="alerts")
