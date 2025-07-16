from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import http_exception_handler
from starlette.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

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
        success=False,
        message="Validation failed",
        errors=errors
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(exclude_none=True),
    )


async def custom_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> Response | JSONResponse:
    if exc.status_code in (status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE):
        payload = APIResponse(
            success=False,
            message="File upload error",
            errors=[str(exc.detail)]
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(exclude_none=True),
        )

    return await http_exception_handler(request, exc)
