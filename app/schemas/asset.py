from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.asset import AssetType


class AssetCreate(BaseModel):
    ticker: str
    name: str
    asset_type: AssetType
    current_price: Decimal


class AssetUpdate(BaseModel):
    ticker: str | None = None
    name: str | None = None
    asset_type: AssetType | None = None
    current_price: Decimal | None = None


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ticker: str
    name: str
    asset_type: AssetType
    current_price: Decimal
    created_at: datetime
