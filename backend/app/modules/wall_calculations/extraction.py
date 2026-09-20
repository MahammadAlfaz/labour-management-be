import json
from decimal import Decimal, InvalidOperation

from app.core.gemini_client import GeminiError, generate_content_from_image
from app.core.image_processing import process_image
from app.core.photo_upload import ALLOWED_CONTENT_TYPES, MAX_UPLOAD_BYTES, InvalidUploadError
from app.core.supabase_storage import upload_image
from app.modules.wall_calculations.schemas import (
    ExtractedMeasurement,
    ExtractionResult,
    MeasurementConfidence,
)

EXTRACTION_PROMPT = """\
You are reading a handwritten construction measurement sheet. Each line lists \
a length (often a mixed number with a fraction such as 31 1/4 or 31 ¼) and \
a quantity (e.g. "1 pc", "3 pcs").

Return ONLY a JSON array (no prose, no markdown fences). Each element must be:
{"raw_text": "<the line as written>", "length_decimal": <number>, \
"quantity": <integer>, "confidence": "high" or "low"}

Rules:
- Convert fractions (halves, quarters, eighths, etc., in any notation) to a \
decimal number.
- Extract ONLY length and quantity from each line. Never output a height or \
breadth value -- those are entered separately by the user and are not part of \
this sheet.
- If a line is partially illegible or ambiguous, still include your best \
reading and set "confidence" to "low". Never omit a line you can partially \
read, and never silently guess without flagging it as "low" confidence.
- If nothing on the image is legible, return [].
"""


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned
    lines = cleaned.split("\n")[1:]
    if lines and lines[-1].strip().startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()


def _parse_response(text: str) -> tuple[list[ExtractedMeasurement], list[str]]:
    cleaned = _strip_code_fence(text)
    try:
        raw_rows = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as exc:
        raise GeminiError("Could not read the AI response; enter measurements manually") from exc

    if not isinstance(raw_rows, list):
        raise GeminiError("Could not read the AI response; enter measurements manually")

    rows: list[ExtractedMeasurement] = []
    warnings: list[str] = []
    for index, item in enumerate(raw_rows, start=1):
        try:
            length = Decimal(str(item["length_decimal"]))
            quantity = int(item["quantity"])
            if length <= 0 or quantity < 1:
                raise ValueError("non-positive value")
            confidence = (
                MeasurementConfidence.LOW
                if str(item.get("confidence", "high")).lower() == "low"
                else MeasurementConfidence.HIGH
            )
            rows.append(
                ExtractedMeasurement(
                    raw_text=str(item.get("raw_text", ""))[:200],
                    length=length,
                    quantity=quantity,
                    confidence=confidence,
                )
            )
        except (KeyError, ValueError, InvalidOperation, TypeError):
            warnings.append(f"Line {index} could not be read and was skipped")

    if not rows and not warnings:
        warnings.append("No measurements were detected in the image")

    return rows, warnings


async def extract_measurements_from_image(*, content_type: str | None, raw_bytes: bytes) -> ExtractionResult:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise InvalidUploadError("Only JPEG, PNG, WEBP, or HEIC images are allowed")
    if len(raw_bytes) > MAX_UPLOAD_BYTES:
        raise InvalidUploadError("Image must be smaller than 8 MB")

    processed = process_image(raw_bytes)
    upload_result = await upload_image(
        folder="wall-calculations", content=processed, content_type="image/jpeg"
    )

    text = await generate_content_from_image(
        image_bytes=processed, mime_type="image/jpeg", prompt=EXTRACTION_PROMPT
    )
    rows, warnings = _parse_response(text)

    return ExtractionResult(
        source_image_path=upload_result["path"], measurements=rows, warnings=warnings
    )
