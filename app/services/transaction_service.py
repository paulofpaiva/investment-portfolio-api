from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.asset import Asset
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    PortfolioAssetSummary,
    PortfolioSummaryResponse,
    TransactionCreate,
)


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_transactions(
        self,
        user_id: UUID,
        asset_id: UUID | None = None,
        transaction_type: TransactionType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[Transaction]:
        statement: Select[tuple[Transaction]] = (
            select(Transaction)
            .options(joinedload(Transaction.asset))
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transacted_at.desc())
        )

        if asset_id is not None:
            statement = statement.where(Transaction.asset_id == asset_id)
        if transaction_type is not None:
            statement = statement.where(Transaction.transaction_type == transaction_type)
        if start_date is not None:
            statement = statement.where(Transaction.transacted_at >= start_date)
        if end_date is not None:
            statement = statement.where(Transaction.transacted_at <= end_date)

        return list(self.db.execute(statement).scalars().all())

    def get_transaction_by_id(self, transaction_id: UUID, user_id: UUID) -> Transaction:
        statement = (
            select(Transaction)
            .options(joinedload(Transaction.asset))
            .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
        transaction = self.db.execute(statement).scalar_one_or_none()
        if transaction is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction not found.",
            )
        return transaction

    def create_transaction(self, user_id: UUID, payload: TransactionCreate) -> Transaction:
        asset = self.db.get(Asset, payload.asset_id)
        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset not found.",
            )

        transaction = Transaction(user_id=user_id, **payload.model_dump())
        self.db.add(transaction)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to create transaction.",
            ) from exc
        self.db.refresh(transaction)
        return self.get_transaction_by_id(transaction.id, user_id)

    def delete_transaction(self, transaction_id: UUID, user_id: UUID) -> None:
        transaction = self.get_transaction_by_id(transaction_id, user_id)
        self.db.delete(transaction)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to delete transaction.",
            ) from exc

    def get_portfolio_summary(self, user_id: UUID) -> PortfolioSummaryResponse:
        statement: Select[tuple[Transaction]] = (
            select(Transaction)
            .options(joinedload(Transaction.asset))
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transacted_at.asc(), Transaction.created_at.asc())
        )
        transactions = list(self.db.execute(statement).scalars().all())

        holdings: dict[UUID, dict[str, Decimal | Asset]] = {}

        for transaction in transactions:
            asset_state = holdings.setdefault(
                transaction.asset_id,
                {
                    "asset": transaction.asset,
                    "quantity": Decimal("0"),
                    "invested": Decimal("0"),
                },
            )

            quantity = Decimal(transaction.quantity)
            price_per_unit = Decimal(transaction.price_per_unit)
            current_quantity = Decimal(asset_state["quantity"])
            current_invested = Decimal(asset_state["invested"])

            if transaction.transaction_type == TransactionType.BUY:
                asset_state["quantity"] = current_quantity + quantity
                asset_state["invested"] = current_invested + (quantity * price_per_unit)
                continue

            if current_quantity <= 0:
                continue

            sell_quantity = min(quantity, current_quantity)
            average_price = current_invested / current_quantity if current_quantity > 0 else Decimal("0")
            asset_state["quantity"] = current_quantity - sell_quantity
            asset_state["invested"] = current_invested - (sell_quantity * average_price)

        asset_summaries: list[PortfolioAssetSummary] = []
        total_invested = Decimal("0")
        total_current_value = Decimal("0")

        for asset_state in holdings.values():
            total_quantity = Decimal(asset_state["quantity"])
            invested = Decimal(asset_state["invested"])

            if total_quantity <= 0:
                continue

            asset = asset_state["asset"]
            if not isinstance(asset, Asset):
                continue

            average_price = invested / total_quantity if total_quantity > 0 else Decimal("0")
            current_price = Decimal(asset.current_price)
            current_value = total_quantity * current_price
            profit_loss = current_value - invested
            profit_loss_pct = (
                (profit_loss / invested) * Decimal("100")
                if invested > 0
                else Decimal("0")
            )

            asset_summaries.append(
                PortfolioAssetSummary(
                    ticker=asset.ticker,
                    total_quantity=total_quantity,
                    average_price=average_price,
                    current_price=current_price,
                    current_value=current_value,
                    profit_loss=profit_loss,
                    profit_loss_pct=profit_loss_pct,
                )
            )

            total_invested += invested
            total_current_value += current_value

        total_profit_loss = total_current_value - total_invested

        return PortfolioSummaryResponse(
            assets=sorted(asset_summaries, key=lambda item: item.ticker),
            total_invested=total_invested,
            total_current_value=total_current_value,
            total_profit_loss=total_profit_loss,
        )
