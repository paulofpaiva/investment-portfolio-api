from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router


app = FastAPI(
    title="Investment Portfolio API",
    version="0.1.0",
    description="Production-oriented FastAPI project for investment portfolio management.",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        content = {
            "message": exc.detail.get("message", "Request failed."),
            "error_code": exc.detail.get("error_code", "HTTP_ERROR"),
            "status_code": exc.detail.get("status_code", exc.status_code),
        }
    else:
        content = {
            "message": str(exc.detail),
            "error_code": "HTTP_ERROR",
            "status_code": exc.status_code,
        }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    del exc
    return JSONResponse(
        status_code=400,
        content={
            "message": "Invalid request payload.",
            "error_code": "VALIDATION_ERROR",
            "status_code": 400,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    del exc
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error.",
            "error_code": "INTERNAL_SERVER_ERROR",
            "status_code": 500,
        },
    )


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
