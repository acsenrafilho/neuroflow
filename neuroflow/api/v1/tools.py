"""Tool listing and per-tool job endpoints."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError

from neuroflow.api.deps import get_cached_settings, get_job_store
from neuroflow.api.host_state import get_tool_availability
from neuroflow.config import Settings
from neuroflow.models.schemas import JobLogResponse, JobStatusResponse, ModuleInfo, ToolInfo
from neuroflow.services.job_monitoring import enrich_log, enrich_status
from neuroflow.services.jobs import JobStore
from neuroflow.tools.freesurfer import BatchScan, FreeSurferJobParams, launch_freesurfer_job
from neuroflow.tools.host_probe import module_available
from neuroflow.tools.registry import get_module, get_tool, list_modules, list_tools

router = APIRouter(prefix="/tools", tags=["tools"])


def _parse_meta_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _meta_to_status(meta: dict) -> JobStatusResponse:
    return JobStatusResponse(
        job_id=meta["job_id"],
        tool_id=meta["tool_id"],
        status=meta["status"],
        command=meta.get("command") or [],
        command_preview=meta.get("command_preview") or "",
        created_at=_parse_meta_datetime(meta["created_at"]) or datetime.now(),
        started_at=_parse_meta_datetime(meta.get("started_at")),
        finished_at=_parse_meta_datetime(meta.get("finished_at")),
        exit_code=meta.get("exit_code"),
        parameters=meta.get("parameters") or {},
        input_files=meta.get("input_files") or [],
        error_message=meta.get("error_message"),
    )


@router.get("", response_model=list[ToolInfo])
async def list_registered_tools(request: Request) -> list[ToolInfo]:
    availability = get_tool_availability(request)
    return [
        ToolInfo(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            page_path=tool.page_path,
            available=availability[tool.id].available if tool.id in availability else False,
        )
        for tool in list_tools()
    ]


@router.get("/modules", response_model=list[ModuleInfo])
async def list_processing_modules(request: Request) -> list[ModuleInfo]:
    availability = get_tool_availability(request)
    result: list[ModuleInfo] = []
    for module in list_modules():
        available = module_available(
            availability,
            module.package_id,
            required_executable=module.required_executable,
        )
        result.append(
            ModuleInfo(
                id=module.id,
                package_id=module.package_id,
                package_name=module.package_name,
                module_name=module.module_name,
                description=module.description,
                page_path=module.page_path,
                recon_options=module.recon_options,
                estimated_hours_per_scan=module.estimated_hours_per_scan,
                coming_soon=module.coming_soon,
                available=available,
            )
        )
    return result


def _parse_subject_ids(raw: str, expected: int) -> list[str]:
    try:
        subject_ids = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="subject_ids must be a JSON array of strings",
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    if not isinstance(subject_ids, list):
        raise HTTPException(
            status_code=422,
            detail="subject_ids must be a JSON array",
            headers={"X-Error-Code": "validation_error"},
        )
    if len(subject_ids) != expected:
        raise HTTPException(
            status_code=422,
            detail=f"Expected {expected} subject ID(s), got {len(subject_ids)}",
            headers={"X-Error-Code": "validation_error"},
        )
    validated: list[str] = []
    for sid in subject_ids:
        try:
            params = FreeSurferJobParams(subject_id=str(sid), recon_options="all")
            validated.append(params.subject_id)
        except (ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
                headers={"X-Error-Code": "validation_error"},
            ) from exc
    return validated


@router.post("/freesurfer/jobs", response_model=JobStatusResponse, status_code=201)
async def create_freesurfer_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    subject_ids: Annotated[str, Form()],
    recon_options: Annotated[str, Form()] = "all",
    module_id: Annotated[str | None, Form()] = None,
) -> JobStatusResponse:
    tool = get_tool("freesurfer")
    if tool is None:
        raise HTTPException(
            status_code=404,
            detail="Tool not found",
            headers={"X-Error-Code": "tool_not_found"},
        )

    if not files:
        raise HTTPException(
            status_code=422,
            detail="At least one file is required",
            headers={"X-Error-Code": "validation_error"},
        )

    if module_id:
        module = get_module(module_id)
        if module is None or module.recon_options is None:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown module: {module_id}",
                headers={"X-Error-Code": "validation_error"},
            )
        recon_options = module.recon_options

    try:
        FreeSurferJobParams(subject_id="sub-validate", recon_options=recon_options)  # type: ignore[arg-type]
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    parsed_subject_ids = _parse_subject_ids(subject_ids, len(files))

    module_def = next(
        (m for m in list_modules() if m.recon_options == recon_options and not m.coming_soon),
        None,
    )
    estimated_hours = module_def.estimated_hours_per_scan if module_def else 8.0

    job_id = store.create_job(
        "freesurfer",
        {"recon_options": recon_options, "subject_ids": parsed_subject_ids},
    )

    scans: list[BatchScan] = []
    try:
        for upload, subject_id in zip(files, parsed_subject_ids, strict=True):
            input_path = await store.save_upload("freesurfer", job_id, upload)
            scans.append(BatchScan(subject_id=subject_id, input_path=input_path))
    except ValueError as exc:
        store.delete_job("freesurfer", job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    try:
        launch_freesurfer_job(
            settings=settings,
            store=store,
            job_id=job_id,
            recon_options=recon_options,  # type: ignore[arg-type]
            scans=scans,
            estimated_hours_per_scan=estimated_hours,
        )
    except FileNotFoundError as exc:
        store.update_meta(
            "freesurfer",
            job_id,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "tool_not_installed"},
        ) from exc

    meta = store.read_meta("freesurfer", job_id)
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/freesurfer/jobs/{job_id}", response_model=JobStatusResponse)
async def get_freesurfer_job(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    try:
        meta = store.read_meta("freesurfer", job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/freesurfer/jobs/{job_id}/log", response_model=JobLogResponse)
async def get_freesurfer_job_log(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobLogResponse:
    try:
        meta = store.read_meta("freesurfer", job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    base = JobLogResponse(
        job_id=job_id,
        log=store.read_log("freesurfer", job_id),
        status=meta["status"],
    )
    return enrich_log(meta, base)
