from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from gh_img_resize.resizer import GITHUB_MAX_BYTES, TARGET_BYTES, resize_to_target


def _aspect(width: int, height: int) -> float:
    return width / height


class ResizeToTargetTests(unittest.TestCase):
    def test_target_is_decimal_999kb_under_github_1mb(self) -> None:
        self.assertEqual(TARGET_BYTES, 999_000)
        self.assertLess(TARGET_BYTES, GITHUB_MAX_BYTES)
        self.assertEqual(GITHUB_MAX_BYTES, 1_000_000)

    def _write(self, image: Image.Image, suffix: str, **save_kwargs) -> Path:
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        handle.close()
        path = Path(handle.name)
        image.save(path, **save_kwargs)
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        return path

    def _assert_target_file(self, source: Path, expected_format: str) -> None:
        with Image.open(source) as original:
            original_aspect = _aspect(*original.size)

        result = resize_to_target(source)
        self.assertEqual(result.size, TARGET_BYTES)
        self.assertEqual(len(result.data), TARGET_BYTES)
        self.assertEqual(result.format, expected_format)

        with Image.open(io.BytesIO(result.data)) as output:
            self.assertEqual(output.format, expected_format)
            output_aspect = _aspect(*output.size)
            self.assertAlmostEqual(original_aspect, output_aspect, places=2)
            output.load()

    def test_large_jpeg_matches_target_size_and_aspect(self) -> None:
        image = Image.frombytes("RGB", (1600, 900), os.urandom(1600 * 900 * 3))
        source = self._write(image, ".jpg", format="JPEG", quality=95)
        self.assertGreater(source.stat().st_size, TARGET_BYTES)
        self._assert_target_file(source, "JPEG")

    def test_large_png_matches_target_size_and_aspect(self) -> None:
        image = Image.frombytes("RGB", (900, 900), os.urandom(900 * 900 * 3))
        source = self._write(image, ".png", format="PNG", compress_level=1)
        self.assertGreater(source.stat().st_size, TARGET_BYTES)
        self._assert_target_file(source, "PNG")

    def test_small_jpeg_is_padded_without_reencode(self) -> None:
        image = Image.new("RGB", (32, 32), (12, 80, 160))
        source = self._write(image, ".jpg", format="JPEG", quality=80)
        self.assertLess(source.stat().st_size, TARGET_BYTES)
        result = resize_to_target(source)
        self.assertEqual(result.size, TARGET_BYTES)
        self.assertFalse(result.reencoded)
        self.assertTrue(result.padded)
        with Image.open(io.BytesIO(result.data)) as output:
            self.assertEqual(output.format, "JPEG")
            self.assertEqual(output.size, (32, 32))


if __name__ == "__main__":
    unittest.main()
