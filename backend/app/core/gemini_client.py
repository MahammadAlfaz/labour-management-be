from google import genai
from google.genai import types

from app.config import get_settings
from app.core.errors import AppError


class GeminiError(AppError):
    status_code = 502
    code = "gemini_error"


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise GeminiError("AI extraction is not configured")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def generate_content_from_image(*, image_bytes: bytes, mime_type: str, prompt: str) -> str:
    """Send one image + prompt to Gemini and return the raw text response.

    Any SDK/network failure is wrapped as GeminiError so callers get a
    consistent 502 with a message safe to show the admin, rather than a raw
    stack trace or provider-specific exception type.
    """
    client = _get_client()
    settings = get_settings()

    try:
        response = await client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
    except GeminiError:
        raise
    except Exception as exc:
        raise GeminiError("AI extraction request failed") from exc

    if not response.text:
        raise GeminiError("AI extraction returned an empty response")

    return response.text
