from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.errors import build_http_error
from app.models.asset import Asset
from app.models.transaction import Transaction, TransactionType
from app.models.wallet import Wallet
from app.schemas.transaction import (
    PortfolioAssetSummary,
    PortfolioSummaryResponse,
    TransactionCreate,
)


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _get_wallet_by_id(self, wallet_id: UUID, user_id: UUID) -> Wallet:
        statement = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        wallet = self.db.execute(statement).scalar_one_or_none()
        if wallet is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Wallet not found.",
                error_code="WALLET_NOT_FOUND",
            )
        return wallet

    def _get_default_wallet(self, user_id: UUID) -> Wallet:
        statement = select(Wallet).where(Wallet.user_id == user_id, Wallet.is_default.is_(True))
        wallet = self.db.execute(statement).scalar_one_or_none()
        if wallet is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Default wallet not found.",
                error_code="DEFAULT_WALLET_NOT_FOUND",
            )
        return wallet

    def _resolve_wallet(self, user_id: UUID, wallet_id: UUID | None = None) -> Wallet:
        if wallet_id is None:
            return self._get_default_wallet(user_id)
        return self._get_wallet_by_id(wallet_id, user_id)

    def _build_user_transactions_with_assets_query(
        self,
        user_id: UUID,
        wallet_id: UUID | None = None,
    ) -> Select[tuple[Transaction]]:
        statement: Select[tuple[Transaction]] = (
            select(Transaction)
            .options(joinedload(Transaction.asset))
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.transacted_at.asc(), Transaction.created_at.asc())
        )
        if wallet_id is not None:
            statement = statement.where(Transaction.wallet_id == wallet_id)
        return statement

    def _calculate_user_asset_state(
        self,
        user_id: UUID,
        wallet_id: UUID | None = None,
        asset_id: UUID | None = None,
    ) -> dict[UUID, dict[str, Decimal | Asset]]:
        statement = self._build_user_transactions_with_assets_query(user_id, wallet_id=wallet_id)
        if asset_id is not None:
            statement = statement.where(Transaction.asset_id == asset_id)

        transactions = list(self.db.execute(statement).scalars().all())
        holdings: dict[UUID, dict[str, Decimal | Asset]] = {}

        for transaction in transactions:
            asset_state = holdings.setdefault(
                transaction.asset_id,
                {
                    "asset": transaction.asset,
                    "quantity": Decimal("0"),
                    "cost_basis": Decimal("0"),
                    "gross_invested": Decimal("0"),
                    "realized_profit_loss": Decimal("0"),
                },
            )

            quantity = Decimal(transaction.quantity)
            price_per_unit = Decimal(transaction.price_per_unit)
            current_quantity = Decimal(asset_state["quantity"])
            current_cost_basis = Decimal(asset_state["cost_basis"])
            current_gross_invested = Decimal(asset_state["gross_invested"])
            current_realized = Decimal(asset_state["realized_profit_loss"])

            if transaction.transaction_type == TransactionType.BUY:
                asset_state["quantity"] = current_quantity + quantity
                asset_state["cost_basis"] = current_cost_basis + (quantity * price_per_unit)
                asset_state["gross_invested"] = current_gross_invested + (quantity * price_per_unit)
                continue

            if current_quantity <= 0 or quantity > current_quantity:
                continue

            average_price = current_cost_basis / current_quantity if current_quantity > 0 else Decimal("0")
            realized_profit_loss = quantity * (price_per_unit - average_price)

            asset_state["quantity"] = current_quantity - quantity
            asset_state["cost_basis"] = current_cost_basis - (quantity * average_price)
            asset_state["realized_profit_loss"] = current_realized + realized_profit_loss

        return holdings

    def _build_filtered_transactions_query(
        self,
        user_id: UUID,
        wallet_id: UUID | None = None,
        asset_id: UUID | None = None,
        transaction_type: TransactionType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> Select[tuple[Transaction]]:
        statement: Select[tuple[Transaction]] = select(Transaction).where(Transaction.user_id == user_id)
        if wallet_id is not None:
            statement = statement.where(Transaction.wallet_id == wallet_id)

        if asset_id is not None:
            statement = statement.where(Transaction.asset_id == asset_id)
        if transaction_type is not None:
            statement = statement.where(Transaction.transaction_type == transaction_type)
        if start_date is not None:
            statement = statement.where(Transaction.transacted_at >= start_date)
        if end_date is not None:
            statement = statement.where(Transaction.transacted_at <= end_date)

        return statement

    def list_transactions(
        self,
        user_id: UUID,
        wallet_id: UUID | None = None,
        asset_id: UUID | None = None,
        transaction_type: TransactionType | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Transaction], int]:
        if wallet_id is not None:
            self._get_wallet_by_id(wallet_id, user_id)

        base_statement = self._build_filtered_transactions_query(
            user_id=user_id,
            wallet_id=wallet_id,
            asset_id=asset_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date,
        )
        items_statement = (
            base_statement
            .options(joinedload(Transaction.asset))
            .order_by(Transaction.transacted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        total_statement = select(func.count()).select_from(base_statement.subquery())

        items = list(self.db.execute(items_statement).scalars().all())
        total = int(self.db.execute(total_statement).scalar_one())
        return items, total

    def get_transaction_by_id(
        self,
        transaction_id: UUID,
        user_id: UUID,
        wallet_id: UUID | None = None,
    ) -> Transaction:
        if wallet_id is not None:
            self._get_wallet_by_id(wallet_id, user_id)

        statement = (
            select(Transaction)
            .options(joinedload(Transaction.asset))
            .where(Transaction.id == transaction_id, Transaction.user_id == user_id)
        )
        if wallet_id is not None:
            statement = statement.where(Transaction.wallet_id == wallet_id)

        transaction = self.db.execute(statement).scalar_one_or_none()
        if transaction is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Transaction not found.",
                error_code="TRANSACTION_NOT_FOUND",
            )
        return transaction

    def create_transaction(
        self,
        user_id: UUID,
        payload: TransactionCreate,
        wallet_id: UUID | None = None,
    ) -> Transaction:
        wallet = self._resolve_wallet(user_id, wallet_id)
        asset = self.db.get(Asset, payload.asset_id)
        if asset is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Asset not found.",
                error_code="ASSET_NOT_FOUND",
            )

        if payload.transaction_type == TransactionType.SELL:
            asset_state = self._calculate_user_asset_state(
                user_id=user_id,
                wallet_id=wallet.id,
                asset_id=payload.asset_id,
            )
            current_state = asset_state.get(payload.asset_id)
            current_quantity = Decimal("0")
            if current_state is not None:
                current_quantity = Decimal(current_state["quantity"])

            if Decimal(payload.quantity) > current_quantity:
                raise build_http_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Cannot sell more than the current asset position.",
                    error_code="INSUFFICIENT_ASSET_POSITION",
                )

        transaction = Transaction(user_id=user_id, wallet_id=wallet.id, **payload.model_dump())
        self.db.add(transaction)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Unable to create transaction.",
                error_code="TRANSACTION_CREATE_FAILED",
            ) from exc
        self.db.refresh(transaction)
        return self.get_transaction_by_id(transaction.id, user_id, wallet_id=wallet.id)

    def delete_transaction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        wallet_id: UUID | None = None,
    ) -> None:
        transaction = self.get_transaction_by_id(transaction_id, user_id, wallet_id=wallet_id)
        self.db.delete(transaction)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Unable to delete transaction.",
                error_code="TRANSACTION_DELETE_FAILED",
            ) from exc

    def get_portfolio_summary(
        self,
        user_id: UUID,
        wallet_id: UUID | None = None,
    ) -> PortfolioSummaryResponse:
        if wallet_id is not None:
            self._get_wallet_by_id(wallet_id, user_id)

        holdings = self._calculate_user_asset_state(user_id=user_id, wallet_id=wallet_id)
        asset_summaries: list[PortfolioAssetSummary] = []
        total_invested = Decimal("0")
        total_realized_profit_loss = Decimal("0")
        total_unrealized_profit_loss = Decimal("0")
        total_current_value = Decimal("0")

        for asset_state in holdings.values():
            total_quantity = Decimal(asset_state["quantity"])
            cost_basis = Decimal(asset_state["cost_basis"])
            gross_invested = Decimal(asset_state["gross_invested"])
            realized_profit_loss = Decimal(asset_state["realized_profit_loss"])

            if total_quantity <= 0:
                total_realized_profit_loss += realized_profit_loss
                continue

            asset = asset_state["asset"]
            if not isinstance(asset, Asset):
                continue

            average_price = cost_basis / total_quantity if total_quantity > 0 else Decimal("0")
            current_price = Decimal(asset.current_price)
            current_value = total_quantity * current_price
            unrealized_profit_loss = current_value - cost_basis
            profit_loss = realized_profit_loss + unrealized_profit_loss
            profit_loss_pct = (
                (profit_loss / gross_invested) * Decimal("100")
                if gross_invested > 0
                else Decimal("0")
            )

            asset_summaries.append(
                PortfolioAssetSummary(
                    ticker=asset.ticker,
                    total_quantity=total_quantity,
                    average_price=average_price,
                    current_price=current_price,
                    current_value=current_value,
                    realized_profit_loss=realized_profit_loss,
                    unrealized_profit_loss=unrealized_profit_loss,
                    profit_loss=profit_loss,
                    profit_loss_pct=profit_loss_pct,
                )
            )

            total_invested += cost_basis
            total_realized_profit_loss += realized_profit_loss
            total_unrealized_profit_loss += unrealized_profit_loss
            total_current_value += current_value

        total_profit_loss = total_realized_profit_loss + total_unrealized_profit_loss

        return PortfolioSummaryResponse(
            assets=sorted(asset_summaries, key=lambda item: item.ticker),
            total_invested=total_invested,
            total_realized_profit_loss=total_realized_profit_loss,
            total_unrealized_profit_loss=total_unrealized_profit_loss,
            total_current_value=total_current_value,
            total_profit_loss=total_profit_loss,
        )
