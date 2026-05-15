"""Health check endpoint."""

from fastapi import APIRouter

from neuroflow import __version__
from neuroflow.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)
