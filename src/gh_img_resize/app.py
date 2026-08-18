"""Localized desktop UI for resizing an image to exactly 999 KB."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from gh_img_resize.i18n import (
    detect_os_language,
    language_from_switcher,
    load_saved_language,
    resolve_language,
    save_language,
    switcher_codes,
    switcher_from_language,
    translate,
)
from gh_img_resize.resizer import (
    SUPPORTED_EXTENSIONS,
    TARGET_BYTES,
    ResizeError,
    ResizeResult,
    resize_to_target,
)
from gh_img_resize.theme import apply_theme, detect_system_appearance, palette_for


class ImageResizeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.minsize(600, 640)
        self.geometry("640x720")
        self.source_path: Path | None = None
        self.preview_image: ImageTk.PhotoImage | None = None
        self._busy = False
        self._image_meta: tuple[str, int, int] | None = None
        self._last_result: ResizeResult | None = None
        self._last_dest: Path | None = None
        self._status_kind = ""
        self._progress_key: str | None = None
        self._error_text = ""
        self.language = resolve_language(load_saved_language(), detect_os_language())
        self.palette = palette_for(detect_system_appearance())
        apply_theme(self, self.palette)
        self._build()
        self._apply_strings()

    def _t(self, key: str, **params: object) -> str:
        return translate(self.language, key, **params)

    def _file_types(self) -> list[tuple[str, str]]:
        return [
            (self._t("dialog.images"), "*.jpg *.jpeg *.png *.gif *.webp"),
            (self._t("dialog.jpeg"), "*.jpg *.jpeg"),
            (self._t("dialog.png"), "*.png"),
            (self._t("dialog.gif"), "*.gif"),
            (self._t("dialog.webp"), "*.webp"),
            (self._t("dialog.all_files"), "*.*"),
        ]

    def _build(self) -> None:
        root = ttk.Frame(self, style="Canvas.TFrame", padding=24)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root, style="Canvas.TFrame")
        header.pack(fill=tk.X, pady=(0, 20))
        titles = ttk.Frame(header, style="Canvas.TFrame")
        titles.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.title_label = ttk.Label(titles, style="Title.TLabel")
        self.title_label.pack(anchor=tk.W)
        self.subtitle_label = ttk.Label(
            titles,
            style="Subtitle.TLabel",
            justify=tk.LEFT,
        )
        self.subtitle_label.pack(anchor=tk.W, pady=(8, 0))

        lang_block = ttk.Frame(header, style="Canvas.TFrame")
        lang_block.pack(side=tk.RIGHT, anchor=tk.N, padx=(16, 0))
        self.language_label = ttk.Label(lang_block, style="Subtitle.TLabel")
        self.language_label.pack(anchor=tk.E)
        self.language_var = tk.StringVar(value=switcher_from_language(self.language))
        self.language_combo = ttk.Combobox(
            lang_block,
            textvariable=self.language_var,
            values=switcher_codes(),
            state="readonly",
            width=8,
        )
        self.language_combo.pack(anchor=tk.E, pady=(4, 0))
        self.language_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        buttons = ttk.Frame(root, style="Canvas.TFrame")
        buttons.pack(fill=tk.X, pady=(0, 16))
        self.choose_button = ttk.Button(
            buttons,
            command=self._choose_image,
            style="Secondary.TButton",
        )
        self.choose_button.pack(side=tk.LEFT)
        self.save_button = ttk.Button(
            buttons,
            command=self._save_image,
            state=tk.DISABLED,
            style="Accent.TButton",
        )
        self.save_button.pack(side=tk.LEFT, padx=(12, 0))

        preview_card = ttk.Frame(root, style="Card.TFrame", padding=16)
        preview_card.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        self.preview_label = ttk.Label(
            preview_card,
            style="Preview.TLabel",
            anchor=tk.CENTER,
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        meta_card = ttk.Frame(root, style="Card.TFrame", padding=16)
        meta_card.pack(fill=tk.X)
        self.info_var = tk.StringVar()
        ttk.Label(
            meta_card,
            textvariable=self.info_var,
            style="Body.TLabel",
            justify=tk.LEFT,
        ).pack(anchor=tk.W, fill=tk.X)
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(
            meta_card,
            textvariable=self.status_var,
            style="Muted.TLabel",
            justify=tk.LEFT,
        )
        self.status_label.pack(anchor=tk.W, fill=tk.X, pady=(8, 0))

    def _apply_strings(self) -> None:
        self.title(self._t("window.title"))
        self.title_label.configure(text=self._t("header.title"))
        self.subtitle_label.configure(text=self._t("header.subtitle"))
        self.language_label.configure(text=self._t("language.label"))
        self.choose_button.configure(text=self._t("button.choose"))
        self.save_button.configure(text=self._t("button.save"))
        if self.preview_image is None:
            self.preview_label.configure(text=self._t("preview.empty"))
        self._refresh_info()
        self._refresh_status()

    def _refresh_info(self) -> None:
        if self._last_result is not None and self._last_dest is not None:
            self.info_var.set(
                self._t(
                    "info.saved_file",
                    path=self._last_dest,
                    size=self._last_result.size,
                    width=self._last_result.width,
                    height=self._last_result.height,
                )
            )
            return
        if self.source_path is not None and self._image_meta is not None:
            fmt, width, height = self._image_meta
            size = self.source_path.stat().st_size
            self.info_var.set(
                self._t(
                    "info.selected",
                    name=self.source_path.name,
                    fmt=fmt,
                    width=width,
                    height=height,
                    bytes=size,
                    kb=size / 1000,
                    target=TARGET_BYTES,
                )
            )
            return
        self.info_var.set(self._t("info.choose_prompt"))

    def _refresh_status(self) -> None:
        if self._status_kind == "ready":
            self._set_status(self._t("status.ready"))
        elif self._status_kind == "progress":
            self._set_status(self._t(self._progress_key or "progress.resizing"))
        elif self._status_kind == "success" and self._last_result is not None:
            self._set_status(self._success_details(self._last_result, self._last_dest))
        elif self._status_kind == "error":
            self._set_status(
                self._t("status.error", message=self._error_text), error=True
            )
        else:
            self._set_status("")

    def _on_language_selected(self, _event: object | None = None) -> None:
        selected = language_from_switcher(self.language_var.get())
        if selected is None or selected == self.language:
            return
        self.language = selected
        save_language(selected)
        self._apply_strings()

    def _set_status(self, message: str, *, error: bool = False) -> None:
        self.status_var.set(message)
        self.status_label.configure(style="Error.TLabel" if error else "Muted.TLabel")

    def _choose_image(self) -> None:
        if self._busy:
            return
        selected = filedialog.askopenfilename(parent=self, filetypes=self._file_types())
        if not selected:
            return
        path = Path(selected)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            messagebox.showerror(
                self._t("error.unsupported_format_title"),
                self._t("error.unsupported_format_body"),
                parent=self,
            )
            return
        try:
            with Image.open(path) as image:
                width, height = image.size
                fmt = image.format or path.suffix.upper().lstrip(".")
                preview = image.copy()
            preview.thumbnail((460, 300))
            if preview.mode not in {"RGB", "RGBA", "L"}:
                preview = preview.convert("RGB")
            self.preview_image = ImageTk.PhotoImage(preview)
        except OSError as exc:
            messagebox.showerror(
                self._t("error.load_failed_title"), str(exc), parent=self
            )
            return

        self.source_path = path
        self._image_meta = (fmt, width, height)
        self._last_result = None
        self._last_dest = None
        self._status_kind = "ready"
        self._progress_key = None
        self._error_text = ""
        self.preview_label.configure(image=self.preview_image, text="")
        self._refresh_info()
        self._refresh_status()
        self.save_button.configure(state=tk.NORMAL)

    def _save_image(self) -> None:
        if self._busy or self.source_path is None:
            return
        source = self.source_path
        suggested = f"{source.stem}-999kb{source.suffix.lower()}"
        destination = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=source.suffix.lower(),
            initialfile=suggested,
            filetypes=self._file_types(),
        )
        if not destination:
            return

        dest_path = Path(destination)
        self._set_busy(True)
        self._status_kind = "progress"
        self._progress_key = "progress.resizing"
        self._refresh_status()

        def work() -> None:
            try:
                result = resize_to_target(source, progress=self._report_progress)
                dest_path.write_bytes(result.data)
            except Exception as exc:  # noqa: BLE001 - show any failure in the UI
                self.after(0, lambda error=exc: self._on_failure(error))
                return
            self.after(0, lambda: self._on_success(result, dest_path))

        threading.Thread(target=work, daemon=True).start()

    def _report_progress(self, message: str) -> None:
        self.after(0, lambda: self._on_progress(message))

    def _on_progress(self, key: str) -> None:
        self._status_kind = "progress"
        self._progress_key = key
        self._refresh_status()

    def _success_details(self, result: ResizeResult, dest_path: Path | None) -> str:
        name = dest_path.name if dest_path is not None else ""
        details = [
            self._t("success.saved", name=name),
            self._t("success.result", size=result.size),
            self._t("success.dimensions", width=result.width, height=result.height),
            self._t("success.format", fmt=result.format),
        ]
        if result.scaled:
            details.append(self._t("success.scaled"))
        if result.padded and not result.reencoded:
            details.append(self._t("success.padded"))
        return "\n".join(details)

    def _on_success(self, result: ResizeResult, dest_path: Path) -> None:
        self._set_busy(False)
        self._last_result = result
        self._last_dest = dest_path
        self._status_kind = "success"
        self._progress_key = None
        self._error_text = ""
        self._refresh_info()
        self._refresh_status()
        messagebox.showinfo(
            self._t("dialog.done_title"),
            self._t("dialog.done_body", size=result.size),
            parent=self,
        )

    def _exception_text(self, exc: Exception) -> str:
        if isinstance(exc, ResizeError):
            return self._t(exc.key, **exc.params)
        return str(exc) if str(exc) else exc.__class__.__name__

    def _on_failure(self, exc: Exception) -> None:
        self._set_busy(False)
        message = self._exception_text(exc)
        self._error_text = message
        self._status_kind = "error"
        self._progress_key = None
        self._refresh_status()
        title_key = (
            "error.cannot_fit_title"
            if isinstance(exc, ResizeError)
            else "error.resize_failed_title"
        )
        messagebox.showerror(self._t(title_key), message, parent=self)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.save_button.configure(state=state if self.source_path else tk.DISABLED)
        self.language_combo.configure(state="disabled" if busy else "readonly")


def main() -> None:
    app = ImageResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
