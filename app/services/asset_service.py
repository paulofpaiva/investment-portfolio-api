from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate


class AssetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_assets(self, skip: int = 0, limit: int = 100) -> list[Asset]:
        statement = select(Asset).offset(skip).limit(limit)
        return list(self.db.execute(statement).scalars().all())

    def get_asset_by_id(self, asset_id: UUID) -> Asset:
        asset = self.db.get(Asset, asset_id)
        if asset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found.",
            )
        return asset

    def get_asset_by_ticker(self, ticker: str) -> Asset | None:
        statement = select(Asset).where(Asset.ticker == ticker)
        return self.db.execute(statement).scalar_one_or_none()

    def create_asset(self, payload: AssetCreate) -> Asset:
        existing_asset = self.get_asset_by_ticker(payload.ticker)
        if existing_asset is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset with this ticker already exists.",
            )

        asset = Asset(**payload.model_dump())
        self.db.add(asset)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset with this ticker already exists.",
            ) from exc
        self.db.refresh(asset)
        return asset

    def update_asset(self, asset_id: UUID, payload: AssetUpdate) -> Asset:
        asset = self.get_asset_by_id(asset_id)
        if payload.ticker is not None and payload.ticker != asset.ticker:
            existing_asset = self.get_asset_by_ticker(payload.ticker)
            if existing_asset is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Asset with this ticker already exists.",
                )

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(asset, field, value)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset with this ticker already exists.",
            ) from exc
        self.db.refresh(asset)
        return asset

    def delete_asset(self, asset_id: UUID) -> None:
        asset = self.get_asset_by_id(asset_id)
        self.db.delete(asset)
        self.db.commit()
