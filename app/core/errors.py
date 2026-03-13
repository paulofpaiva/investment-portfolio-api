from fastapi import HTTPException


def build_http_error(status_code: int, message: str, error_code: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "message": message,
            "error_code": error_code,
            "status_code": status_code,
        },
    )
