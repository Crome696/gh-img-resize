from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gh_img_resize.i18n import (
    CATALOGS,
    DEFAULT_LANGUAGE,
    LANGUAGE_ORDER,
    SWITCHER_CODES,
    config_dir,
    detect_os_language,
    language_from_switcher,
    load_saved_language,
    normalize_language,
    resolve_language,
    save_language,
    switcher_from_language,
    translate,
)
from gh_img_resize.resizer import ResizeError, resize_to_target


class CatalogTests(unittest.TestCase):
    def test_language_order_matches_switcher_codes(self) -> None:
        self.assertEqual(
            LANGUAGE_ORDER,
            ("en", "es", "de", "fr", "it", "pt-BR", "ja", "ko", "zh-CN"),
        )
        self.assertEqual(
            SWITCHER_CODES,
            ("EN", "ES", "DE", "FR", "IT", "PT-BR", "JA", "KO", "ZH-CN"),
        )
        for code, language in zip(SWITCHER_CODES, LANGUAGE_ORDER, strict=True):
            self.assertEqual(language_from_switcher(code), language)
            self.assertEqual(switcher_from_language(language), code)

    def test_every_catalog_has_the_english_keys(self) -> None:
        expected = set(CATALOGS[DEFAULT_LANGUAGE])
        for language, catalog in CATALOGS.items():
            with self.subTest(language=language):
                self.assertEqual(set(catalog), expected)
                for key, value in catalog.items():
                    self.assertTrue(value, msg=f"{language}:{key} is empty")


class LocaleMatchingTests(unittest.TestCase):
    def test_supported_os_tags_map_to_languages(self) -> None:
        cases = {
            "en-US": "en",
            "es_MX.UTF-8": "es",
            "de_DE": "de",
            "fr-CA": "fr",
            "it-IT": "it",
            "pt-BR": "pt-BR",
            "pt_BR": "pt-BR",
            "ja_JP": "ja",
            "ko-KR": "ko",
            "zh-CN": "zh-CN",
            "zh_CN.UTF-8": "zh-CN",
            "zh-Hans": "zh-CN",
            "zh": "zh-CN",
        }
        for tag, language in cases.items():
            with self.subTest(tag=tag):
                self.assertEqual(normalize_language(tag), language)

    def test_unsupported_os_tags_do_not_match(self) -> None:
        for tag in ("pt-PT", "zh-TW", "zh-Hant", "zh-HK", "nl-NL", "sv_SE", ""):
            with self.subTest(tag=tag):
                self.assertIsNone(normalize_language(tag))

    def test_detect_os_language_returns_first_supported_tag(self) -> None:
        self.assertEqual(detect_os_language(["nl-NL", "de-DE", "en-US"]), "de")
        self.assertIsNone(detect_os_language(["nl-NL", "pt-PT"]))


class LanguageResolutionTests(unittest.TestCase):
    def test_saved_language_wins_over_os_locale(self) -> None:
        self.assertEqual(resolve_language("ja", "de"), "ja")

    def test_os_locale_is_used_when_nothing_is_saved(self) -> None:
        self.assertEqual(resolve_language(None, "fr"), "fr")

    def test_unsupported_os_locale_falls_back_to_english(self) -> None:
        self.assertEqual(resolve_language(None, None), "en")


class SettingsPersistenceTests(unittest.TestCase):
    def test_save_and_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "settings.json"
            save_language("ko", path=path)
            self.assertEqual(load_saved_language(path=path), "ko")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload, {"language": "ko"})

    def test_missing_or_invalid_settings_return_none(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            missing = Path(raw) / "missing.json"
            invalid = Path(raw) / "settings.json"
            invalid.write_text("{not json", encoding="utf-8")
            self.assertIsNone(load_saved_language(path=missing))
            self.assertIsNone(load_saved_language(path=invalid))
            invalid.write_text('{"language": "nl"}\n', encoding="utf-8")
            self.assertIsNone(load_saved_language(path=invalid))

    def test_windows_config_dir_uses_appdata(self) -> None:
        with patch("gh_img_resize.i18n.sys.platform", "win32"):
            path = config_dir(
                environ={"APPDATA": r"C:\Users\demo\AppData\Roaming"},
                home=Path(r"C:\Users\demo"),
            )
        self.assertEqual(path, Path(r"C:\Users\demo\AppData\Roaming") / "gh-img-resize")


class TranslateTests(unittest.TestCase):
    def test_translate_formats_active_language(self) -> None:
        german = translate("de", "button.save")
        english = translate("en", "button.save")
        self.assertEqual(german, "Als 999 KB speichern…")
        self.assertEqual(english, "Save as 999 KB…")
        self.assertNotEqual(german, english)
        selected = translate(
            "de",
            "info.selected",
            name="demo.png",
            fmt="PNG",
            width=1,
            height=1,
            bytes=2,
            kb=0.002,
            target=999000,
        )
        self.assertIn("Datei: demo.png", selected)

    def test_immediate_switch_does_not_require_restart(self) -> None:
        before = translate("en", "window.title")
        after = translate("zh-CN", "window.title")
        self.assertNotEqual(before, after)
        self.assertEqual(translate("en", "window.title"), before)


class ResizerLocalizationTests(unittest.TestCase):
    def test_progress_callback_receives_stable_keys(self) -> None:
        messages: list[str] = []

        def progress(message: str) -> None:
            messages.append(message)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as handle:
            path = Path(handle.name)
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        from PIL import Image

        Image.new("RGB", (32, 32), (12, 80, 160)).save(path, format="JPEG", quality=80)
        result = resize_to_target(path, progress=progress)
        self.assertEqual(result.size, 999_000)
        self.assertTrue(messages)
        self.assertTrue(all(item.startswith("progress.") for item in messages))

    def test_unsupported_suffix_uses_error_key(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as handle:
            path = Path(handle.name)
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        path.write_bytes(b"not-an-image")
        with self.assertRaises(ResizeError) as raised:
            resize_to_target(path)
        self.assertEqual(raised.exception.key, "error.unsupported_suffix")
        translated = translate("en", raised.exception.key, **raised.exception.params)
        self.assertIn(".bmp", translated)


if __name__ == "__main__":
    unittest.main()
