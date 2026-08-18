"""Startup-only OS light/dark palettes for the Tkinter desktop UI."""

from __future__ import annotations

import os
import platform
import subprocess
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from tkinter import ttk
from typing import Literal

Appearance = Literal["light", "dark"]


@dataclass(frozen=True)
class Palette:
    appearance: Appearance
    background: str
    surface: str
    text: str
    muted: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_disabled: str
    accent_text: str
    border: str
    preview: str
    error: str


LIGHT = Palette(
    appearance="light",
    background="#F4F6F8",
    surface="#FFFFFF",
    text="#1F2328",
    muted="#656D76",
    accent="#0969DA",
    accent_hover="#0860CA",
    accent_pressed="#0550AE",
    accent_disabled="#9DC3F0",
    accent_text="#FFFFFF",
    border="#D0D7DE",
    preview="#EAEEF2",
    error="#CF222E",
)

DARK = Palette(
    appearance="dark",
    background="#0D1117",
    surface="#161B22",
    text="#E6EDF3",
    muted="#8B949E",
    accent="#4493F8",
    accent_hover="#316DCA",
    accent_pressed="#1F57B5",
    accent_disabled="#2F4668",
    accent_text="#0D1117",
    border="#30363D",
    preview="#21262D",
    error="#F85149",
)


def palette_for(appearance: Appearance) -> Palette:
    return DARK if appearance == "dark" else LIGHT


def detect_system_appearance() -> Appearance:
    """Read the OS color scheme once at startup. Unknown probes fall back to light."""
    system = platform.system()
    if system == "Windows":
        return _windows_appearance()
    if system == "Darwin":
        return _macos_appearance()
    return _linux_appearance()


def apply_theme(root: tk.Misc, palette: Palette) -> ttk.Style:
    """Apply a clam ttk theme so light and dark palettes stay consistent across OSes."""
    root.configure(background=palette.background)
    _configure_fonts(root)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        ".",
        background=palette.background,
        foreground=palette.text,
        bordercolor=palette.border,
        darkcolor=palette.surface,
        lightcolor=palette.surface,
        troughcolor=palette.preview,
        focuscolor=palette.accent,
    )
    heading = None
    body = None
    try:
        heading = tkfont.nametofont("TkHeadingFont")
        body = tkfont.nametofont("TkDefaultFont")
    except tk.TclError:
        pass

    style.configure("Canvas.TFrame", background=palette.background)
    style.configure(
        "Card.TFrame",
        background=palette.surface,
        bordercolor=palette.border,
        relief="flat",
        borderwidth=0,
    )
    style.configure(
        "Title.TLabel",
        background=palette.background,
        foreground=palette.text,
        font=heading,
    )
    style.configure(
        "Subtitle.TLabel",
        background=palette.background,
        foreground=palette.muted,
        font=body,
    )
    style.configure(
        "Body.TLabel",
        background=palette.surface,
        foreground=palette.text,
        font=body,
    )
    style.configure(
        "Muted.TLabel",
        background=palette.surface,
        foreground=palette.muted,
        font=body,
    )
    style.configure(
        "Error.TLabel",
        background=palette.surface,
        foreground=palette.error,
        font=body,
    )
    style.configure(
        "Preview.TLabel",
        background=palette.preview,
        foreground=palette.muted,
        font=body,
        anchor="center",
        padding=16,
    )
    style.configure(
        "Secondary.TButton",
        background=palette.surface,
        foreground=palette.text,
        bordercolor=palette.border,
        darkcolor=palette.surface,
        lightcolor=palette.surface,
        focusthickness=1,
        focuscolor=palette.accent,
        padding=(14, 10),
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("disabled", palette.preview),
            ("pressed", palette.preview),
            ("active", palette.preview),
        ],
        foreground=[("disabled", palette.muted)],
        bordercolor=[("disabled", palette.border)],
    )
    style.configure(
        "Accent.TButton",
        background=palette.accent,
        foreground=palette.accent_text,
        bordercolor=palette.accent,
        darkcolor=palette.accent,
        lightcolor=palette.accent,
        focusthickness=1,
        focuscolor=palette.accent,
        padding=(16, 10),
    )
    style.map(
        "Accent.TButton",
        background=[
            ("disabled", palette.accent_disabled),
            ("pressed", palette.accent_pressed),
            ("active", palette.accent_hover),
        ],
        foreground=[("disabled", palette.accent_text)],
        bordercolor=[
            ("disabled", palette.accent_disabled),
            ("pressed", palette.accent_pressed),
            ("active", palette.accent_hover),
        ],
    )
    style.configure(
        "TCombobox",
        fieldbackground=palette.surface,
        background=palette.surface,
        foreground=palette.text,
        bordercolor=palette.border,
        arrowcolor=palette.text,
        lightcolor=palette.surface,
        darkcolor=palette.surface,
        padding=(6, 4),
    )
    style.map(
        "TCombobox",
        fieldbackground=[
            ("readonly", palette.surface),
            ("disabled", palette.preview),
        ],
        foreground=[
            ("readonly", palette.text),
            ("disabled", palette.muted),
        ],
        background=[("readonly", palette.surface)],
        arrowcolor=[("disabled", palette.muted)],
    )
    root.option_add("*TCombobox*Listbox.background", palette.surface)
    root.option_add("*TCombobox*Listbox.foreground", palette.text)
    root.option_add("*TCombobox*Listbox.selectBackground", palette.accent)
    root.option_add("*TCombobox*Listbox.selectForeground", palette.accent_text)
    return style


def _configure_fonts(_root: tk.Misc) -> None:
    try:
        heading = tkfont.nametofont("TkHeadingFont")
        heading.configure(size=18, weight="bold")
        body = tkfont.nametofont("TkDefaultFont")
        body.configure(size=10)
    except tk.TclError:
        return


def _windows_appearance() -> Appearance:
    try:
        import winreg
    except ImportError:
        return "light"
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    except OSError:
        return "light"
    return "light" if int(value) else "dark"


def _macos_appearance() -> Appearance:
    completed = _run_probe(["defaults", "read", "-g", "AppleInterfaceStyle"])
    if completed is None:
        return "light"
    if completed.returncode == 0 and completed.stdout.strip().lower() == "dark":
        return "dark"
    return "light"


def _linux_appearance() -> Appearance:
    gtk_theme = os.environ.get("GTK_THEME", "")
    if "dark" in gtk_theme.lower():
        return "dark"
    completed = _run_probe(
        ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"]
    )
    if completed is not None and completed.returncode == 0:
        value = completed.stdout.strip().strip("'\"").lower()
        if "dark" in value:
            return "dark"
        return "light"
    return "light"


_ALLOWED_PROBES = frozenset({"defaults", "gsettings"})


def _run_probe(command: list[str]) -> subprocess.CompletedProcess[str] | None:
    if not command or command[0] not in _ALLOWED_PROBES:
        return None
    try:
        return subprocess.run(  # noqa: S603 - argv is a fixed OS appearance probe
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
