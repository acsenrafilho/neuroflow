"""Read portal package readiness from Windows after the Linux portal is healthy."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from neuroflow.windows_launcher.types import (
    HOST_TOOLS_URL,
    PORTAL_PACKAGE_IDS,
    PORTAL_URL,
    TOOLS_URL,
)

TOOLS_REQUEST_TIMEOUT_SECONDS = 2.0


def portal_tools_missing(packages: Any) -> bool | None:
    """Return whether every portal package is present and unavailable.

    Parameters
    ----------
    packages:
        Parsed JSON from ``GET /api/v1/tools`` (expected: a list of dicts).

    Returns
    -------
    True
        Every portal package id is present and ``available`` is false.
    False
        At least one portal package is available.
    None
        Empty, malformed, or incomplete payload (treat as scan failure).
    """
    if not isinstance(packages, list) or not packages:
        return None

    by_id: dict[str, bool] = {}
    for item in packages:
        if not isinstance(item, dict):
            return None
        pkg_id = item.get("id")
        if not isinstance(pkg_id, str) or not pkg_id:
            return None
        available = item.get("available")
        if not isinstance(available, bool):
            return None
        by_id[pkg_id] = available

    if not PORTAL_PACKAGE_IDS.issubset(by_id):
        return None

    return all(not by_id[pkg_id] for pkg_id in PORTAL_PACKAGE_IDS)


def fetch_tools(url: str = TOOLS_URL) -> list[Any] | None:
    """GET ``/api/v1/tools`` once; return the JSON list or None on any failure."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=TOOLS_REQUEST_TIMEOUT_SECONDS) as resp:  # noqa: S310
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
            if not isinstance(data, list):
                return None
            return data
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
        OSError,
    ):
        return None


def choose_landing_url(*, tools_url: str = TOOLS_URL) -> tuple[str, bool]:
    """Pick Home or Host tools help after health OK.

    Returns
    -------
    (url, all_portal_missing)
        ``all_portal_missing`` is True only when the scan succeeded and every
        portal package is unavailable. Scan failures fail-open to Home.
    """
    packages = fetch_tools(tools_url)
    if packages is None:
        return PORTAL_URL, False
    missing = portal_tools_missing(packages)
    if missing is True:
        return HOST_TOOLS_URL, True
    return PORTAL_URL, False
