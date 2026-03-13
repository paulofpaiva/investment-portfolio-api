from sqlalchemy.orm import Session


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ping(self) -> str:
        return "auth-service"
