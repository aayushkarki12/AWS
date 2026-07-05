"""Secure handling of user-uploaded files (currently: profile pictures)."""
import uuid
from pathlib import Path

from fastapi import UploadFile, status

from app.core.config import settings
from app.core.exceptions import AppException

_ALLOWED_CONTENT_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class InvalidUploadError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_CONTENT, "invalid_upload")


async def save_avatar(employee_id: uuid.UUID, file: UploadFile) -> str:
    """Validates and persists an avatar image, returning its public URL path."""
    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise InvalidUploadError("Only JPEG, PNG, or WebP images are allowed")

    max_bytes = settings.MAX_AVATAR_SIZE_MB * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_bytes:
        raise InvalidUploadError(f"Image must be smaller than {settings.MAX_AVATAR_SIZE_MB}MB")
    if len(contents) == 0:
        raise InvalidUploadError("Uploaded file is empty")

    extension = _ALLOWED_CONTENT_TYPES[file.content_type]
    # Filename is derived entirely from the employee id + a fixed extension map —
    # never from client-supplied input — so there's no path traversal surface.
    filename = f"{employee_id}.{extension}"

    avatars_dir = Path(settings.UPLOAD_DIR) / "avatars"
    avatars_dir.mkdir(parents=True, exist_ok=True)

    # Remove any previously stored avatar for this employee under a different extension.
    for existing_ext in _ALLOWED_CONTENT_TYPES.values():
        stale = avatars_dir / f"{employee_id}.{existing_ext}"
        if existing_ext != extension and stale.exists():
            stale.unlink()

    destination = avatars_dir / filename
    destination.write_bytes(contents)

    return f"{settings.UPLOAD_URL_PREFIX}/avatars/{filename}"
