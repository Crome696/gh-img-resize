"""Resize images to exactly 999 KB for GitHub uploads."""

from gh_img_resize.resizer import (
    GITHUB_MAX_BYTES,
    TARGET_BYTES,
    ResizeResult,
    resize_to_target,
)

__all__ = ["GITHUB_MAX_BYTES", "TARGET_BYTES", "ResizeResult", "resize_to_target"]
