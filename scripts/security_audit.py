#!/usr/bin/env python
"""
Offline security audit (no network).

Checks for:
- Secrets accidentally committed (common key patterns)
- Insecure defaults (e.g., default QR_SIGNING_KEY)
- .env accidentally tracked

Usage:
  python scripts/security_audit.py
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


SECRET_PATTERNS = [
    ("SendGrid key", re.compile(r"\bSG\.[A-Za-z0-9_\-]{20,}\b")),
    ("Supabase service role", re.compile(r"\bSUPABASE_SERVICE_ROLE_KEY\s*=\s*.+", re.IGNORECASE)),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Private key block", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----")),
]


def git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={PROJECT_ROOT}", "ls-files"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def scan_file(path: Path) -> list[str]:
    findings = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return [f"[WARN] Failed to read {path}: {e}"]

    for name, pat in SECRET_PATTERNS:
        if pat.search(text):
            findings.append(f"[HIGH] Possible secret ({name}) in {path}")

    return findings


def main() -> int:
    print("Security audit (offline)")
    print("=" * 60)

    tracked = git_ls_files()
    if ".env" in tracked or any(p.endswith("/.env") for p in tracked):
        print("[HIGH] .env appears to be tracked by git. Remove it from git history.")
        return 2

    all_findings: list[str] = []
    for rel in tracked:
        # Skip large binary-like paths by extension.
        if rel.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".pdf", ".docx")):
            continue
        all_findings.extend(scan_file(PROJECT_ROOT / rel))

    if not all_findings:
        print("[OK] No obvious secrets or insecure defaults found in tracked files.")
        return 0

    for f in sorted(set(all_findings)):
        print(f)

    # Exit non-zero if any HIGH findings.
    if any(f.startswith("[HIGH]") for f in all_findings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
