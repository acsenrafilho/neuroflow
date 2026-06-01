"""Shared access to cached host tool availability on the FastAPI app."""

from __future__ import annotations

from fastapi import FastAPI, Request

from neuroflow.api.deps import get_cached_settings
from neuroflow.tools.host_probe import (
    TOOL_AVAILABILITY_STATE_KEY,
    ProbeResult,
    scan_all_packages,
)


def run_host_scan(app: FastAPI) -> dict[str, ProbeResult]:
    settings = get_cached_settings()
    results = scan_all_packages(settings)
    setattr(app.state, TOOL_AVAILABILITY_STATE_KEY, results)
    return results


def get_tool_availability(request: Request) -> dict[str, ProbeResult]:
    cached = getattr(request.app.state, TOOL_AVAILABILITY_STATE_KEY, None)
    if cached is not None:
        return cached
    return run_host_scan(request.app)
