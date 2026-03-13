from pydantic import BaseModel


class AssetCreate(BaseModel):
    ticker: str
    name: str


class AssetResponse(BaseModel):
    id: int
    ticker: str
    name: str
