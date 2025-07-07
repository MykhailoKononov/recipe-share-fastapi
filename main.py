import random
import time

import sentry_sdk
import uvicorn
import logging
import httpx
from fastapi.exceptions import RequestValidationError

from app.routes.exceptions import custom_validation_exception_handler
from config import Config

from fastapi import FastAPI, Response, APIRouter
from opentelemetry.propagate import inject

from app.routes.moderator_route import moderator_router
from app.routes.auth_route import user_router, auth_router
from app.routes.admin_route import admin_router
from app.routes.profile_route import profile_router
from utils.prometheus_logging import PrometheusMiddleware, metrics, setting_otlp


APP_NAME = "fastapi"


# Create FastAPI app
app = FastAPI(
    title="Recipe Share",
    exception_handlers={
        RequestValidationError: custom_validation_exception_handler
    }
)


# Prometheus
app.add_middleware(PrometheusMiddleware, app_name=APP_NAME)
app.add_route("/metrics", metrics)

if not Config.DEBUG:
    setting_otlp(app, APP_NAME, "http://tempo:4317")


# Filter Logging
class EndpointFilter(logging.Filter):
    # Uvicorn endpoint access log filter
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("GET /metrics") == -1


# Filter out /endpoint
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())

test_router = APIRouter(tags=["Testing"])

@test_router.get("/io_task")
async def io_task():
    time.sleep(1)
    logging.error("io task")
    return "IO bound task finish!"


@test_router.get("/cpu_task")
async def cpu_task():
    for i in range(1000):
        _ = i * i * i
    logging.error("cpu task")
    return "CPU bound task finish!"


@test_router.get("/random_status")
async def random_status(response: Response):
    response.status_code = random.choice([200, 200, 300, 400, 500])
    logging.error("random status")
    return {"path": "/random_status"}


@test_router.get("/random_sleep")
async def random_sleep(response: Response):
    time.sleep(random.randint(0, 5))
    logging.error("random sleep")
    return {"path": "/random_sleep"}


@test_router.get("/error_test")
async def error_test(response: Response):
    logging.error("got error!!!!")
    raise ValueError("value error")


@test_router.get("/chain")
async def chain(response: Response):
    headers = {}
    inject(headers)
    logging.critical(headers)

    async with httpx.AsyncClient() as client:
        await client.get(
            "http://localhost:8000/",
            headers=headers,
        )
    async with httpx.AsyncClient() as client:
        await client.get(
            f"http://localhost:8000/io_task",
            headers=headers,
        )
    async with httpx.AsyncClient() as client:
        await client.get(
            f"http://localhost:8000/cpu_task",
            headers=headers,
        )
    logging.info("Chain Finished")
    return {"path": "/chain"}


if not Config.DEBUG:
    # Sentry
    sentry_sdk.init(
        dsn=Config.SENTRY_URL,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        traces_sample_rate=1.0,
    )


# Routers
app.include_router(profile_router, prefix="/profile")
app.include_router(user_router, prefix="/user")
app.include_router(auth_router, prefix="/auth")
app.include_router(moderator_router, prefix="/moderator")
app.include_router(admin_router, prefix="/admin")
app.include_router(test_router)

if __name__ == "__main__":
    if not Config.DEBUG:
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["access"][
            "fmt"
        ] = "%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s resource.service.name=%(otelServiceName)s] - %(message)s"
        uvicorn.run(app, host="0.0.0.0", port=8000, log_config=log_config)
    else:
        uvicorn.run(app, host="127.0.0.1", port=8000)
