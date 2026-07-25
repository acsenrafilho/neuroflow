"""Workspace create / list / open-folder endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from neuroflow.api.deps import get_dataset_store
from neuroflow.models.schemas import WorkspaceCreate, WorkspaceInfo, WorkspaceOpenResponse
from neuroflow.services.datasets import DatasetStore, WorkspaceSummary
from neuroflow.services.reveal_path import open_in_file_manager

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


def _to_info(summary: WorkspaceSummary) -> WorkspaceInfo:
    return WorkspaceInfo(
        name=summary.name,
        path=str(summary.path),
        subject_count=summary.subject_count,
    )


@router.get("", response_model=list[WorkspaceInfo])
async def list_workspaces(
    store: Annotated[DatasetStore, Depends(get_dataset_store)],
) -> list[WorkspaceInfo]:
    return [_to_info(item) for item in store.list_workspaces()]


@router.post("", response_model=WorkspaceInfo, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    body: WorkspaceCreate,
    store: Annotated[DatasetStore, Depends(get_dataset_store)],
) -> WorkspaceInfo:
    try:
        summary = store.create_workspace(body.name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    return _to_info(summary)


@router.post("/{name}/open", response_model=WorkspaceOpenResponse)
async def open_workspace(
    name: str,
    store: Annotated[DatasetStore, Depends(get_dataset_store)],
) -> WorkspaceOpenResponse:
    try:
        path = store.resolve_workspace_dir(name)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
            headers={"X-Error-Code": "validation_error"},
        ) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
            headers={"X-Error-Code": "workspace_not_found"},
        ) from exc

    try:
        open_in_file_manager(path)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
            headers={"X-Error-Code": "workspace_not_found"},
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
            headers={"X-Error-Code": "open_folder_failed"},
        ) from exc

    return WorkspaceOpenResponse(ok=True)
