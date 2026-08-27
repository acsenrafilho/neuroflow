"""Health checks against the NeuroFlow portal from Windows."""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from neuroflow.windows_launcher.types import HEALTH_URL, PORTAL_HOST, PORTAL_PORT

HEALTH_REQUEST_TIMEOUT_SECONDS = 2.0
HEALTH_POLL_INTERVAL_SECONDS = 0.5
HEALTH_POLL_BUDGET_SECONDS = 45.0


class HealthStatus(str, Enum):
    """Outcome of a single health probe."""

    OK = "ok"
    DOWN = "down"
    PORT_BUSY = "port_busy"
    BAD_RESPONSE = "bad_response"


@dataclass(frozen=True)
class HealthResult:
    """Result of probing the portal health endpoint."""

    status: HealthStatus
    version: str | None = None
    detail: str | None = None


def _tcp_port_open(
    host: str = PORTAL_HOST,
    port: int = PORTAL_PORT,
    *,
    timeout: float = 0.5,
) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_health(url: str = HEALTH_URL) -> HealthResult:
    """GET ``/api/v1/health`` once; classify ok / down / port-busy / bad."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=HEALTH_REQUEST_TIMEOUT_SECONDS) as resp:  # noqa: S310
            body = resp.read()
            if resp.status != 200:
                if _tcp_port_open():
                    return HealthResult(
                        HealthStatus.PORT_BUSY,
                        detail=f"HTTP {resp.status}",
                    )
                return HealthResult(HealthStatus.DOWN, detail=f"HTTP {resp.status}")
            data = json.loads(body.decode("utf-8"))
            if isinstance(data, dict) and data.get("status") == "ok":
                version = data.get("version")
                return HealthResult(
                    HealthStatus.OK,
                    version=str(version) if version is not None else None,
                )
            if _tcp_port_open():
                return HealthResult(
                    HealthStatus.PORT_BUSY,
                    detail="health JSON missing status=ok",
                )
            return HealthResult(HealthStatus.BAD_RESPONSE, detail="unexpected JSON")
    except urllib.error.HTTPError as exc:
        if _tcp_port_open():
            return HealthResult(HealthStatus.PORT_BUSY, detail=str(exc))
        return HealthResult(HealthStatus.DOWN, detail=str(exc))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        if _tcp_port_open():
            # Something is listening but it is not NeuroFlow health.
            return HealthResult(HealthStatus.PORT_BUSY, detail=str(exc))
        return HealthResult(HealthStatus.DOWN, detail=str(exc))


def wait_until_healthy(
    *,
    url: str = HEALTH_URL,
    budget_seconds: float = HEALTH_POLL_BUDGET_SECONDS,
    interval_seconds: float = HEALTH_POLL_INTERVAL_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> HealthResult:
    """Poll health until OK, PORT_BUSY, or the budget expires (DOWN)."""
    deadline = time.monotonic() + budget_seconds
    last = HealthResult(HealthStatus.DOWN, detail="not probed")
    while time.monotonic() < deadline:
        last = probe_health(url)
        if last.status == HealthStatus.OK:
            return last
        if last.status == HealthStatus.PORT_BUSY:
            return last
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        sleep(min(interval_seconds, remaining))
    return last if last.status != HealthStatus.OK else last
