"""Shared API response models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class ErrorDetail(BaseModel):
    detail: str
    code: str
    field: str | None = None


class ToolInfo(BaseModel):
    id: str
    name: str
    description: str
    page_path: str
    available: bool = True
    visible_in_portal: bool = True


class ModuleInfo(BaseModel):
    id: str
    package_id: str
    package_name: str
    module_name: str
    description: str
    page_path: str
    recon_options: str | None = None
    estimated_hours_per_scan: float = 1.0
    coming_soon: bool = False
    available: bool = False
    visible_in_portal: bool = True


class PackageProbeInfo(BaseModel):
    package_id: str
    available: bool
    resolved_path: str | None = None
    detail: str = ""


class HostScanResponse(BaseModel):
    packages: list[PackageProbeInfo]


class BatchItemStatus(BaseModel):
    filename: str
    subject_id: str
    status: Literal["pending", "running", "completed", "failed", "cancelled"] = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    tool_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    command: list[str]
    command_preview: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    exit_code: int | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    input_files: list[str] = Field(default_factory=list)
    error_message: str | None = None
    pid: int | None = None
    batch_items: list[BatchItemStatus] = Field(default_factory=list)
    batch_current_index: int = 0
    batch_total: int = 0
    estimated_total_seconds: int | None = None
    estimated_remaining_seconds: int | None = None
    elapsed_seconds: int | None = None


class JobLogResponse(BaseModel):
    job_id: str
    log: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    elapsed_seconds: int | None = None
    pid: int | None = None
    batch_current_index: int = 0
    batch_total: int = 0
    estimated_total_seconds: int | None = None
    estimated_remaining_seconds: int | None = None


class JobSummary(BaseModel):
    job_id: str
    tool_id: str
    module_id: str | None = None
    workspace: str | None = None
    subject_id: str | None = None
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    page_path: str
    queue_reason: str | None = None


class HostResourcesResponse(BaseModel):
    memory_percent: float
    cpu_percent: float
    ram_max_percent: float
    cpu_max_percent: float
    can_start_job: bool
    can_accept_job: bool = True
    block_reason: str | None = None
    queued_jobs: int = 0
    max_queued_jobs: int = 20


class WorkspaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)


class WorkspaceInfo(BaseModel):
    name: str
    path: str
    subject_count: int = 0


class WorkspaceOpenResponse(BaseModel):
    ok: bool = True
