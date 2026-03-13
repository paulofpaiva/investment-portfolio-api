from fastapi import APIRouter


router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("/status")
def transactions_status() -> dict[str, str]:
    return {"module": "transactions", "status": "placeholder"}
