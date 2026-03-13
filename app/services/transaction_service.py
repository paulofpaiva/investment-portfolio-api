from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.models.asset import Asset
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate


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
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found.",
            )
        return transaction

    def create_transaction(self, user_id: UUID, payload: TransactionCreate) -> Transaction:
        asset = self.db.get(Asset, payload.asset_id)
        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found.",
            )

        transaction = Transaction(user_id=user_id, **payload.model_dump())
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return self.get_transaction_by_id(transaction.id, user_id)

    def delete_transaction(self, transaction_id: UUID, user_id: UUID) -> None:
        transaction = self.get_transaction_by_id(transaction_id, user_id)
        self.db.delete(transaction)
        self.db.commit()
