"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from neuroflow import __version__
from neuroflow.api.deps import get_cached_settings
from neuroflow.api.v1.router import api_router
from neuroflow.models.schemas import ErrorDetail

# MVP: no authentication. Deploy only on trusted networks; see docs/security.md.
app = FastAPI(
    title="NeuroFlow API",
    version=__version__,
    description="Facilitation portal API for BIDS-oriented neuroimaging workflows.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
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


@app.on_event("startup")
def mount_frontend_if_enabled() -> None:
    settings = get_cached_settings()
    if not settings.neuroflow_serve_frontend:
        return
    dist = Path("frontend/dist")
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="frontend")


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "neuroflow", "docs": "/docs", "api": "/api/v1/health"}
