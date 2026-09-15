"""
Common image I/O utilities.

Provides shared helpers for decoding, encoding, and converting images
between formats used across the simulation engine.  All region-specific
modules should use these rather than implementing their own image
loading logic.

Shared MediaPipe / OpenCV initialisation belongs here; region-specific
landmark *selection* belongs in the corresponding simulation module.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


# ── Decoding ────────────────────────────────────────────────────────


def decode_image(raw_bytes: bytes) -> "np.ndarray":
    """Decode raw image bytes (JPEG/PNG/WebP) into a BGR NumPy array.

    Args:
        raw_bytes: Raw file content.

    Returns:
        HxWx3 uint8 NumPy array in BGR colour order (OpenCV convention).

    Raises:
        ImageValidationError: If the image cannot be decoded.

    TODO:
        Implement using ``cv2.imdecode`` once opencv-python is added to
        requirements.
    """
    raise NotImplementedError("decode_image is not yet implemented.")


def encode_image(image: "np.ndarray", *, fmt: str = ".png") -> bytes:
    """Encode a BGR NumPy array back into image bytes.

    Args:
        image: HxWx3 uint8 NumPy array.
        fmt: Target format extension, e.g. ``'.png'``, ``'.jpg'``.

    Returns:
        Encoded image bytes.

    TODO:
        Implement using ``cv2.imencode``.
    """
    raise NotImplementedError("encode_image is not yet implemented.")


# ── URL loading ─────────────────────────────────────────────────────


async def load_image_from_url(url: str) -> "np.ndarray":
    """Download an image from *url* and return it as a NumPy array.

    This is the primary way the backend will receive images from the
    frontend via Cloudinary temporary URLs.

    Args:
        url: Public or signed image URL.

    Returns:
        Decoded HxWx3 uint8 NumPy array.

    TODO:
        Implement with ``httpx`` async download + ``decode_image``.
    """
    raise NotImplementedError("load_image_from_url is not yet implemented.")


# ── Base-64 helpers ─────────────────────────────────────────────────


def image_to_base64(image: "np.ndarray", *, fmt: str = ".png") -> str:
    """Encode a NumPy image to a base-64 data URI string.

    Useful for returning inline preview images in API responses during
    development.

    Args:
        image: HxWx3 uint8 NumPy array.
        fmt: Image format extension.

    Returns:
        ``data:image/<type>;base64,<data>`` string.

    TODO:
        Implement using ``encode_image`` + ``base64.b64encode``.
    """
    raise NotImplementedError("image_to_base64 is not yet implemented.")
