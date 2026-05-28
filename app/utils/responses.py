from fastapi.responses import JSONResponse
from typing import Any, Optional


def success_response(data: Any = None, message: str = "Succès", status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def error_response(message: str, status_code: int = 400, detail: Optional[Any] = None):
    content = {"success": False, "message": message}
    if detail:
        content["detail"] = detail
    return JSONResponse(status_code=status_code, content=content)
