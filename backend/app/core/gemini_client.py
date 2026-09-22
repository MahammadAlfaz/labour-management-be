import logging

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)


class GeminiError(AppError):
    status_code = 502
    code = "gemini_error"


_client: genai.Client | None = None

# Google's own error message for 503s calls these spikes "usually temporary" --
# a short retry clears most of them. 429 (rate limit) can also briefly recover
# within a couple of seconds. Anything else (bad request, auth, etc.) is not
# retried since retrying won't change the outcome.
_RETRYABLE_STATUS_CODES = {429, 503}

# If the configured model (settings.gemini_model) keeps failing -- e.g. a
# brand-new model hitting a sustained capacity issue on Google's side -- fall
# through to progressively more established models rather than surfacing an
# error the admin can do nothing about.
_FALLBACK_MODELS = ["gemini-flash-lite-latest", "gemini-2.5-flash"]


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, genai_errors.APIError) and exc.code in _RETRYABLE_STATUS_CODES


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise GeminiError("AI extraction is not configured")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


@retry(
    retry=retry_if_exception(_is_retryable),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
async def _generate_content(
    client: genai.Client, *, model: str, contents, config: types.GenerateContentConfig | None = None
) -> types.GenerateContentResponse:
    if config is not None:
        return await client.aio.models.generate_content(model=model, contents=contents, config=config)
    return await client.aio.models.generate_content(model=model, contents=contents)


async def _generate_with_model_fallback(
    client: genai.Client, *, contents, config: types.GenerateContentConfig | None = None
) -> types.GenerateContentResponse:
    """Try the configured model first (with its own quick retry above); if it
    still fails, work through _FALLBACK_MODELS in order rather than giving up
    immediately -- only raises once every model in the chain has failed.
    """
    settings = get_settings()
    models_to_try = [settings.gemini_model] + [m for m in _FALLBACK_MODELS if m != settings.gemini_model]

    last_exc: Exception | None = None
    for model in models_to_try:
        try:
            return await _generate_content(client, model=model, contents=contents, config=config)
        except Exception as exc:
            logger.warning("Gemini model %s failed, trying next in fallback chain: %r", model, exc)
            last_exc = exc
            continue

    assert last_exc is not None
    raise last_exc


async def generate_content_from_image(*, image_bytes: bytes, mime_type: str, prompt: str) -> str:
    """Send one image + prompt to Gemini and return the raw text response.

    Any SDK/network failure is wrapped as GeminiError so callers get a
    consistent 502 with a message safe to show the admin, rather than a raw
    stack trace or provider-specific exception type.
    """
    client = _get_client()

    try:
        response = await _generate_with_model_fallback(
            client,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
        )
    except GeminiError:
        raise
    except Exception as exc:
        logger.warning("Gemini image extraction failed: %r", exc)
        raise GeminiError("AI extraction request failed") from exc

    if not response.text:
        raise GeminiError("AI extraction returned an empty response")

    return response.text


async def generate_with_tools(
    *, contents: list[types.Content], config: types.GenerateContentConfig
) -> types.GenerateContentResponse:
    """Send a multi-turn conversation (optionally with function-calling tools)
    to Gemini and return the full response, since callers need to inspect
    candidate.content.parts for function calls rather than just the text.
    """
    client = _get_client()

    try:
        response = await _generate_with_model_fallback(client, contents=contents, config=config)
    except GeminiError:
        raise
    except Exception as exc:
        logger.warning("Gemini chat request failed: %r", exc)
        raise GeminiError("AI assistant request failed") from exc

    return response
