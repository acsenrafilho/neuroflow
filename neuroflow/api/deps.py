"""FastAPI dependencies."""

from functools import lru_cache

from neuroflow.config import Settings
from neuroflow.services.jobs import JobStore


@lru_cache
def get_cached_settings() -> Settings:
    return Settings()


def get_job_store() -> JobStore:
    return JobStore(get_cached_settings())
