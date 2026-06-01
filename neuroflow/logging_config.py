"""Application logging setup for console output alongside uvicorn."""

from __future__ import annotations

import logging


def configure_app_logging(level_name: str = "INFO") -> None:
    """Attach a stderr handler to the neuroflow logger tree if not already set."""
    level = getattr(logging, level_name.upper(), logging.INFO)
    neuroflow_logger = logging.getLogger("neuroflow")
    neuroflow_logger.setLevel(level)

    if not any(isinstance(handler, logging.StreamHandler) for handler in neuroflow_logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s:     %(message)s"))
        neuroflow_logger.addHandler(handler)
