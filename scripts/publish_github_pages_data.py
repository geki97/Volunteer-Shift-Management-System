#!/usr/bin/env python
"""
Publish AppFlowy export JSON files into the GitHub Pages (docs/) folder.

GitHub Pages is static, so the frontend must read data from docs/appflowy_exports/.
This script copies the latest exports from APPFLOWY_EXPORT_PATH into docs/.

Usage:
  python scripts/publish_github_pages_data.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import APPFLOWY_EXPORT_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_EXPORT_DIR = PROJECT_ROOT / "docs" / "appflowy_exports"


def _copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    src_dir = Path(APPFLOWY_EXPORT_PATH)
    if not src_dir.exists():
        print(f"[ERROR] Export folder not found: {src_dir}")
        return 2

    PAGES_EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    files = ["volunteers.json", "shifts.json"]
    missing = []
    for name in files:
        src = src_dir / name
        if not src.exists():
            missing.append(str(src))
            continue
        _copy(src, PAGES_EXPORT_DIR / name)

    if missing:
        print("[ERROR] Missing export files:")
        for m in missing:
            print(f"  - {m}")
        return 2

    print("[OK] Published GitHub Pages data:")
    for name in files:
        dst = PAGES_EXPORT_DIR / name
        print(f"  - {dst} ({dst.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
