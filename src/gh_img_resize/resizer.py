"""Fit an image to exactly 999 KB while keeping format and aspect ratio."""

from __future__ import annotations

import io
import zlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PIL import (  # noqa: F401
    GifImagePlugin,
    Image,
    ImageOps,
    JpegImagePlugin,
    PngImagePlugin,
    WebPImagePlugin,
)

# GitHub enforces 1 MB as 1,000,000 bytes. 999 KiB (999 * 1024) is 1,022,976
# bytes and is rejected. Use decimal kilobytes so the file stays under that cap.
GITHUB_MAX_BYTES = 1_000_000
TARGET_BYTES = 999 * 1000
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
_FORMAT_BY_SUFFIX = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".webp": "WEBP",
}

ProgressCallback = Callable[[str], None]


class ResizeError(ValueError):
    """Raised when an image cannot be fitted to the target size."""

    def __init__(self, key: str, **params: object) -> None:
        self.key = key
        self.params = params
        super().__init__(key)


@dataclass(frozen=True)
class ResizeResult:
    data: bytes
    format: str
    width: int
    height: int
    original_size: int
    original_width: int
    original_height: int
    padded: bool
    scaled: bool
    reencoded: bool

    @property
    def size(self) -> int:
        return len(self.data)


class _CannotPad(Exception):
    """Encoded payload does not leave enough room for exact padding."""


def resize_to_target(
    path: str | Path,
    target_bytes: int = TARGET_BYTES,
    progress: ProgressCallback | None = None,
) -> ResizeResult:
    """Return image bytes with length exactly ``target_bytes``."""
    if target_bytes >= GITHUB_MAX_BYTES:
        raise ResizeError("error.target_over_limit")
    source = Path(path)
    if source.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ResizeError("error.unsupported_suffix", suffix=source.suffix)

    original = source.read_bytes()
    _emit(progress, "progress.loading")
    with Image.open(io.BytesIO(original)) as src:
        fmt = _normalize_format(src.format, source.suffix)
        original_width, original_height = src.size
        frame = _first_frame(src)
        image = _prepare_image(frame, fmt)

    if len(original) == target_bytes:
        return ResizeResult(
            data=original,
            format=fmt,
            width=original_width,
            height=original_height,
            original_size=len(original),
            original_width=original_width,
            original_height=original_height,
            padded=False,
            scaled=False,
            reencoded=False,
        )

    if len(original) < target_bytes and _can_pad(fmt, len(original), target_bytes):
        _emit(progress, "progress.padding")
        padded = _pad(fmt, original, target_bytes)
        return ResizeResult(
            data=padded,
            format=fmt,
            width=original_width,
            height=original_height,
            original_size=len(original),
            original_width=original_width,
            original_height=original_height,
            padded=True,
            scaled=False,
            reencoded=False,
        )

    _emit(progress, "progress.adjusting")
    encoded, out_image, scaled = _fit_to_target(image, fmt, target_bytes, progress)
    try:
        padded = _pad(fmt, encoded, target_bytes)
    except _CannotPad as exc:
        raise ResizeError("error.cannot_pad") from exc
    return ResizeResult(
        data=padded,
        format=fmt,
        width=out_image.width,
        height=out_image.height,
        original_size=len(original),
        original_width=original_width,
        original_height=original_height,
        padded=len(padded) != len(encoded),
        scaled=scaled,
        reencoded=True,
    )


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)


def _normalize_format(detected: str | None, suffix: str) -> str:
    mapped = _FORMAT_BY_SUFFIX.get(suffix.lower())
    if mapped:
        return mapped
    if not detected:
        raise ResizeError("error.detect_format")
    return "JPEG" if detected.upper() == "JPG" else detected.upper()


def _first_frame(image: Image.Image) -> Image.Image:
    try:
        image.seek(0)
    except EOFError:
        pass
    return image.copy()


