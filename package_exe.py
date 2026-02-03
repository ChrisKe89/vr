#!/usr/bin/env python3
"""Helper script that packages VR Training Server Helper into a standalone EXE."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SPEC_FILE = ROOT / "webx_app.spec"
DIST_DIR = ROOT / "dist"
EXE_NAME = "webx_app"


def ensure_pyinstaller_installed() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller is not installed; installing now.")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "pyinstaller"],
            check=True,
        )


def build_executable() -> None:
    if not SPEC_FILE.exists():
        raise FileNotFoundError(f"{SPEC_FILE} not found.")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--log-level",
        "WARN",
        str(SPEC_FILE.name),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)


def find_built_executable() -> Path | None:
    candidates = [
        DIST_DIR / EXE_NAME / f"{EXE_NAME}.exe",
        DIST_DIR / f"{EXE_NAME}.exe",
        DIST_DIR / EXE_NAME / EXE_NAME,
        DIST_DIR / EXE_NAME,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    if not DIST_DIR.exists():
        return None
    for item in DIST_DIR.rglob("*"):
        if item.is_file() and item.name.lower() == f"{EXE_NAME}.exe":
            return item
    return None


def main() -> None:
    ensure_pyinstaller_installed()
    build_executable()
    exe_path = find_built_executable()
    if exe_path:
        print(f"EXE ready: {exe_path}")
        return
    raise RuntimeError(
        "Packaging completed but EXE not found. "
        "Check the dist/ folder for output."
    )


if __name__ == "__main__":
    main()
