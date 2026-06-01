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
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


class JobStatusResponse(BaseModel):
    job_id: str
    tool_id: str
    status: Literal["queued", "running", "completed", "failed"]
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
    status: Literal["queued", "running", "completed", "failed"]
    elapsed_seconds: int | None = None
    pid: int | None = None
    batch_current_index: int = 0
    batch_total: int = 0
    estimated_total_seconds: int | None = None
    estimated_remaining_seconds: int | None = None
