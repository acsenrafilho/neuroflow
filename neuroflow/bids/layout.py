"""Read-only BIDS layout utilities via pybids."""

import json
from pathlib import Path

from bids import BIDSLayout


def get_layout(root: Path, *, validate: bool = False) -> BIDSLayout:
    return BIDSLayout(str(root), validate=validate)


def list_subjects(root: Path) -> list[str]:
    if not (root / "dataset_description.json").is_file():
        return []
    layout = get_layout(root)
    return sorted(layout.get_subjects())


def read_dataset_description(root: Path) -> str | None:
    desc_path = root / "dataset_description.json"
    if not desc_path.is_file():
        return None
    with desc_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("Name") or data.get("name")
