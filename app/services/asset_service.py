from uuid import UUID

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import build_http_error
from app.models.asset import Asset
from app.models.transaction import Transaction
from app.schemas.asset import AssetCreate, AssetUpdate


class AssetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_assets(self, skip: int = 0, limit: int = 100) -> tuple[list[Asset], int]:
        items_statement = select(Asset).order_by(Asset.created_at.desc()).offset(skip).limit(limit)
        total_statement = select(func.count()).select_from(Asset)

        items = list(self.db.execute(items_statement).scalars().all())
        total = int(self.db.execute(total_statement).scalar_one())
        return items, total

    def get_asset_by_id(self, asset_id: UUID) -> Asset:
        asset = self.db.get(Asset, asset_id)
        if asset is None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Asset not found.",
                error_code="ASSET_NOT_FOUND",
            )
        return asset

    def get_asset_by_ticker(self, ticker: str) -> Asset | None:
        statement = select(Asset).where(Asset.ticker == ticker)
        return self.db.execute(statement).scalar_one_or_none()

    def asset_has_transactions(self, asset_id: UUID) -> bool:
        statement = select(Transaction.id).where(Transaction.asset_id == asset_id).limit(1)
        return self.db.execute(statement).scalar_one_or_none() is not None

    def create_asset(self, payload: AssetCreate) -> Asset:
        existing_asset = self.get_asset_by_ticker(payload.ticker)
        if existing_asset is not None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Asset with this ticker already exists.",
                error_code="ASSET_TICKER_EXISTS",
            )

        asset = Asset(**payload.model_dump())
        self.db.add(asset)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Asset with this ticker already exists.",
                error_code="ASSET_TICKER_EXISTS",
            ) from exc
        self.db.refresh(asset)
        return asset

    def update_asset(self, asset_id: UUID, payload: AssetUpdate) -> Asset:
        asset = self.get_asset_by_id(asset_id)
        if payload.ticker is not None and payload.ticker != asset.ticker:
            existing_asset = self.get_asset_by_ticker(payload.ticker)
            if existing_asset is not None:
                raise build_http_error(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="Asset with this ticker already exists.",
                    error_code="ASSET_TICKER_EXISTS",
                )

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(asset, field, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Asset with this ticker already exists.",
                error_code="ASSET_TICKER_EXISTS",
            ) from exc
        self.db.refresh(asset)
        return asset

    def delete_asset(self, asset_id: UUID) -> None:
        asset = self.get_asset_by_id(asset_id)
        if self.asset_has_transactions(asset_id):
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Cannot delete asset with existing transactions.",
                error_code="ASSET_HAS_TRANSACTIONS",
            )

        self.db.delete(asset)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Cannot delete asset with existing transactions.",
                error_code="ASSET_HAS_TRANSACTIONS",
            ) from exc
