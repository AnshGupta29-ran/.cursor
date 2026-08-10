"""Upload validation: magic-byte sniffing, size, dimensions, decodability."""
import io

from PIL import Image

from .errors import ApiError

# Decompression-bomb guard
Image.MAX_IMAGE_PIXELS = 89_478_485  # PIL's default; set explicitly for clarity

_MAGIC_SIGNATURES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],  # refined below via bytes[8:12] == WEBP
}

ALLOWED_CONTENT_TYPES = set(_MAGIC_SIGNATURES)


def sniff_content_type(data: bytes) -> str | None:
    """Detect image type from magic bytes only — never the declared content-type."""
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image_bytes(data: bytes, max_bytes: int, min_dimension: int) -> tuple[str, int, int]:
    """Validate raw upload bytes. Returns (content_type, width, height).

    Raises ApiError with a distinct 4xx code per failure mode.
    """
    if not data:
        raise ApiError(422, "empty_file", "Uploaded file is empty (0 bytes).")

    if len(data) > max_bytes:
        raise ApiError(
            413,
            "file_too_large",
            f"File is {len(data)} bytes; maximum allowed is {max_bytes} bytes.",
        )

    content_type = sniff_content_type(data)
    if content_type is None:
        raise ApiError(
            415,
            "unsupported_media_type",
            "File is not a JPEG, PNG, or WebP image (magic-byte check failed).",
        )

    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()  # cheap structural check
        with Image.open(io.BytesIO(data)) as img:
            img.load()  # full decode — catches truncated/corrupt payloads
            width, height = img.size
    except ApiError:
        raise
    except Exception:
        raise ApiError(422, "corrupt_image", "File could not be decoded as an image.")

    if width < min_dimension or height < min_dimension:
        raise ApiError(
            422,
            "dimensions_too_small",
            f"Image is {width}x{height}; minimum dimension is {min_dimension}px.",
        )

    return content_type, width, height
