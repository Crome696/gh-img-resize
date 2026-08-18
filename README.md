# gh-img-resize

Desktop tool that turns an image into a file of **exactly 999 KB** (999,000 bytes) for GitHub uploads such as repository social previews. The original file format and aspect ratio are kept.

GitHub asks for PNG, JPG, or GIF files **under 1 MB** and treats 1 MB as **1,000,000 bytes**. Using 999 KiB (999 × 1024 = 1,022,976 bytes) exceeds that cap and is rejected. This tool therefore uses decimal kilobytes: 999 × 1000 = 999,000 bytes.

Builds are produced **on the target OS** (Windows EXE, macOS `.app`, Linux binary). There is no cross-compile and no Electron wrapper.

## Use the desktop app

1. Build locally for your OS, or download the matching CI artifact (`gh-img-resize.exe`, `gh-img-resize.app.zip`, or `gh-img-resize`).
2. Start the app.
3. Choose an image (JPEG, PNG, GIF, or WebP).
4. Save the result. The suggested name is `{original}-999kb.{ext}`.

The saved file is always exactly 999,000 bytes.

Unsigned Windows and macOS builds may show SmartScreen or Gatekeeper warnings.

## Run from source

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe run.py
```

macOS and Linux (install Tk on Ubuntu first: `sudo apt-get install -y python3-tk tcl-dev tk-dev`):

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PYTHONPATH=src .venv/bin/python run.py
```

## How sizing works

- Files already under 999 KB are padded with format-native metadata (JPEG COM, PNG `tEXt`, GIF comment, WebP `META` chunk). Quality is not reduced.
- Larger JPEG/WebP files first search the highest quality that fits, then reduce pixel dimensions with LANCZOS if needed.
- PNG and GIF only reduce pixel dimensions (lossless formats). Aspect ratio is preserved.
- EXIF orientation is applied before re-encoding.
- Animated GIFs are saved as a still image of the first frame.

## Lint, format, and security

Install development tools with `pip install -r requirements-dev.txt` (after the runtime requirements above).

Windows:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests run.py
.\.venv\Scripts\python.exe -m ruff format --check src tests run.py
.\.venv\Scripts\python.exe -m ruff format src tests run.py
.\.venv\Scripts\python.exe -m pip_audit -r requirements.txt
```

macOS and Linux:

```bash
.venv/bin/python -m ruff check src tests run.py
.venv/bin/python -m ruff format --check src tests run.py
.venv/bin/python -m ruff format src tests run.py
.venv/bin/python -m pip_audit -r requirements.txt
```

GitHub Actions workflows `.github/workflows/quality.yml` and `.github/workflows/security.yml` run these gates on pull requests. Quality runs Ruff and `pip-audit`. Security runs Gitleaks and Trivy.

## Tests

Windows:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

macOS and Linux:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

## Build desktop binaries

PyInstaller reads the committed [gh-img-resize.spec](gh-img-resize.spec). Run the build **on the OS you want to ship**; Windows cannot produce a macOS app or Linux binary.

Windows:

```powershell
.\build.ps1
```

Writes `dist\gh-img-resize.exe`.

macOS and Linux:

```bash
bash build.sh
```

Writes `dist/gh-img-resize.app` on macOS and `dist/gh-img-resize` on Linux.

GitHub Actions workflow `.github/workflows/build.yml` runs tests and native builds on `windows-latest`, `macos-latest`, and `ubuntu-latest`, then uploads those three artifacts.
