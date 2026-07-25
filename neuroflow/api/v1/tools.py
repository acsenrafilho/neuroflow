"""Tool listing and per-tool job endpoints."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError

from neuroflow.api.deps import get_cached_settings, get_job_store
from neuroflow.api.host_state import get_tool_availability
from neuroflow.config import Settings
from neuroflow.models.schemas import JobLogResponse, JobStatusResponse, ModuleInfo, ToolInfo
from neuroflow.services.datasets import normalize_subject_id, sanitize_workspace
from neuroflow.services.job_kill import JobKillError, request_job_kill
from neuroflow.services.job_monitoring import enrich_log, enrich_status
from neuroflow.services.job_scheduler import try_start_job
from neuroflow.services.jobs import JobStore
from neuroflow.tools.ants import (
    ANTS_TOOL_ID,
    AntsJobParams,
    launch_ants_job,
)
from neuroflow.tools.ants import (
    group_uploads_into_batch as group_ants_uploads_into_batch,
)
from neuroflow.tools.freesurfer import BatchScan, FreeSurferJobParams, launch_freesurfer_job
from neuroflow.tools.fsl import FSL_TOOL_ID, FslJobParams, group_uploads_into_batch, launch_fsl_job
from neuroflow.tools.host_probe import module_available
from neuroflow.tools.itk import (
    ITK_TOOL_ID,
    ItkJobParams,
    launch_itk_job,
)
from neuroflow.tools.itk import (
    group_uploads_into_batch as group_itk_uploads_into_batch,
)
from neuroflow.tools.registry import get_module, get_tool, list_modules, list_tools
from neuroflow.tools.sct import SCT_TOOL_ID, SctJobParams, launch_sct_job
from neuroflow.tools.sct import (
    group_uploads_into_batch as group_sct_uploads_into_batch,
)
from neuroflow.tools.slicer import (
    SLICER_TOOL_ID,
    SlicerJobParams,
    launch_slicer_job,
)
from neuroflow.tools.slicer import (
    group_uploads_into_batch as group_slicer_uploads_into_batch,
)

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
            visible_in_portal=tool.visible_in_portal,
        )
        for tool in list_tools(portal_only=True)
    ]


@router.get("/modules", response_model=list[ModuleInfo])
async def list_processing_modules(request: Request) -> list[ModuleInfo]:
    availability = get_tool_availability(request)
    result: list[ModuleInfo] = []
    settings = get_cached_settings()
    visible_packages = {t.id for t in list_tools(portal_only=True)}
    for module in list_modules(portal_only=True):
        available = module_available(availability, module, settings)
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
                visible_in_portal=module.package_id in visible_packages,
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
            validated.append(normalize_subject_id(str(sid)))
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=str(exc),
                headers={"X-Error-Code": "validation_error"},
            ) from exc
    return validated


def _parse_workspace(raw: str) -> str:
    try:
        return sanitize_workspace(raw)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc


def _resource_or_queue_error(exc: RuntimeError) -> HTTPException:
    detail = str(exc)
    code = "queue_full" if "queue is full" in detail.lower() else "resource_exhausted"
    return HTTPException(
        status_code=503,
        detail=detail,
        headers={"X-Error-Code": code},
    )


@router.post("/freesurfer/jobs", response_model=JobStatusResponse, status_code=201)
async def create_freesurfer_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    subject_ids: Annotated[str, Form()],
    workspace: Annotated[str, Form()],
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

    safe_workspace = _parse_workspace(workspace)

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
    resolved_module_id = (
        module_def.id
        if module_def
        else ("freesurfer-recon-all" if recon_options == "all" else f"freesurfer-{recon_options}")
    )

    job_id = store.create_job(
        "freesurfer",
        {
            "recon_options": recon_options,
            "subject_ids": parsed_subject_ids,
            "workspace": safe_workspace,
            "module_id": resolved_module_id,
        },
    )
    store.update_meta(
        "freesurfer",
        job_id,
        workspace=safe_workspace,
        subject_id=parsed_subject_ids[0],
        parameters={
            "recon_options": recon_options,
            "workspace": safe_workspace,
            "module_id": resolved_module_id,
            "batch_subject_ids": parsed_subject_ids,
        },
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

    def _start() -> None:
        launch_freesurfer_job(
            settings=settings,
            store=store,
            job_id=job_id,
            recon_options=recon_options,  # type: ignore[arg-type]
            scans=scans,
            estimated_hours_per_scan=estimated_hours,
            workspace=safe_workspace,
        )

    try:
        # Validate tool presence before queueing.
        from neuroflow.tools.freesurfer import ensure_recon_all_available

        ensure_recon_all_available(settings)
        try_start_job(
            settings=settings,
            store=store,
            tool_id="freesurfer",
            job_id=job_id,
            starter=_start,
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
    except RuntimeError as exc:
        store.delete_job("freesurfer", job_id)
        raise _resource_or_queue_error(exc) from exc

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


def _parse_file_roles(raw: str, expected: int) -> list[str]:
    try:
        roles = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="file_roles must be a JSON array of strings",
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    if not isinstance(roles, list):
        raise HTTPException(
            status_code=422,
            detail="file_roles must be a JSON array",
            headers={"X-Error-Code": "validation_error"},
        )
    if len(roles) != expected:
        raise HTTPException(
            status_code=422,
            detail=f"Expected {expected} file role(s), got {len(roles)}",
            headers={"X-Error-Code": "validation_error"},
        )
    return [str(role) for role in roles]


def _parse_parameters(raw: str) -> dict:
    if not raw or raw.strip() == "":
        return {}
    try:
        params = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="parameters must be a JSON object",
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    if not isinstance(params, dict):
        raise HTTPException(
            status_code=422,
            detail="parameters must be a JSON object",
            headers={"X-Error-Code": "validation_error"},
        )
    return params


@router.post("/fsl/jobs", response_model=JobStatusResponse, status_code=201)
async def create_fsl_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    file_roles: Annotated[str, Form()],
    module_id: Annotated[str, Form()],
    workspace: Annotated[str, Form()],
    subject_id: Annotated[str, Form()],
    output_prefix: Annotated[str, Form()] = "result",
    parameters: Annotated[str, Form()] = "{}",
) -> JobStatusResponse:
    tool = get_tool(FSL_TOOL_ID)
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

    safe_workspace = _parse_workspace(workspace)
    try:
        safe_subject = normalize_subject_id(subject_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    module = get_module(module_id)
    if module is None or module.coming_soon:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown or unavailable module: {module_id}",
            headers={"X-Error-Code": "validation_error"},
        )

    parsed_roles = _parse_file_roles(file_roles, len(files))
    parsed_parameters = _parse_parameters(parameters)

    try:
        job_params = FslJobParams(
            module_id=module_id,
            output_prefix=output_prefix,
            parameters=parsed_parameters,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    job_id = store.create_job(
        FSL_TOOL_ID,
        {
            "module_id": job_params.module_id,
            "output_prefix": job_params.output_prefix,
            "parameters": job_params.parameters,
            "workspace": safe_workspace,
            "subject_id": safe_subject,
        },
    )
    store.update_meta(
        FSL_TOOL_ID,
        job_id,
        workspace=safe_workspace,
        subject_id=safe_subject,
    )

    files_by_role: dict[str, list[Path]] = defaultdict(list)
    try:
        for upload, role in zip(files, parsed_roles, strict=True):
            input_path = await store.save_upload(FSL_TOOL_ID, job_id, upload)
            files_by_role[role].append(input_path)
        batch_items = group_uploads_into_batch(
            job_params.module_id, dict(files_by_role)
        )
    except ValueError as exc:
        store.delete_job(FSL_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    def _start() -> None:
        launch_fsl_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id=job_params.module_id,
            batch_items=batch_items,
            output_prefix=job_params.output_prefix,
            parameters=job_params.parameters,
            workspace=safe_workspace,
            subject_id=safe_subject,
        )

    try:
        from neuroflow.tools.fsl import ensure_module_available

        ensure_module_available(settings, job_params.module_id, job_params.parameters)
        try_start_job(
            settings=settings,
            store=store,
            tool_id=FSL_TOOL_ID,
            job_id=job_id,
            starter=_start,
        )
    except FileNotFoundError as exc:
        store.update_meta(
            FSL_TOOL_ID,
            job_id,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "tool_not_installed"},
        ) from exc
    except ValueError as exc:
        store.delete_job(FSL_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    except RuntimeError as exc:
        store.delete_job(FSL_TOOL_ID, job_id)
        raise _resource_or_queue_error(exc) from exc

    meta = store.read_meta(FSL_TOOL_ID, job_id)
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/fsl/jobs/{job_id}", response_model=JobStatusResponse)
async def get_fsl_job(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    try:
        meta = store.read_meta(FSL_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/fsl/jobs/{job_id}/log", response_model=JobLogResponse)
async def get_fsl_job_log(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobLogResponse:
    try:
        meta = store.read_meta(FSL_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    base = JobLogResponse(
        job_id=job_id,
        log=store.read_log(FSL_TOOL_ID, job_id),
        status=meta["status"],
    )
    return enrich_log(meta, base)


@router.post("/sct/jobs", response_model=JobStatusResponse, status_code=201)
async def create_sct_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    file_roles: Annotated[str, Form()],
    module_id: Annotated[str, Form()],
    workspace: Annotated[str, Form()],
    subject_id: Annotated[str, Form()],
    output_prefix: Annotated[str, Form()] = "result",
    parameters: Annotated[str, Form()] = "{}",
) -> JobStatusResponse:
    tool = get_tool(SCT_TOOL_ID)
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

    safe_workspace = _parse_workspace(workspace)
    try:
        safe_subject = normalize_subject_id(subject_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    module = get_module(module_id)
    if module is None or module.coming_soon:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown or unavailable module: {module_id}",
            headers={"X-Error-Code": "validation_error"},
        )

    parsed_roles = _parse_file_roles(file_roles, len(files))
    parsed_parameters = _parse_parameters(parameters)

    try:
        job_params = SctJobParams(
            module_id=module_id,
            output_prefix=output_prefix,
            parameters=parsed_parameters,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    job_id = store.create_job(
        SCT_TOOL_ID,
        {
            "module_id": job_params.module_id,
            "output_prefix": job_params.output_prefix,
            "parameters": job_params.parameters,
            "workspace": safe_workspace,
            "subject_id": safe_subject,
        },
    )
    store.update_meta(
        SCT_TOOL_ID,
        job_id,
        workspace=safe_workspace,
        subject_id=safe_subject,
    )

    files_by_role: dict[str, list[Path]] = defaultdict(list)
    try:
        for upload, role in zip(files, parsed_roles, strict=True):
            input_path = await store.save_upload(SCT_TOOL_ID, job_id, upload)
            files_by_role[role].append(input_path)
        batch_items = group_sct_uploads_into_batch(
            job_params.module_id, dict(files_by_role)
        )
    except ValueError as exc:
        store.delete_job(SCT_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    def _start() -> None:
        launch_sct_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id=job_params.module_id,
            batch_items=batch_items,
            output_prefix=job_params.output_prefix,
            parameters=job_params.parameters,
            workspace=safe_workspace,
            subject_id=safe_subject,
        )

    try:
        from neuroflow.tools.sct import ensure_module_available

        ensure_module_available(settings, job_params.module_id, job_params.parameters)
        try_start_job(
            settings=settings,
            store=store,
            tool_id=SCT_TOOL_ID,
            job_id=job_id,
            starter=_start,
        )
    except FileNotFoundError as exc:
        store.update_meta(
            SCT_TOOL_ID,
            job_id,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "tool_not_installed"},
        ) from exc
    except ValueError as exc:
        store.delete_job(SCT_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    except RuntimeError as exc:
        store.delete_job(SCT_TOOL_ID, job_id)
        raise _resource_or_queue_error(exc) from exc

    meta = store.read_meta(SCT_TOOL_ID, job_id)
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/sct/jobs/{job_id}", response_model=JobStatusResponse)
async def get_sct_job(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    try:
        meta = store.read_meta(SCT_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/sct/jobs/{job_id}/log", response_model=JobLogResponse)
async def get_sct_job_log(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobLogResponse:
    try:
        meta = store.read_meta(SCT_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    base = JobLogResponse(
        job_id=job_id,
        log=store.read_log(SCT_TOOL_ID, job_id),
        status=meta["status"],
    )
    return enrich_log(meta, base)


@router.post("/ants/jobs", response_model=JobStatusResponse, status_code=201)
async def create_ants_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    file_roles: Annotated[str, Form()],
    module_id: Annotated[str, Form()],
    output_prefix: Annotated[str, Form()] = "result",
    parameters: Annotated[str, Form()] = "{}",
) -> JobStatusResponse:
    tool = get_tool(ANTS_TOOL_ID)
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

    module = get_module(module_id)
    if module is None or module.coming_soon:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown or unavailable module: {module_id}",
            headers={"X-Error-Code": "validation_error"},
        )

    parsed_roles = _parse_file_roles(file_roles, len(files))
    parsed_parameters = _parse_parameters(parameters)

    try:
        job_params = AntsJobParams(
            module_id=module_id,
            output_prefix=output_prefix,
            parameters=parsed_parameters,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    job_id = store.create_job(
        ANTS_TOOL_ID,
        {
            "module_id": job_params.module_id,
            "output_prefix": job_params.output_prefix,
            "parameters": job_params.parameters,
        },
    )

    files_by_role: dict[str, list[Path]] = defaultdict(list)
    try:
        for upload, role in zip(files, parsed_roles, strict=True):
            input_path = await store.save_upload(ANTS_TOOL_ID, job_id, upload)
            files_by_role[role].append(input_path)
        batch_items = group_ants_uploads_into_batch(
            job_params.module_id, dict(files_by_role)
        )
    except ValueError as exc:
        store.delete_job(ANTS_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    try:
        launch_ants_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id=job_params.module_id,
            batch_items=batch_items,
            output_prefix=job_params.output_prefix,
            parameters=job_params.parameters,
        )
    except FileNotFoundError as exc:
        store.update_meta(
            ANTS_TOOL_ID,
            job_id,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "tool_not_installed"},
        ) from exc
    except ValueError as exc:
        store.delete_job(ANTS_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    meta = store.read_meta(ANTS_TOOL_ID, job_id)
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/ants/jobs/{job_id}", response_model=JobStatusResponse)
async def get_ants_job(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    try:
        meta = store.read_meta(ANTS_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/ants/jobs/{job_id}/log", response_model=JobLogResponse)
async def get_ants_job_log(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobLogResponse:
    try:
        meta = store.read_meta(ANTS_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    base = JobLogResponse(
        job_id=job_id,
        log=store.read_log(ANTS_TOOL_ID, job_id),
        status=meta["status"],
    )
    return enrich_log(meta, base)


@router.post("/slicer/jobs", response_model=JobStatusResponse, status_code=201)
async def create_slicer_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    file_roles: Annotated[str, Form()],
    module_id: Annotated[str, Form()],
    output_prefix: Annotated[str, Form()] = "result",
    parameters: Annotated[str, Form()] = "{}",
) -> JobStatusResponse:
    tool = get_tool(SLICER_TOOL_ID)
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

    module = get_module(module_id)
    if module is None or module.coming_soon:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown or unavailable module: {module_id}",
            headers={"X-Error-Code": "validation_error"},
        )

    parsed_roles = _parse_file_roles(file_roles, len(files))
    parsed_parameters = _parse_parameters(parameters)

    try:
        job_params = SlicerJobParams(
            module_id=module_id,
            output_prefix=output_prefix,
            parameters=parsed_parameters,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    job_id = store.create_job(
        SLICER_TOOL_ID,
        {
            "module_id": job_params.module_id,
            "output_prefix": job_params.output_prefix,
            "parameters": job_params.parameters,
        },
    )

    files_by_role: dict[str, list[Path]] = defaultdict(list)
    try:
        for upload, role in zip(files, parsed_roles, strict=True):
            input_path = await store.save_upload(SLICER_TOOL_ID, job_id, upload)
            files_by_role[role].append(input_path)
        batch_items = group_slicer_uploads_into_batch(
            job_params.module_id, dict(files_by_role)
        )
    except ValueError as exc:
        store.delete_job(SLICER_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    try:
        launch_slicer_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id=job_params.module_id,
            batch_items=batch_items,
            output_prefix=job_params.output_prefix,
            parameters=job_params.parameters,
        )
    except FileNotFoundError as exc:
        store.update_meta(
            SLICER_TOOL_ID,
            job_id,
            status="failed",
            error_message=str(exc),
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        raise HTTPException(
            status_code=503,
            detail=str(exc),
            headers={"X-Error-Code": "tool_unavailable"},
        ) from exc
    except ValueError as exc:
        store.delete_job(SLICER_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    meta = store.read_meta(SLICER_TOOL_ID, job_id)
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/slicer/jobs/{job_id}", response_model=JobStatusResponse)
async def get_slicer_job(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    try:
        meta = store.read_meta(SLICER_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/slicer/jobs/{job_id}/log", response_model=JobLogResponse)
async def get_slicer_job_log(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobLogResponse:
    try:
        meta = store.read_meta(SLICER_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    base = JobLogResponse(
        job_id=job_id,
        log=store.read_log(SLICER_TOOL_ID, job_id),
        status=meta["status"],
    )
    return enrich_log(meta, base)


@router.post("/itk/jobs", response_model=JobStatusResponse, status_code=201)
async def create_itk_job(
    settings: Annotated[Settings, Depends(get_cached_settings)],
    store: Annotated[JobStore, Depends(get_job_store)],
    files: Annotated[list[UploadFile], File()],
    file_roles: Annotated[str, Form()],
    module_id: Annotated[str, Form()],
    output_prefix: Annotated[str, Form()] = "result",
    parameters: Annotated[str, Form()] = "{}",
) -> JobStatusResponse:
    tool = get_tool(ITK_TOOL_ID)
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

    module = get_module(module_id)
    if module is None or module.coming_soon:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown or unavailable module: {module_id}",
            headers={"X-Error-Code": "validation_error"},
        )

    parsed_roles = _parse_file_roles(file_roles, len(files))
    parsed_parameters = _parse_parameters(parameters)

    try:
        job_params = ItkJobParams(
            module_id=module_id,
            output_prefix=output_prefix,
            parameters=parsed_parameters,
        )
    except (ValueError, ValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    job_id = store.create_job(
        ITK_TOOL_ID,
        {
            "module_id": job_params.module_id,
            "output_prefix": job_params.output_prefix,
            "parameters": job_params.parameters,
        },
    )

    files_by_role: dict[str, list[Path]] = defaultdict(list)
    try:
        for upload, role in zip(files, parsed_roles, strict=True):
            input_path = await store.save_upload(ITK_TOOL_ID, job_id, upload)
            files_by_role[role].append(input_path)
        batch_items = group_itk_uploads_into_batch(
            job_params.module_id, dict(files_by_role)
        )
    except ValueError as exc:
        store.delete_job(ITK_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    try:
        launch_itk_job(
            settings=settings,
            store=store,
            job_id=job_id,
            module_id=job_params.module_id,
            batch_items=batch_items,
            output_prefix=job_params.output_prefix,
            parameters=job_params.parameters,
        )
    except FileNotFoundError as exc:
        store.update_meta(
            ITK_TOOL_ID,
            job_id,
            status="failed",
            error_message=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "tool_not_installed"},
        ) from exc
    except ValueError as exc:
        store.delete_job(ITK_TOOL_ID, job_id)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc

    meta = store.read_meta(ITK_TOOL_ID, job_id)
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/itk/jobs/{job_id}", response_model=JobStatusResponse)
async def get_itk_job(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    try:
        meta = store.read_meta(ITK_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))


@router.get("/itk/jobs/{job_id}/log", response_model=JobLogResponse)
async def get_itk_job_log(
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobLogResponse:
    try:
        meta = store.read_meta(ITK_TOOL_ID, job_id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Job not found: {job_id}",
            headers={"X-Error-Code": "job_not_found"},
        ) from exc
    base = JobLogResponse(
        job_id=job_id,
        log=store.read_log(ITK_TOOL_ID, job_id),
        status=meta["status"],
    )
    return enrich_log(meta, base)


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


@router.post("/{tool_id}/jobs/{job_id}/kill", response_model=JobStatusResponse)
async def kill_tool_job(
    tool_id: str,
    job_id: str,
    store: Annotated[JobStore, Depends(get_job_store)],
) -> JobStatusResponse:
    if get_tool(tool_id) is None:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown tool: {tool_id}",
            headers={"X-Error-Code": "validation_error"},
        )
    try:
        meta = request_job_kill(store, tool_id, job_id)
    except JobKillError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
            headers={"X-Error-Code": exc.code},
        ) from exc
    return enrich_status(meta, _meta_to_status(meta))
