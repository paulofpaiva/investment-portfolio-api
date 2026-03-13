from fastapi import APIRouter


router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/status")
def assets_status() -> dict[str, str]:
    return {"module": "assets", "status": "placeholder"}
