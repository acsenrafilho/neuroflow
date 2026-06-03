"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """NeuroFlow runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    neuroflow_env: str = "development"
    neuroflow_data_root: Path = Path("./data/jobs")
    neuroflow_log_level: str = "INFO"
    neuroflow_serve_frontend: bool = False
    neuroflow_max_upload_mb: int = 500
    neuroflow_freesurfer_home: Path | None = None
    neuroflow_recon_all_bin: str = "recon-all"
    neuroflow_fsldir: Path | None = None
    neuroflow_slicer_home: Path | None = None

    @property
    def data_root(self) -> Path:
        return self.neuroflow_data_root.resolve()

    @property
    def max_upload_bytes(self) -> int:
        return self.neuroflow_max_upload_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()
