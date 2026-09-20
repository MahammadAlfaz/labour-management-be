from fastapi import UploadFile

from app.core.errors import AppError
from app.core.image_processing import process_image
from app.core.supabase_storage import delete_image, upload_image

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB, before compression


class InvalidUploadError(AppError):
    status_code = 400
    code = "invalid_upload"


async def handle_photo_upload(
    *, file: UploadFile, folder: str, existing_photo_path: str | None
) -> dict[str, str]:
    """Validate, compress, and store an uploaded photo; clean up the old one."""
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidUploadError("Only JPEG, PNG, WEBP, or HEIC images are allowed")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise InvalidUploadError("Image must be smaller than 8 MB")

    processed = process_image(raw)
    result = await upload_image(folder=folder, content=processed, content_type="image/jpeg")

    if existing_photo_path:
        await delete_image(existing_photo_path)

    return result
