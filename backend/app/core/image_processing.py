import io

from PIL import Image, ImageOps

from app.core.errors import AppError

MAX_DIMENSION = 1280
JPEG_QUALITY = 82

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    # HEIC/HEIF (iPhone camera photos) support is best-effort; JPEG/PNG/WEBP
    # still work without it.
    pass


class InvalidImageError(AppError):
    status_code = 400
    code = "invalid_image"


def process_image(raw: bytes) -> bytes:
    """Validate, downscale, and re-encode an uploaded image as a compact JPEG.

    Re-encoding everything to JPEG keeps storage/bandwidth predictable and
    sidesteps format-specific quirks (PNG transparency, HEIC from iPhones).
    """
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception as exc:
        raise InvalidImageError("File is not a valid image") from exc

    image = ImageOps.exif_transpose(image) or image

    if image.mode not in ("RGB",):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        image = background

    image.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return buffer.getvalue()
