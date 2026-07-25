"""FastAPI dependencies."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from neuroflow.config import Settings
from neuroflow.services.jobs import JobStore


@lru_cache
def get_cached_settings() -> Settings:
    return Settings()


def get_job_store(
    settings: Annotated[Settings, Depends(get_cached_settings)],
) -> JobStore:
    return JobStore(settings)
