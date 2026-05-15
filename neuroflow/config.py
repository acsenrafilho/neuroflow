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
    neuroflow_bids_root: Path = Path("./data/sample")
    neuroflow_log_level: str = "INFO"
    neuroflow_serve_frontend: bool = False

    @property
    def bids_root(self) -> Path:
        return self.neuroflow_bids_root.resolve()


def get_settings() -> Settings:
    return Settings()
