"""Host environment scan endpoints."""

from __future__ import annotations

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from neuroflow.api.deps import get_cached_settings, get_job_store
from neuroflow.api.host_state import run_host_scan
from neuroflow.config import Settings
from neuroflow.models.schemas import HostResourcesResponse, HostScanResponse, PackageProbeInfo
from neuroflow.services.host_resources import sample_host_resources
from neuroflow.services.job_list import count_jobs_with_status
from neuroflow.services.jobs import JobStore
from neuroflow.tools.host_probe import ProbeResult

router = APIRouter(prefix="/host", tags=["host"])


def _results_to_response(results: dict[str, ProbeResult]) -> HostScanResponse:
    packages = [
        PackageProbeInfo(
            package_id=probe.package_id,
            available=probe.available,
            resolved_path=probe.resolved_path,
            detail=probe.detail,
        )
        for probe in sorted(results.values(), key=lambda p: p.package_id)
    ]
    return HostScanResponse(packages=packages)


@router.post("/rescan", response_model=HostScanResponse)
async def rescan_host_tools(request: Request) -> HostScanResponse:
    """Re-run local package probes (e.g. after sourcing FreeSurfer setup)."""
    results = run_host_scan(request.app)
    return _results_to_response(results)


@router.get("/resources", response_model=HostResourcesResponse)
async def get_host_resources(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
) -> HostResourcesResponse:
    # sample_host_resources sleeps briefly for CPU%; count_jobs scans disk.
    sample, queued = await asyncio.gather(
        asyncio.to_thread(sample_host_resources, settings),
        asyncio.to_thread(count_jobs_with_status, store, {"queued"}),
    )
    queue_full = queued >= settings.neuroflow_max_queued_jobs
    block_reason = sample.block_reason
    if queue_full:
        block_reason = f"Job queue is full ({settings.neuroflow_max_queued_jobs})"
    return HostResourcesResponse(
        memory_percent=sample.memory_percent,
        cpu_percent=sample.cpu_percent,
        ram_max_percent=sample.ram_max_percent,
        cpu_max_percent=sample.cpu_max_percent,
        can_start_job=sample.can_start_job,
        can_accept_job=not queue_full,
        block_reason=block_reason,
        queued_jobs=queued,
        max_queued_jobs=settings.neuroflow_max_queued_jobs,
    )
