"""Shared API response models."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str


class DatasetSummary(BaseModel):
    name: str
    path: str
    subjects: list[str] = Field(default_factory=list)
    description: str | None = None


class ErrorDetail(BaseModel):
    detail: str
    code: str
    field: str | None = None
