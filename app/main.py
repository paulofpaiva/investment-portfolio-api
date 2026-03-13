from fastapi import FastAPI

from app.api.v1.router import api_router


app = FastAPI(
    title="Investment Portfolio API",
    version="0.1.0",
    description="Production-oriented FastAPI project for investment portfolio management.",
)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
