# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-18

### Added

- Desktop Tkinter app that writes JPEG, PNG, GIF, and WebP files at exactly 999,000 bytes while keeping format and aspect ratio.
- Padding for files already under 999 KB using format-native metadata (JPEG COM, PNG `tEXt`, GIF comment, WebP `META`).
- Quality search plus LANCZOS downscale for larger JPEG/WebP files, and lossless downscale for PNG and GIF.
- Native PyInstaller builds for Windows, macOS, and Linux, produced on the target OS.
- GitHub Actions workflows for tests and native artifacts, Ruff lint/format, pip-audit, Gitleaks, and Trivy.
- README banner, architecture overview, and local run, test, lint, and build commands.

[1.0.0]: https://github.com/Crome696/gh-img-resize/releases/tag/v1.0.0
