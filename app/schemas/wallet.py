from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WalletCreate(BaseModel):
    name: str


class WalletUpdate(BaseModel):
    name: str


class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    is_default: bool
    created_at: datetime
