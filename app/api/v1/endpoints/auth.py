from fastapi import APIRouter


router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/status")
def auth_status() -> dict[str, str]:
    return {"module": "auth", "status": "placeholder"}
