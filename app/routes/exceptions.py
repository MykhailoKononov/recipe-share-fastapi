from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.schemas.responses.api_schema_resp import APIResponse


async def custom_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    errors = []
    for err in exc.errors():
        loc = [str(l) for l in err["loc"] if l != "body"]
        field = ".".join(loc)
        errors.append(f"{field or 'body'}: {err['msg']}")
    payload = APIResponse(
        status="error",
        message="Validation failed",
        errors=errors
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(exclude_none=True),
    )
