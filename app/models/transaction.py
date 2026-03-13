from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Numeric, Uuid, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    asset_id: Mapped[UUID] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    transaction_type: Mapped[TransactionType] = mapped_column(
        SqlEnum(TransactionType, name="transaction_type_enum"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    transacted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    user: Mapped["User"] = relationship(back_populates="transactions")
    asset: Mapped["Asset"] = relationship(back_populates="transactions")

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self._sync_total_value()

    def _sync_total_value(self) -> None:
        quantity = Decimal(self.quantity or 0)
        price_per_unit = Decimal(self.price_per_unit or 0)
        self.total_value = quantity * price_per_unit

    @property
    def asset_ticker(self) -> str:
        return self.asset.ticker

    @property
    def asset_name(self) -> str:
        return self.asset.name


@event.listens_for(Transaction, "before_insert")
@event.listens_for(Transaction, "before_update")
def sync_transaction_total_value(mapper: object, connection: object, target: Transaction) -> None:
    del mapper, connection
    target._sync_total_value()
