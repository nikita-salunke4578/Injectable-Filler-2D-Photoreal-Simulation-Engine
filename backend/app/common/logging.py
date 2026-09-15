"""
Shared logging configuration.

Provides a ``get_logger`` factory that returns pre-configured loggers
with a consistent format across the entire backend.

**Privacy:** Never log raw image bytes, base-64 encoded images, or
personally identifiable information.  Log only metadata such as image
dimensions, MIME type, and processing durations.
"""

from __future__ import annotations

import logging
import sys


_CONFIGURED = False

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)


def _configure_root() -> None:
    """Set up the root logger once."""
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)

    # Quiet noisy third-party loggers.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with consistent formatting.

    Args:
        name: Usually ``__name__`` of the calling module.

    Returns:
        Configured ``logging.Logger`` instance.

    Usage::

        from app.common.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Processing simulation for zone=%s", zone)
    """
    _configure_root()
    return logging.getLogger(name)
