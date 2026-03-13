from decimal import Decimal

from pydantic import BaseModel


class TransactionCreate(BaseModel):
    asset_id: int
    quantity: Decimal
    unit_price: Decimal


class TransactionResponse(BaseModel):
    id: int
    asset_id: int
    quantity: Decimal
    unit_price: Decimal
