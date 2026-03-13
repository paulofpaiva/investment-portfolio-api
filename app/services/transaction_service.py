from sqlalchemy.orm import Session


class TransactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ping(self) -> str:
        return "transaction-service"
