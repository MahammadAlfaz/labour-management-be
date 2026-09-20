import io

import pytest
from PIL import Image

from app.core.image_processing import MAX_DIMENSION, InvalidImageError, process_image


def _make_png(width: int, height: int, mode: str = "RGB") -> bytes:
    image = Image.new(mode, (width, height), color=(200, 50, 50, 128) if mode == "RGBA" else (200, 50, 50))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_process_image_rejects_non_image_bytes():
    with pytest.raises(InvalidImageError):
        process_image(b"not an image")


def test_process_image_reencodes_as_jpeg():
    raw = _make_png(400, 300)

    processed = process_image(raw)

    result = Image.open(io.BytesIO(processed))
    assert result.format == "JPEG"
    assert result.mode == "RGB"
    assert result.size == (400, 300)


def test_process_image_flattens_transparency_onto_white():
    raw = _make_png(50, 50, mode="RGBA")

    processed = process_image(raw)

    result = Image.open(io.BytesIO(processed))
    assert result.mode == "RGB"


def test_process_image_downscales_oversized_images():
    raw = _make_png(MAX_DIMENSION + 800, MAX_DIMENSION + 400)

    processed = process_image(raw)

    result = Image.open(io.BytesIO(processed))
    assert max(result.size) <= MAX_DIMENSION
