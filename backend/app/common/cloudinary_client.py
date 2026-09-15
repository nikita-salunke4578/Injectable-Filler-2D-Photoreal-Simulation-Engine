"""
Cloudinary integration client.

Wraps the Cloudinary Python SDK to provide temporary image storage for
the simulation pipeline.  All credentials come from environment
variables via ``app.common.config``.

**Privacy note:** Uploaded images are intended to be *temporary*.  The
caller is responsible for calling ``delete_image`` after the simulation
result has been delivered to the frontend.  Do not rely on Cloudinary
as permanent biometric storage.

Usage:
    from app.common.cloudinary_client import CloudinaryClient

    client = CloudinaryClient()
    url = await client.upload_temp_image(image_bytes, "sim_12345")
    ...
    await client.delete_image("sim_12345")
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class CloudinaryClient:
    """Manages temporary image uploads and deletions on Cloudinary.

    TODO:
        - Install ``cloudinary`` package.
        - Initialise ``cloudinary.config()`` from ``get_settings()``.
        - Implement upload/download/delete using the Cloudinary SDK.
    """

    def __init__(self) -> None:
        # TODO: Call cloudinary.config(...) here using get_settings().
        logger.info(
            "CloudinaryClient created (placeholder — SDK not yet initialised)"
        )

    async def upload_temp_image(
        self,
        image_bytes: bytes,
        public_id: str,
        *,
        folder: str = "simulations",
    ) -> str:
        """Upload image bytes to Cloudinary with a temporary lifecycle.

        Args:
            image_bytes: Encoded image data (JPEG/PNG).
            public_id: Unique identifier for this image.
            folder: Cloudinary folder for organisation.

        Returns:
            The secure URL of the uploaded image.

        TODO:
            Use ``cloudinary.uploader.upload`` with type="private" and
            appropriate expiry settings.
        """
        raise NotImplementedError("upload_temp_image is not yet implemented.")

    async def get_image_url(self, public_id: str) -> str:
        """Get the secure URL for a previously uploaded image.

        Args:
            public_id: Cloudinary public ID.

        Returns:
            Signed/secure URL string.

        TODO:
            Implement using ``cloudinary.utils.cloudinary_url``.
        """
        raise NotImplementedError("get_image_url is not yet implemented.")

    async def delete_image(self, public_id: str) -> bool:
        """Delete a temporary image from Cloudinary.

        Should be called after the simulation result has been delivered
        to the user.

        Args:
            public_id: Cloudinary public ID.

        Returns:
            ``True`` if deletion was successful.

        TODO:
            Implement using ``cloudinary.uploader.destroy``.
        """
        raise NotImplementedError("delete_image is not yet implemented.")
