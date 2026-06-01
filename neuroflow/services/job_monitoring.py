"""Computed monitoring fields for job status responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from neuroflow.models.schemas import BatchItemStatus, JobLogResponse, JobStatusResponse


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def elapsed_seconds(meta: dict[str, Any]) -> int | None:
    started = _parse_dt(meta.get("started_at"))
    if started is None:
        return None
    finished = _parse_dt(meta.get("finished_at"))
    end = finished if finished is not None else datetime.now(timezone.utc)
    return max(0, int((end - started).total_seconds()))


def estimated_remaining_seconds(meta: dict[str, Any]) -> int | None:
    total = meta.get("estimated_total_seconds")
    if total is None:
        return None
    elapsed = elapsed_seconds(meta)
    if elapsed is None:
        return int(total)
    return max(0, int(total) - elapsed)


def batch_items_from_meta(meta: dict[str, Any]) -> list[BatchItemStatus]:
    raw = meta.get("batch_items") or []
    return [BatchItemStatus.model_validate(item) for item in raw]


def enrich_status(meta: dict[str, Any], base: JobStatusResponse) -> JobStatusResponse:
    return base.model_copy(
        update={
            "pid": meta.get("pid"),
            "batch_items": batch_items_from_meta(meta),
            "batch_current_index": int(meta.get("batch_current_index") or 0),
            "batch_total": int(meta.get("batch_total") or 0),
            "estimated_total_seconds": meta.get("estimated_total_seconds"),
            "estimated_remaining_seconds": estimated_remaining_seconds(meta),
            "elapsed_seconds": elapsed_seconds(meta),
        }
    )


def enrich_log(meta: dict[str, Any], base: JobLogResponse) -> JobLogResponse:
    return base.model_copy(
        update={
            "elapsed_seconds": elapsed_seconds(meta),
            "pid": meta.get("pid"),
            "batch_current_index": int(meta.get("batch_current_index") or 0),
            "batch_total": int(meta.get("batch_total") or 0),
            "estimated_total_seconds": meta.get("estimated_total_seconds"),
            "estimated_remaining_seconds": estimated_remaining_seconds(meta),
        }
    )
