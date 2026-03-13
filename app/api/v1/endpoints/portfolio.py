from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.transaction import PortfolioSummaryResponse
from app.services.auth_service import get_current_user
from app.services.transaction_service import TransactionService


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/summary", response_model=PortfolioSummaryResponse)
def get_portfolio_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PortfolioSummaryResponse:
    service = TransactionService(db)
    return service.get_portfolio_summary(current_user.id)
