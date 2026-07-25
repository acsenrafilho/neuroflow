"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from neuroflow import __version__
from neuroflow.api.deps import get_cached_settings
from neuroflow.api.host_state import run_host_scan
from neuroflow.api.v1.router import api_router
from neuroflow.logging_config import configure_app_logging
from neuroflow.models.schemas import ErrorDetail
from neuroflow.tools.host_probe import log_scan_summary


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_cached_settings()
    configure_app_logging(settings.neuroflow_log_level)
    settings.data_root.mkdir(parents=True, exist_ok=True)
    settings.datasets_root.mkdir(parents=True, exist_ok=True)
    results = run_host_scan(app)
    log_scan_summary(results)

    from neuroflow.services.job_scheduler import start_scheduler, stop_scheduler

    start_scheduler()

    if settings.neuroflow_serve_frontend:
        dist = Path("frontend/dist")
        if dist.is_dir():
            app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")

    yield
    stop_scheduler()


# MVP: no authentication. Deploy only on trusted networks; see docs/security.md.
app = FastAPI(
    title="NeuroFlow API",
    version=__version__,
    description="Web API for per-tool neuroimaging CLI jobs (upload, run, logs).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"https?://(127\.0\.0\.1|localhost)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "http_error"
    if exc.headers and "X-Error-Code" in exc.headers:
        code = exc.headers["X-Error-Code"]
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    body = ErrorDetail(detail=detail, code=code).model_dump()
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    body = ErrorDetail(
        detail="Request validation failed",
        code="validation_error",
        field=str(exc.errors()[0].get("loc")) if exc.errors() else None,
    ).model_dump()
    return JSONResponse(status_code=422, content=body)


@app.get("/", response_model=None)
async def root():
    settings = get_cached_settings()
    if settings.neuroflow_serve_frontend:
        index = Path("frontend/dist/index.html")
        if index.is_file():
            return FileResponse(index)
    return {"service": "neuroflow", "docs": "/docs", "api": "/api/v1/health"}
