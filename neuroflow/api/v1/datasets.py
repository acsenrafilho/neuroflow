"""Dataset listing endpoints (BIDS root)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from neuroflow.api.deps import get_cached_settings
from neuroflow.bids.layout import list_subjects, read_dataset_description
from neuroflow.config import Settings
from neuroflow.models.schemas import DatasetSummary

router = APIRouter(prefix="/datasets", tags=["datasets"])

SettingsDep = Annotated[Settings, Depends(get_cached_settings)]


@router.get("", response_model=list[DatasetSummary])
async def list_datasets(settings: SettingsDep) -> list[DatasetSummary]:
    root = settings.bids_root
    if not root.is_dir():
        raise HTTPException(
            status_code=404,
            detail=(
                "BIDS root directory not found. "
                "Configure NEUROFLOW_BIDS_ROOT or fetch sample data."
            ),
            headers={"X-Error-Code": "bids_root_missing"},
        )

    description = read_dataset_description(root)
    subjects = list_subjects(root)
    if not subjects and not (root / "dataset_description.json").is_file():
        raise HTTPException(
            status_code=404,
            detail="No valid BIDS dataset at the configured root.",
            headers={"X-Error-Code": "bids_dataset_invalid"},
        )

    return [
        DatasetSummary(
            name=root.name,
            path=str(root),
            subjects=subjects,
            description=description,
        )
    ]
