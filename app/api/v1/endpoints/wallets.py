from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.transaction import TransactionType
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.transaction import (
    PortfolioSummaryResponse,
    TransactionCreate,
    TransactionResponse,
)
from app.schemas.wallet import WalletCreate, WalletResponse, WalletUpdate
from app.services.auth_service import get_current_user
from app.services.transaction_service import TransactionService
from app.services.wallet_service import WalletService


router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("/", response_model=list[WalletResponse])
def list_wallets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WalletResponse]:
    service = WalletService(db)
    return service.list_wallets(current_user.id)


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
def create_wallet(
    payload: WalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WalletResponse:
    service = WalletService(db)
    return service.create_wallet(current_user.id, payload)


@router.get("/{wallet_id}", response_model=WalletResponse)
def get_wallet(
    wallet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WalletResponse:
    service = WalletService(db)
    return service.get_wallet_by_id(wallet_id, current_user.id)


@router.put("/{wallet_id}", response_model=WalletResponse)
def update_wallet(
    wallet_id: UUID,
    payload: WalletUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WalletResponse:
    service = WalletService(db)
    return service.update_wallet(wallet_id, current_user.id, payload)


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(
    wallet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    service = WalletService(db)
    service.delete_wallet(wallet_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{wallet_id}/transactions", response_model=PaginatedResponse[TransactionResponse])
def list_wallet_transactions(
    wallet_id: UUID,
    skip: int = 0,
    limit: int = 100,
    asset_id: UUID | None = None,
    transaction_type: TransactionType | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[TransactionResponse]:
    service = TransactionService(db)
    items, total = service.list_transactions(
        user_id=current_user.id,
        wallet_id=wallet_id,
        asset_id=asset_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )
    return PaginatedResponse[TransactionResponse](items=items, total=total, skip=skip, limit=limit)


@router.post("/{wallet_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_wallet_transaction(
    wallet_id: UUID,
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    service = TransactionService(db)
    return service.create_transaction(current_user.id, payload, wallet_id=wallet_id)


@router.get("/{wallet_id}/transactions/{transaction_id}", response_model=TransactionResponse)
def get_wallet_transaction(
    wallet_id: UUID,
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResponse:
    service = TransactionService(db)
    return service.get_transaction_by_id(transaction_id, current_user.id, wallet_id=wallet_id)


@router.delete("/{wallet_id}/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet_transaction(
    wallet_id: UUID,
    transaction_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    service = TransactionService(db)
    service.delete_transaction(transaction_id, current_user.id, wallet_id=wallet_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{wallet_id}/summary", response_model=PortfolioSummaryResponse)
def get_wallet_summary(
    wallet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PortfolioSummaryResponse:
    service = TransactionService(db)
    return service.get_portfolio_summary(current_user.id, wallet_id=wallet_id)
