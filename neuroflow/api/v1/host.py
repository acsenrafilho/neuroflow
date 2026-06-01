"""Host environment scan endpoints."""

from fastapi import APIRouter, Request

from neuroflow.api.host_state import run_host_scan
from neuroflow.models.schemas import HostScanResponse, PackageProbeInfo
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
