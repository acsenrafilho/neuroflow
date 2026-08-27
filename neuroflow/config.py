"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from neuroflow.runtime_paths import (
    default_data_root,
    default_datasets_root,
    is_frozen,
)


class Settings(BaseSettings):
    """NeuroFlow runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neuroflow_env: str = "development"
    neuroflow_data_root: Path = Field(default_factory=default_data_root)
    neuroflow_datasets_root: Path = Field(default_factory=default_datasets_root)
    neuroflow_log_level: str = "INFO"
    neuroflow_serve_frontend: bool = Field(default_factory=is_frozen)
    neuroflow_max_upload_mb: int = 500
    neuroflow_ram_max_percent: float = 80.0
    neuroflow_cpu_max_percent: float = 90.0
    neuroflow_max_queued_jobs: int = 20
    neuroflow_freesurfer_home: Path | None = None
    neuroflow_recon_all_bin: str = "recon-all"
    neuroflow_fsldir: Path | None = None
    neuroflow_slicer_home: Path | None = None
    neuroflow_itk_binaries_config: Path | None = None
    neuroflow_antspath: Path | None = None
    neuroflow_sct_dir: Path | None = None

    @property
    def data_root(self) -> Path:
        return self.neuroflow_data_root.resolve()

    @property
    def datasets_root(self) -> Path:
        return self.neuroflow_datasets_root.resolve()

    @property
    def max_upload_bytes(self) -> int:
        return self.neuroflow_max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()
