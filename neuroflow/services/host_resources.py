"""Host RAM/CPU resource checks for job admission (Linux /proc, no extra deps)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from neuroflow.config import Settings

_PROC_MEMINFO = Path("/proc/meminfo")
_PROC_STAT = Path("/proc/stat")


@dataclass(frozen=True)
class HostResources:
    memory_percent: float
    cpu_percent: float
    ram_max_percent: float
    cpu_max_percent: float
    can_start_job: bool
    block_reason: str | None = None


def _memory_percent() -> float:
    if not _PROC_MEMINFO.is_file():
        # Non-Linux fallback: assume healthy so local tests can proceed.
        return 0.0
    total_kb = 0
    available_kb = 0
    free_kb = 0
    buffers_kb = 0
    cached_kb = 0
    for line in _PROC_MEMINFO.read_text(encoding="utf-8").splitlines():
        if line.startswith("MemTotal:"):
            total_kb = int(line.split()[1])
        elif line.startswith("MemAvailable:"):
            available_kb = int(line.split()[1])
        elif line.startswith("MemFree:"):
            free_kb = int(line.split()[1])
        elif line.startswith("Buffers:"):
            buffers_kb = int(line.split()[1])
        elif line.startswith("Cached:"):
            cached_kb = int(line.split()[1])
    if total_kb <= 0:
        return 0.0
    if available_kb <= 0:
        available_kb = free_kb + buffers_kb + cached_kb
    used = max(0, total_kb - available_kb)
    return round(100.0 * used / total_kb, 1)


def _read_cpu_times() -> tuple[int, int] | None:
    if not _PROC_STAT.is_file():
        return None
    for line in _PROC_STAT.read_text(encoding="utf-8").splitlines():
        if not line.startswith("cpu "):
            continue
        parts = [int(p) for p in line.split()[1:]]
        if len(parts) < 4:
            return None
        idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
        total = sum(parts)
        return total, idle
    return None


def _cpu_percent(interval: float = 0.1) -> float:
    first = _read_cpu_times()
    if first is None:
        load1, _load5, _load15 = os.getloadavg()
        cores = os.cpu_count() or 1
        return round(min(100.0, 100.0 * load1 / cores), 1)
    time.sleep(max(0.05, interval))
    second = _read_cpu_times()
    if second is None:
        return 0.0
    total_delta = second[0] - first[0]
    idle_delta = second[1] - first[1]
    if total_delta <= 0:
        return 0.0
    busy = total_delta - idle_delta
    return round(max(0.0, min(100.0, 100.0 * busy / total_delta)), 1)


def sample_host_resources(settings: Settings, *, cpu_interval: float = 0.1) -> HostResources:
    memory_percent = _memory_percent()
    cpu_percent = _cpu_percent(cpu_interval)
    ram_max = float(settings.neuroflow_ram_max_percent)
    cpu_max = float(settings.neuroflow_cpu_max_percent)

    reasons: list[str] = []
    if memory_percent >= ram_max:
        reasons.append(f"RAM at {memory_percent:.0f}% (limit {ram_max:.0f}%)")
    if cpu_percent >= cpu_max:
        reasons.append(f"CPU at {cpu_percent:.0f}% (limit {cpu_max:.0f}%)")

    can_start = not reasons
    block_reason = "; ".join(reasons) if reasons else None
    return HostResources(
        memory_percent=memory_percent,
        cpu_percent=cpu_percent,
        ram_max_percent=ram_max,
        cpu_max_percent=cpu_max,
        can_start_job=can_start,
        block_reason=block_reason,
    )


def can_start_job(settings: Settings) -> tuple[bool, str | None]:
    sample = sample_host_resources(settings)
    return sample.can_start_job, sample.block_reason