def _prepare_image(image: Image.Image, fmt: str) -> Image.Image:
    image = ImageOps.exif_transpose(image) or image
    if fmt == "JPEG":
        if image.mode in {"RGBA", "LA"}:
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1])
            return background
        if image.mode == "P":
            converted = image.convert("RGBA")
            background = Image.new("RGB", converted.size, (255, 255, 255))
            background.paste(converted, mask=converted.split()[-1])
            return background
        if image.mode != "RGB":
            return image.convert("RGB")
        return image
    if fmt == "GIF":
        return image.convert("P", palette=Image.Palette.ADAPTIVE, colors=256)
    if fmt == "PNG" and image.mode not in {"RGB", "RGBA", "L", "LA", "P"}:
        return image.convert("RGBA")
    if fmt == "WEBP" and image.mode not in {"RGB", "RGBA"}:
        return image.convert("RGBA") if "A" in image.mode else image.convert("RGB")
    return image


def _resize_to_width(image: Image.Image, width: int) -> Image.Image:
    width = max(1, width)
    height = max(1, round(image.height * width / image.width))
    if width == image.width and height == image.height:
        return image
    return image.resize((width, height), Image.Resampling.LANCZOS)


def _encode(image: Image.Image, fmt: str, quality: int | None = None) -> bytes:
    buffer = io.BytesIO()
    if fmt == "JPEG":
        image.save(buffer, format="JPEG", quality=quality or 85, optimize=True)
    elif fmt == "WEBP":
        image.save(buffer, format="WEBP", quality=quality or 85, method=4)
    elif fmt == "PNG":
        image.save(buffer, format="PNG", optimize=True, compress_level=9)
    elif fmt == "GIF":
        image.save(buffer, format="GIF", optimize=True)
    else:
        raise ResizeError("error.unsupported_encode_format", fmt=fmt)
    return buffer.getvalue()


def _can_pad(fmt: str, current_len: int, target_bytes: int) -> bool:
    need = target_bytes - current_len
    if need == 0:
        return True
    if need < 0:
        return False
    if fmt == "JPEG":
        return need >= 4
    if fmt == "PNG":
        return need >= 20
    if fmt == "GIF":
        return _gif_padding(need) is not None
    if fmt == "WEBP":
        return need >= 8 and (need - 8) % 2 == 0
    return False


def _fit_to_target(
    image: Image.Image,
    fmt: str,
    target_bytes: int,
    progress: ProgressCallback | None,
) -> tuple[bytes, Image.Image, bool]:
    if fmt in {"JPEG", "WEBP"}:
        found = _search_quality(image, fmt, target_bytes)
        if found is not None:
            return found, image, False
        _emit(progress, "progress.scaling")
        data, scaled_image = _search_scale_lossy(image, fmt, target_bytes)
        return data, scaled_image, True

    found = _try_encode(image, fmt, target_bytes)
    if found is not None:
        return found, image, False
    _emit(progress, "progress.scaling")
    data, scaled_image = _search_scale_lossless(image, fmt, target_bytes)
    return data, scaled_image, True


def _try_encode(
    image: Image.Image,
    fmt: str,
    target_bytes: int,
    quality: int | None = None,
) -> bytes | None:
    data = _encode(image, fmt, quality)
    if _can_pad(fmt, len(data), target_bytes):
        return data
    return None


def _search_quality(image: Image.Image, fmt: str, target_bytes: int) -> bytes | None:
    best: bytes | None = None
    low, high = 1, 95
    while low <= high:
        mid = (low + high) // 2
        data = _try_encode(image, fmt, target_bytes, quality=mid)
        if data is not None:
            best = data
            low = mid + 1
        else:
            high = mid - 1
    return best


def _search_scale_lossy(
    image: Image.Image, fmt: str, target_bytes: int
) -> tuple[bytes, Image.Image]:
    best: tuple[bytes, Image.Image] | None = None
    low, high = 1, image.width
    while low <= high:
        mid = (low + high) // 2
        scaled = _resize_to_width(image, mid)
        data = _search_quality(scaled, fmt, target_bytes)
        if data is not None:
            best = (data, scaled)
            low = mid + 1
        else:
            high = mid - 1
    if best is None:
        raise ResizeError("error.cannot_shrink")
    return best


def _search_scale_lossless(
    image: Image.Image, fmt: str, target_bytes: int
) -> tuple[bytes, Image.Image]:
    best: tuple[bytes, Image.Image] | None = None
    low, high = 1, image.width
    while low <= high:
        mid = (low + high) // 2
        scaled = _resize_to_width(image, mid)
        data = _try_encode(scaled, fmt, target_bytes)
        if data is not None:
            best = (data, scaled)
            low = mid + 1
        else:
            high = mid - 1
    if best is None:
        raise ResizeError("error.cannot_shrink")
    return best


