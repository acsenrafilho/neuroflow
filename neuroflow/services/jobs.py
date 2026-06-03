"""Job storage and metadata on disk."""

from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import UploadFile

from neuroflow.config import Settings

JobStatus = Literal["queued", "running", "completed", "failed", "cancelled"]

ALLOWED_UPLOAD_SUFFIXES = (
    ".nii",
    ".nii.gz",
    ".nrrd",
    ".bval",
    ".bvec",
    ".dcm",
    ".txt",
    ".mat",
    ".zip",
)


def _validate_upload_name(filename: str) -> None:
    name = filename.lower()
    if not any(name.endswith(suffix) for suffix in ALLOWED_UPLOAD_SUFFIXES):
        allowed = ", ".join(ALLOWED_UPLOAD_SUFFIXES)
        raise ValueError(f"Unsupported file type. Allowed: {allowed}")


class JobStore:
    """CRUD for per-tool job directories under the data root."""

    def __init__(self, settings: Settings) -> None:
        self._root = settings.data_root
        self._max_bytes = settings.max_upload_bytes

    def tool_dir(self, tool_id: str) -> Path:
        path = self._root / tool_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def job_dir(self, tool_id: str, job_id: str) -> Path:
        return self.tool_dir(tool_id) / job_id

    def create_job(self, tool_id: str, parameters: dict[str, Any]) -> str:
        job_id = uuid.uuid4().hex[:12]
        job_path = self.job_dir(tool_id, job_id)
        (job_path / "input").mkdir(parents=True)
        (job_path / "output").mkdir(parents=True)
        meta = {
            "job_id": job_id,
            "tool_id": tool_id,
            "status": "queued",
            "parameters": parameters,
            "command": [],
            "command_preview": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "started_at": None,
            "finished_at": None,
            "exit_code": None,
            "pid": None,
            "input_files": [],
            "error_message": None,
        }
        self.write_meta(tool_id, job_id, meta)
        return job_id

    def meta_path(self, tool_id: str, job_id: str) -> Path:
        return self.job_dir(tool_id, job_id) / "meta.json"

    def log_path(self, tool_id: str, job_id: str) -> Path:
        return self.job_dir(tool_id, job_id) / "run.log"

    def read_meta(self, tool_id: str, job_id: str) -> dict[str, Any]:
        path = self.meta_path(tool_id, job_id)
        if not path.is_file():
            raise FileNotFoundError(f"Job not found: {job_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def write_meta(self, tool_id: str, job_id: str, meta: dict[str, Any]) -> None:
        path = self.meta_path(tool_id, job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    def update_meta(self, tool_id: str, job_id: str, **fields: Any) -> dict[str, Any]:
        meta = self.read_meta(tool_id, job_id)
        meta.update(fields)
        self.write_meta(tool_id, job_id, meta)
        return meta

    async def save_upload(
        self, tool_id: str, job_id: str, upload: UploadFile
    ) -> Path:
        if not upload.filename:
            raise ValueError("Upload filename is required")
        _validate_upload_name(upload.filename)

        content = await upload.read()
        if len(content) > self._max_bytes:
            raise ValueError(
                f"File exceeds maximum size of {self._max_bytes // (1024 * 1024)} MB"
            )

        dest = self.job_dir(tool_id, job_id) / "input" / Path(upload.filename).name
        dest.write_bytes(content)
        return dest

    def read_log(self, tool_id: str, job_id: str) -> str:
        path = self.log_path(tool_id, job_id)
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    def append_log(self, tool_id: str, job_id: str, text: str) -> None:
        path = self.log_path(tool_id, job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(text)

    def delete_job(self, tool_id: str, job_id: str) -> None:
        job_path = self.job_dir(tool_id, job_id)
        if job_path.is_dir():
            shutil.rmtree(job_path)
