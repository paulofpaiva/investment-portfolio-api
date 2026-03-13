from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import build_http_error
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.user import UserCreate


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.db.execute(statement).scalar_one_or_none()

    def get_user_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def register_user(self, payload: UserCreate) -> User:
        existing_user = self.get_user_by_email(payload.email)
        if existing_user is not None:
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email is already registered.",
                error_code="EMAIL_ALREADY_REGISTERED",
            )

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
        )
        default_wallet = Wallet(name="Default", is_default=True, user=user)
        self.db.add(user)
        self.db.add(default_wallet)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Email is already registered.",
                error_code="EMAIL_ALREADY_REGISTERED",
            ) from exc
        self.db.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.get_user_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise build_http_error(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Invalid credentials.",
                error_code="INVALID_CREDENTIALS",
            )
        return user

    def create_user_token(self, user: User) -> str:
        return create_access_token({"sub": str(user.id)})


def get_auth_service(db: Annotated[Session, Depends(get_db)]) -> AuthService:
    return AuthService(db)


def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    credentials_exception = build_http_error(
        status_code=status.HTTP_400_BAD_REQUEST,
        message="Could not validate credentials.",
        error_code="INVALID_AUTH_TOKEN",
    )

    if token is None:
        raise build_http_error(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Authentication token is required.",
            error_code="AUTH_TOKEN_REQUIRED",
        )

    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise credentials_exception
        user_id = UUID(subject)
    except (ValueError, TypeError):
        raise credentials_exception

    service = AuthService(db)
    user = service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
