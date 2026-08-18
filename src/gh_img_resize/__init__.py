"""Resize images to exactly 999 KB for GitHub uploads."""

from gh_img_resize.resizer import (
    GITHUB_MAX_BYTES,
    TARGET_BYTES,
    ResizeResult,
    resize_to_target,
)

__version__ = "1.0.0"

__all__ = [
    "GITHUB_MAX_BYTES",
    "TARGET_BYTES",
    "ResizeResult",
    "__version__",
    "resize_to_target",
]
