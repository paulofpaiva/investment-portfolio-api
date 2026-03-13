from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    asset_id: UUID
    transaction_type: TransactionType
    quantity: Decimal
    price_per_unit: Decimal


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    wallet_id: UUID
    asset_id: UUID
    transaction_type: TransactionType
    quantity: Decimal
    price_per_unit: Decimal
    total_value: Decimal
    transacted_at: datetime
    created_at: datetime
    asset_ticker: str
    asset_name: str


class PortfolioAssetSummary(BaseModel):
    ticker: str
    total_quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    current_value: Decimal
    realized_profit_loss: Decimal
    unrealized_profit_loss: Decimal
    profit_loss: Decimal
    profit_loss_pct: Decimal


class PortfolioSummaryResponse(BaseModel):
    assets: list[PortfolioAssetSummary]
    total_invested: Decimal
    total_realized_profit_loss: Decimal
    total_unrealized_profit_loss: Decimal
    total_current_value: Decimal
    total_profit_loss: Decimal
