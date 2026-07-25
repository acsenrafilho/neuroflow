"""Aggregate job listing endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from neuroflow.api.deps import get_job_store
from neuroflow.models.schemas import JobSummary
from neuroflow.services.job_list import list_jobs
from neuroflow.services.jobs import JobStore

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobSummary])
async def list_all_jobs(
    store: Annotated[JobStore, Depends(get_job_store)],
    status: Annotated[str | None, Query(description="Comma-separated statuses")] = "running,queued",
) -> list[JobSummary]:
    statuses: set[str] | None = None
    if status and status.strip():
        statuses = {part.strip() for part in status.split(",") if part.strip()}
    rows = list_jobs(store, statuses=statuses)
    return [JobSummary.model_validate(row) for row in rows]
