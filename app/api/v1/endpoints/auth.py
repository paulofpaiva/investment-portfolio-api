from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.schemas.user import TokenResponse, UserCreate, UserLogin
from app.services.auth_service import AuthService, get_auth_service


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user = auth_service.register_user(payload)
    access_token = auth_service.create_user_token(user)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    user = auth_service.authenticate_user(payload.email, payload.password)
    access_token = auth_service.create_user_token(user)
    return TokenResponse(access_token=access_token)
