from datetime import datetime, timezone
from decimal import Decimal

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Card(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("cardmarket_id", "foil"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str
    set_code: str
    set_name: str
    cardmarket_id: int = Field(index=True)
    scryfall_id: str
    foil: bool = False
    target_price: Decimal = Field(max_digits=10, decimal_places=2)
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    price_checks: list["PriceCheck"] = Relationship(
        back_populates="card", cascade_delete=True
    )


class PriceCheck(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    card_id: int = Field(foreign_key="card.id", index=True, ondelete="CASCADE")
    checked_at: datetime = Field(default_factory=utcnow)
    low: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    trend: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    avg30: Decimal | None = Field(default=None, max_digits=10, decimal_places=2)
    price_guide_created_at: str

    card: Card | None = Relationship(back_populates="price_checks")