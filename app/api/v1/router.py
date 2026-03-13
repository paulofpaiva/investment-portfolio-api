from fastapi import APIRouter

from app.api.v1.endpoints.assets import router as assets_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.portfolio import router as portfolio_router
from app.api.v1.endpoints.transactions import router as transactions_router
from app.api.v1.endpoints.wallets import router as wallets_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(assets_router)
api_router.include_router(wallets_router)
api_router.include_router(transactions_router)
api_router.include_router(portfolio_router)
