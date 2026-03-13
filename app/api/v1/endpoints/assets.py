from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetResponse, AssetUpdate
from app.services.asset_service import AssetService
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=list[AssetResponse])
def list_assets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[AssetResponse]:
    service = AssetService(db)
    return service.list_assets(skip=skip, limit=limit)


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AssetResponse:
    service = AssetService(db)
    return service.get_asset_by_id(asset_id)


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AssetResponse:
    service = AssetService(db)
    return service.create_asset(payload)


@router.put("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> AssetResponse:
    service = AssetService(db)
    return service.update_asset(asset_id, payload)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Response:
    service = AssetService(db)
    service.delete_asset(asset_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