def _pad(fmt: str, data: bytes, target_bytes: int) -> bytes:
    if len(data) == target_bytes:
        return data
    if len(data) > target_bytes:
        raise ResizeError("error.encoded_too_large")
    if fmt == "JPEG":
        return _pad_jpeg(data, target_bytes)
    if fmt == "PNG":
        return _pad_png(data, target_bytes)
    if fmt == "GIF":
        return _pad_gif(data, target_bytes)
    if fmt == "WEBP":
        return _pad_webp(data, target_bytes)
    raise ResizeError("error.unsupported_encode_format", fmt=fmt)


def _pad_jpeg(data: bytes, target_bytes: int) -> bytes:
    eoi = data.rfind(b"\xff\xd9")
    if eoi < 0:
        raise ResizeError("error.jpeg_eoi")
    remaining = target_bytes - len(data)
    if remaining < 4:
        raise _CannotPad
    parts: list[bytes] = []
    while remaining:
        if remaining < 4:
            raise _CannotPad
        take = min(remaining, 4 + 65533)
        leftover = remaining - take
        if 0 < leftover < 4:
            take -= 4 - leftover
        payload_len = take - 4
        length = payload_len + 2
        parts.append(b"\xff\xfe" + length.to_bytes(2, "big") + bytes(payload_len))
        remaining -= take
    return data[:eoi] + b"".join(parts) + data[eoi:]


def _find_png_iend(data: bytes) -> int:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ResizeError("error.not_png")
    pos = 8
    while pos + 12 <= len(data):
        length = int.from_bytes(data[pos : pos + 4], "big")
        chunk_type = data[pos + 4 : pos + 8]
        if chunk_type == b"IEND":
            return pos
        pos += 12 + length
    raise ResizeError("error.png_iend")


def _pad_png(data: bytes, target_bytes: int) -> bytes:
    iend = _find_png_iend(data)
    need = target_bytes - len(data)
    keyword = b"Comment\x00"
    if need < 12 + len(keyword):
        raise _CannotPad
    text = bytes(need - 12 - len(keyword))
    payload = keyword + text
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    chunk = (
        len(payload).to_bytes(4, "big") + chunk_type + payload + crc.to_bytes(4, "big")
    )
    return data[:iend] + chunk + data[iend:]


def _gif_comment(payload: bytes) -> bytes:
    parts = [b"\x21\xfe"]
    if not payload:
        return b"\x21\xfe\x00"
    offset = 0
    while offset < len(payload):
        size = min(255, len(payload) - offset)
        parts.append(bytes([size]) + payload[offset : offset + size])
        offset += size
    parts.append(b"\x00")
    return b"".join(parts)


def _gif_padding(need: int) -> bytes | None:
    if need == 0:
        return b""
    if need < 3 or need == 4:
        return None
    if need % 3 == 0:
        return b"\x21\xfe\x00" * (need // 3)
    for empty_count in range((need // 3) + 1):
        payload_len = need - 4 - 3 * empty_count
        if 1 <= payload_len <= 255:
            return _gif_comment(bytes(payload_len)) + (b"\x21\xfe\x00" * empty_count)
    return None


def _pad_gif(data: bytes, target_bytes: int) -> bytes:
    if not data or data[-1] != 0x3B:
        raise ResizeError("error.gif_trailer")
    padding = _gif_padding(target_bytes - len(data))
    if padding is None:
        raise _CannotPad
    return data[:-1] + padding + data[-1:]


def _pad_webp(data: bytes, target_bytes: int) -> bytes:
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ResizeError("error.not_webp")
    need = target_bytes - len(data)
    extra = need - 8
    if extra < 0 or extra % 2 != 0:
        raise _CannotPad
    payload = bytes(extra)
    chunk = b"META" + extra.to_bytes(4, "little") + payload
    out = bytearray(data + chunk)
    out[4:8] = (len(out) - 8).to_bytes(4, "little")
    return bytes(out)
