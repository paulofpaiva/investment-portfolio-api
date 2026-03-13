from uuid import UUID

from fastapi import status
from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import build_http_error
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletUpdate


class WalletService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_wallets(self, user_id: UUID) -> list[Wallet]:
        statement: Select[tuple[Wallet]] = (
            select(Wallet)
            .where(Wallet.user_id == user_id)
            .order_by(Wallet.is_default.desc(), Wallet.created_at.asc())
        )
        return list(self.db.execute(statement).scalars().all())

    def get_wallet_by_id(self, wallet_id: UUID, user_id: UUID) -> Wallet:
        statement = select(Wallet).where(Wallet.id == wallet_id, Wallet.user_id == user_id)
        wallet = self.db.execute(statement).scalar_one_or_none()
        if wallet is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Wallet not found.",
                error_code="WALLET_NOT_FOUND",
            )
        return wallet

    def get_default_wallet(self, user_id: UUID) -> Wallet:
        statement = select(Wallet).where(Wallet.user_id == user_id, Wallet.is_default.is_(True))
        wallet = self.db.execute(statement).scalar_one_or_none()
        if wallet is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Default wallet not found.",
                error_code="DEFAULT_WALLET_NOT_FOUND",
            )
        return wallet

    def create_wallet(self, user_id: UUID, payload: WalletCreate) -> Wallet:
        wallet = Wallet(user_id=user_id, name=payload.name, is_default=False)
        self.db.add(wallet)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Unable to create wallet.",
                error_code="WALLET_CREATE_FAILED",
            ) from exc
        self.db.refresh(wallet)
        return wallet

    def update_wallet(self, wallet_id: UUID, user_id: UUID, payload: WalletUpdate) -> Wallet:
        wallet = self.get_wallet_by_id(wallet_id, user_id)
        wallet.name = payload.name
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Unable to update wallet.",
                error_code="WALLET_UPDATE_FAILED",
            ) from exc
        self.db.refresh(wallet)
        return wallet

    def wallet_has_transactions(self, wallet_id: UUID) -> bool:
        statement = select(func.count()).select_from(Transaction).where(Transaction.wallet_id == wallet_id)
        return int(self.db.execute(statement).scalar_one()) > 0

    def delete_wallet(self, wallet_id: UUID, user_id: UUID) -> None:
        wallet = self.get_wallet_by_id(wallet_id, user_id)
        if wallet.is_default:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Default wallet cannot be deleted.",
                error_code="DEFAULT_WALLET_DELETE_FORBIDDEN",
            )
        if self.wallet_has_transactions(wallet_id):
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Cannot delete wallet with existing transactions.",
                error_code="WALLET_HAS_TRANSACTIONS",
            )

        self.db.delete(wallet)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Unable to delete wallet.",
                error_code="WALLET_DELETE_FAILED",
            ) from exc
