from __future__ import annotations

import subprocess
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from gh_img_resize.theme import (
    DARK,
    LIGHT,
    detect_system_appearance,
    palette_for,
)


class PaletteTests(unittest.TestCase):
    def test_palette_for_selects_light_and_dark(self) -> None:
        self.assertIs(palette_for("light"), LIGHT)
        self.assertIs(palette_for("dark"), DARK)

    def test_light_and_dark_keep_one_accent_and_distinct_surfaces(self) -> None:
        self.assertNotEqual(LIGHT.background, DARK.background)
        self.assertNotEqual(LIGHT.surface, LIGHT.background)
        self.assertNotEqual(DARK.surface, DARK.background)
        self.assertTrue(LIGHT.accent)
        self.assertTrue(DARK.accent)
        self.assertNotEqual(LIGHT.text, LIGHT.muted)
        self.assertNotEqual(DARK.text, DARK.muted)


class DetectAppearanceTests(unittest.TestCase):
    @patch("gh_img_resize.theme.platform.system", return_value="Windows")
    @patch("gh_img_resize.theme._windows_appearance", return_value="dark")
    def test_windows_uses_windows_probe(
        self, windows_probe: MagicMock, _system: MagicMock
    ) -> None:
        self.assertEqual(detect_system_appearance(), "dark")
        windows_probe.assert_called_once_with()

    @patch("gh_img_resize.theme.platform.system", return_value="Darwin")
    @patch("gh_img_resize.theme._macos_appearance", return_value="dark")
    def test_macos_uses_macos_probe(
        self, macos_probe: MagicMock, _system: MagicMock
    ) -> None:
        self.assertEqual(detect_system_appearance(), "dark")
        macos_probe.assert_called_once_with()

    @patch("gh_img_resize.theme.platform.system", return_value="Linux")
    @patch("gh_img_resize.theme._linux_appearance", return_value="light")
    def test_other_platforms_use_linux_probe(
        self, linux_probe: MagicMock, _system: MagicMock
    ) -> None:
        self.assertEqual(detect_system_appearance(), "light")
        linux_probe.assert_called_once_with()


class _Key:
    def __enter__(self) -> object:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def _fake_winreg(*, value: int = 1, missing: bool = False) -> SimpleNamespace:
    open_key = (
        MagicMock(side_effect=OSError("missing"))
        if missing
        else MagicMock(return_value=_Key())
    )
    return SimpleNamespace(
        HKEY_CURRENT_USER="hkcu",
        OpenKey=open_key,
        QueryValueEx=MagicMock(return_value=(value, 4)),
    )


class WindowsAppearanceTests(unittest.TestCase):
    def test_missing_registry_falls_back_to_light(self) -> None:
        with patch.dict("sys.modules", {"winreg": _fake_winreg(missing=True)}):
            from gh_img_resize.theme import _windows_appearance

            self.assertEqual(_windows_appearance(), "light")

    def test_apps_use_light_theme_zero_is_dark(self) -> None:
        with patch.dict("sys.modules", {"winreg": _fake_winreg(value=0)}):
            from gh_img_resize.theme import _windows_appearance

            self.assertEqual(_windows_appearance(), "dark")

    def test_apps_use_light_theme_one_is_light(self) -> None:
        with patch.dict("sys.modules", {"winreg": _fake_winreg(value=1)}):
            from gh_img_resize.theme import _windows_appearance

            self.assertEqual(_windows_appearance(), "light")


class MacosAppearanceTests(unittest.TestCase):
    @patch("gh_img_resize.theme._run_probe")
    def test_dark_stdout_is_dark(self, run_probe: MagicMock) -> None:
        run_probe.return_value = subprocess.CompletedProcess(
            args=["defaults"], returncode=0, stdout="Dark\n", stderr=""
        )
        from gh_img_resize.theme import _macos_appearance

        self.assertEqual(_macos_appearance(), "dark")

    @patch("gh_img_resize.theme._run_probe", return_value=None)
    def test_missing_defaults_falls_back_to_light(self, _run_probe: MagicMock) -> None:
        from gh_img_resize.theme import _macos_appearance

        self.assertEqual(_macos_appearance(), "light")


class LinuxAppearanceTests(unittest.TestCase):
    @patch.dict("os.environ", {"GTK_THEME": "Adwaita-dark"}, clear=False)
    def test_gtk_theme_env_dark(self) -> None:
        from gh_img_resize.theme import _linux_appearance

        self.assertEqual(_linux_appearance(), "dark")

    @patch.dict("os.environ", {"GTK_THEME": ""}, clear=False)
    @patch("gh_img_resize.theme._run_probe")
    def test_gsettings_prefer_dark(self, run_probe: MagicMock) -> None:
        run_probe.return_value = subprocess.CompletedProcess(
            args=["gsettings"],
            returncode=0,
            stdout="'prefer-dark'\n",
            stderr="",
        )
        from gh_img_resize.theme import _linux_appearance

        self.assertEqual(_linux_appearance(), "dark")

    @patch.dict("os.environ", {"GTK_THEME": ""}, clear=False)
    @patch("gh_img_resize.theme._run_probe", return_value=None)
    def test_unknown_linux_falls_back_to_light(self, _run_probe: MagicMock) -> None:
        from gh_img_resize.theme import _linux_appearance

        self.assertEqual(_linux_appearance(), "light")


class ProbeTests(unittest.TestCase):
    @patch("gh_img_resize.theme.subprocess.run", side_effect=OSError("missing"))
    def test_run_probe_returns_none_on_oserror(self, _run: MagicMock) -> None:
        from gh_img_resize.theme import _run_probe

        self.assertIsNone(_run_probe(["defaults"]))


if __name__ == "__main__":
    unittest.main()
