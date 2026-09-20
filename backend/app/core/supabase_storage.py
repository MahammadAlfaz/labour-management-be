import uuid

import httpx

from app.config import get_settings
from app.core.errors import AppError


class StorageError(AppError):
    status_code = 502
    code = "storage_error"


def _auth_headers(secret_key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {secret_key}", "apikey": secret_key}


async def upload_image(*, folder: str, content: bytes, content_type: str) -> dict[str, str]:
    """Upload processed image bytes to Supabase Storage.

    Returns {"path": <storage path>, "url": <public URL>}. The configured
    bucket must be public -- profile/site photos aren't sensitive, and a
    public bucket avoids the extra round-trip (and staleness) of signed URLs.
    """
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise StorageError("Image storage is not configured")

    path = f"{folder}/{uuid.uuid4().hex}.jpg"
    upload_url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{path}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            upload_url,
            content=content,
            headers={
                **_auth_headers(settings.supabase_secret_key),
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )

    if response.status_code >= 400:
        raise StorageError(f"Image upload failed ({response.status_code})")

    public_url = f"{settings.supabase_url}/storage/v1/object/public/{settings.supabase_bucket}/{path}"
    return {"path": path, "url": public_url}


async def delete_image(path: str) -> None:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_secret_key:
        return

    delete_url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}"
    async with httpx.AsyncClient(timeout=15) as client:
        await client.request(
            "DELETE",
            delete_url,
            json={"prefixes": [path]},
            headers=_auth_headers(settings.supabase_secret_key),
        )
