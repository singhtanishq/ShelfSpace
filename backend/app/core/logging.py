"""Application-wide logging configuration."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import settings

_CONFIGURED = False

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(console)

    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)

    # Quiet down noisy third-party loggers.
    for name in ("uvicorn.access", "sqlalchemy.engine.Engine"):
        logging.getLogger(name).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
