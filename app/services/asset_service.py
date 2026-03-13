from sqlalchemy.orm import Session


class AssetService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ping(self) -> str:
        return "asset-service"
