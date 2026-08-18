"""German desktop UI for resizing an image to exactly 999 KB."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from gh_img_resize.resizer import (
    SUPPORTED_EXTENSIONS,
    TARGET_BYTES,
    ResizeError,
    ResizeResult,
    resize_to_target,
)

FILE_TYPES = [
    (
        "Bilder",
        "*.jpg *.jpeg *.png *.gif *.webp",
    ),
    ("JPEG", "*.jpg *.jpeg"),
    ("PNG", "*.png"),
    ("GIF", "*.gif"),
    ("WebP", "*.webp"),
    ("Alle Dateien", "*.*"),
]


class ImageResizeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("GitHub Bild auf 999 KB")
        self.minsize(520, 520)
        self.geometry("560x620")
        self.source_path: Path | None = None
        self.preview_image: ImageTk.PhotoImage | None = None
        self._busy = False
        self._build()

    def _build(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            root,
            text="Bild wählen. Seitenverhältnis und Format bleiben erhalten.\n"
            "Die gespeicherte Datei ist genau 999 KB (999.000 Bytes),\n"
            "unter GitHubs 1-MB-Limit (1.000.000 Bytes).",
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

        buttons = ttk.Frame(root)
        buttons.pack(fill=tk.X, pady=(12, 8))
        ttk.Button(buttons, text="Bild auswählen…", command=self._choose_image).pack(
            side=tk.LEFT
        )
        self.save_button = ttk.Button(
            buttons,
            text="Als 999 KB speichern…",
            command=self._save_image,
            state=tk.DISABLED,
        )
        self.save_button.pack(side=tk.LEFT, padx=(8, 0))

        self.preview_label = ttk.Label(
            root,
            text="Noch kein Bild gewählt",
            anchor=tk.CENTER,
            relief=tk.SOLID,
            padding=8,
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True, pady=(8, 8))

        self.info_var = tk.StringVar(value="Bitte ein Bild auswählen.")
        ttk.Label(root, textvariable=self.info_var, justify=tk.LEFT).pack(
            anchor=tk.W, fill=tk.X
        )

        self.status_var = tk.StringVar(value="")
        ttk.Label(root, textvariable=self.status_var, foreground="#444").pack(
            anchor=tk.W, pady=(8, 0)
        )

    def _choose_image(self) -> None:
        if self._busy:
            return
        selected = filedialog.askopenfilename(parent=self, filetypes=FILE_TYPES)
        if not selected:
            return
        path = Path(selected)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            messagebox.showerror(
                "Nicht unterstütztes Format",
                "Bitte JPEG, PNG, GIF oder WebP wählen.",
                parent=self,
            )
            return
        try:
            with Image.open(path) as image:
                width, height = image.size
                fmt = image.format or path.suffix.upper().lstrip(".")
                preview = image.copy()
            preview.thumbnail((420, 280))
            if preview.mode not in {"RGB", "RGBA", "L"}:
                preview = preview.convert("RGB")
            self.preview_image = ImageTk.PhotoImage(preview)
        except OSError as exc:
            messagebox.showerror(
                "Bild konnte nicht geladen werden", str(exc), parent=self
            )
            return

        self.source_path = path
        self.preview_label.configure(image=self.preview_image, text="")
        size = path.stat().st_size
        self.info_var.set(
            f"Datei: {path.name}\n"
            f"Format: {fmt}  |  Maße: {width} × {height} px\n"
            f"Aktuelle Größe: {size:,} Bytes ({size / 1000:.1f} KB)\n"
            f"Zielgröße: {TARGET_BYTES:,} Bytes (999 KB, unter 1.000.000 Bytes)"
        )
        self.status_var.set("Bereit zum Speichern.")
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
            filetypes=FILE_TYPES,
        )
        if not destination:
            return

        dest_path = Path(destination)
        self._set_busy(True)
        self.status_var.set("Datei wird angepasst…")

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
        self.after(0, lambda: self.status_var.set(message))

    def _on_success(self, result: ResizeResult, dest_path: Path) -> None:
        self._set_busy(False)
        details = [
            f"Gespeichert: {dest_path.name}",
            f"Ergebnis: {result.size:,} Bytes (999 KB)",
            f"Maße: {result.width} × {result.height} px",
            f"Format: {result.format}",
        ]
        if result.scaled:
            details.append(
                "Die Auflösung wurde bei gleichem Seitenverhältnis reduziert."
            )
        if result.padded and not result.reencoded:
            details.append(
                "Die Originaldatei war kleiner als 999 KB und wurde nur aufgefüllt."
            )
        self.status_var.set("\n".join(details))
        self.info_var.set(
            f"Gespeicherte Datei: {dest_path}\n"
            f"Größe: {result.size:,} Bytes\n"
            f"Maße: {result.width} × {result.height} px"
        )
        messagebox.showinfo(
            "Fertig", f"Die Datei ist genau {result.size:,} Bytes groß.", parent=self
        )

    def _on_failure(self, exc: Exception) -> None:
        self._set_busy(False)
        message = str(exc) if str(exc) else exc.__class__.__name__
        self.status_var.set(f"Fehler: {message}")
        title = "Anpassung fehlgeschlagen"
        if isinstance(exc, ResizeError):
            title = "Bild konnte nicht auf 999 KB gebracht werden"
        messagebox.showerror(title, message, parent=self)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.save_button.configure(state=state if self.source_path else tk.DISABLED)


def main() -> None:
    app = ImageResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
