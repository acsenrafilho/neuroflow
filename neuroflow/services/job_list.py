"""Aggregate job listing across tools."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from neuroflow.services.jobs import JobStore
from neuroflow.tools.registry import get_module, get_tool, list_tools

JobListStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _subject_from_meta(meta: dict[str, Any]) -> str | None:
    if meta.get("subject_id"):
        return str(meta["subject_id"])
    params = meta.get("parameters") or {}
    if params.get("subject_id"):
        return str(params["subject_id"])
    batch_ids = params.get("batch_subject_ids")
    if isinstance(batch_ids, list) and batch_ids:
        return str(batch_ids[0])
    items = meta.get("batch_items") or []
    if items and isinstance(items[0], dict) and items[0].get("subject_id"):
        return str(items[0]["subject_id"])
    return None


def _module_from_meta(meta: dict[str, Any]) -> str | None:
    params = meta.get("parameters") or {}
    if params.get("module_id"):
        return str(params["module_id"])
    return meta.get("module_id")


def _page_path(tool_id: str, module_id: str | None) -> str:
    if module_id:
        module = get_module(module_id)
        if module:
            return f"{module.page_path}?module={module.id}"
    tool = get_tool(tool_id)
    return tool.page_path if tool else f"/tools/{tool_id}.html"


def list_jobs(
    store: JobStore,
    *,
    statuses: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Scan job store for jobs matching optional status filter."""
    wanted = statuses
    results: list[dict[str, Any]] = []

    for tool in list_tools(portal_only=False):
        tool_path = store.tool_dir(tool.id)
        if not tool_path.is_dir():
            continue
        for job_path in tool_path.iterdir():
            if not job_path.is_dir():
                continue
            meta_path = job_path / "meta.json"
            if not meta_path.is_file():
                continue
            try:
                meta = store.read_meta(tool.id, job_path.name)
            except (OSError, ValueError):
                continue
            status = meta.get("status") or "queued"
            if wanted is not None and status not in wanted:
                continue
            module_id = _module_from_meta(meta)
            page = _page_path(tool.id, module_id)
            job_id = meta.get("job_id") or job_path.name
            if module_id:
                page = f"{page}&job_id={job_id}" if "?" in page else f"{page}?job_id={job_id}"
            else:
                page = f"{page}?job_id={job_id}"

            results.append(
                {
                    "job_id": job_id,
                    "tool_id": tool.id,
                    "module_id": module_id,
                    "workspace": meta.get("workspace")
                    or (meta.get("parameters") or {}).get("workspace"),
                    "subject_id": _subject_from_meta(meta),
                    "status": status,
                    "created_at": _parse_dt(meta.get("created_at")),
                    "started_at": _parse_dt(meta.get("started_at")),
                    "finished_at": _parse_dt(meta.get("finished_at")),
                    "page_path": page,
                    "queue_reason": meta.get("queue_reason"),
                }
            )

    results.sort(
        key=lambda row: row["created_at"].timestamp() if row["created_at"] else 0.0,
        reverse=True,
    )
    return results


def count_jobs_with_status(store: JobStore, statuses: set[str]) -> int:
    return len(list_jobs(store, statuses=statuses))
