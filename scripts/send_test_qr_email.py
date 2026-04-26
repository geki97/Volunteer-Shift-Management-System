#!/usr/bin/env python
"""
Send a single test reminder email with a QR code.

This is a developer smoke-test for the end-to-end flow:
exports -> QR generation -> email content -> email send (or dry-run output).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import APPFLOWY_EXPORT_PATH, APP_BASE_URL, is_placeholder_value
from scripts.security.qr_secure import SecureQRCode
from scripts.utils.email_service_enhanced import (
    create_shift_reminder_email_with_qr,
    send_email_with_qr_attachment,
)


def _load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Send a test shift reminder email with QR code.")
    parser.add_argument("--to", dest="to_email", required=False, help="Recipient email address")
    parser.add_argument("--shift-id", dest="shift_id", required=False, help="Shift id (defaults to first shift)")
    parser.add_argument("--volunteer-id", dest="volunteer_id", required=False, help="Volunteer id (defaults to first assigned)")
    parser.add_argument("--dry-run", action="store_true", help="Write output to outbox/ instead of sending")
    args = parser.parse_args(argv)

    shifts_file = Path(APPFLOWY_EXPORT_PATH) / "shifts.json"
    volunteers_file = Path(APPFLOWY_EXPORT_PATH) / "volunteers.json"
    if not shifts_file.exists():
        print(f"[ERROR] Missing shifts export: {shifts_file}")
        return 2
    if not volunteers_file.exists():
        print(f"[ERROR] Missing volunteers export: {volunteers_file}")
        return 2

    shifts = _load_json(shifts_file)
    volunteers = _load_json(volunteers_file)
    volunteer_lookup = {str(v.get("id")): v for v in volunteers if v.get("id")}

    if not shifts:
        print("[ERROR] shifts.json is empty")
        return 2

    shift = None
    if args.shift_id:
        for s in shifts:
            if str(s.get("id")) == str(args.shift_id):
                shift = s
                break
        if not shift:
            print(f"[ERROR] Shift not found: {args.shift_id}")
            return 2
    else:
        shift = shifts[0]

    shift_id = str(shift.get("id"))
    shift_name = shift.get("shift_name", "Shift")
    shift_date_raw = shift.get("shift_date", "")
    shift_date = shift_date_raw.split("T")[0] if "T" in shift_date_raw else shift_date_raw
    shift_time = shift_date_raw.split("T")[1][:5] if "T" in shift_date_raw else "Unknown"
    location = shift.get("location", "TBD")

    assigned = shift.get("assigned_volunteers", []) or []
    volunteer_id = args.volunteer_id or (assigned[0] if assigned else None)
    if not volunteer_id:
        print("[ERROR] No volunteer_id provided and shift has no assigned_volunteers")
        return 2

    volunteer = volunteer_lookup.get(str(volunteer_id), {})
    volunteer_name = volunteer.get("name") or str(volunteer_id)
    volunteer_email = args.to_email or volunteer.get("email")

    if not args.dry_run and not volunteer_email:
        print("[ERROR] No recipient email. Provide --to or ensure volunteer has an email in volunteers.json.")
        return 2

    # Generate QR code (token points to /check-in/token/<token>)
    qr_path, token = SecureQRCode.generate_shift_qr_code(
        shift_id=shift_id,
        shift_name=shift_name,
        user_id=str(volunteer_id),
        expiry_hours=25,
        app_base_url=APP_BASE_URL,
    )
    if not qr_path:
        print(f"[ERROR] Failed to generate QR code: {token}")
        return 2

    check_in_url = f"{APP_BASE_URL}/check-in/token/{token}"

    html_content, text_content, _ = create_shift_reminder_email_with_qr(
        volunteer_name=volunteer_name,
        shift_name=shift_name,
        shift_date=shift_date,
        shift_time=shift_time,
        location=location,
        qr_code_path=qr_path,
        special_instructions=shift.get("special_instructions") or None,
    )

    if args.dry_run:
        outbox = Path("outbox")
        outbox.mkdir(parents=True, exist_ok=True)
        html_path = outbox / "test_qr_email.html"
        with open(html_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html_content)
        print("[OK] Dry-run email written:")
        print(f"  HTML: {html_path.resolve()}")
        print(f"  QR:   {Path(qr_path).resolve()}")
        print(f"  URL:  {check_in_url}")
        return 0

    # Heuristic guardrail: refuse to send if config still looks like template placeholders.
    from config import settings as settings_module

    provider = (settings_module.EMAIL_PROVIDER or "").strip().lower()
    if provider == "sendgrid":
        if is_placeholder_value(settings_module.SENDGRID_API_KEY) or is_placeholder_value(
            settings_module.SENDGRID_FROM_EMAIL
        ):
            print("[ERROR] SendGrid credentials look like placeholders in .env. Update .env before sending.")
            print("Run with --dry-run to generate the QR + email preview without sending.")
            return 2
    elif provider == "gmail":
        if is_placeholder_value(settings_module.GMAIL_USER) or is_placeholder_value(settings_module.GMAIL_APP_PASSWORD):
            print("[ERROR] Gmail credentials look like placeholders in .env. Update .env before sending.")
            print("Run with --dry-run to generate the QR + email preview without sending.")
            return 2
    else:
        print(f"[ERROR] Unknown EMAIL_PROVIDER: {settings_module.EMAIL_PROVIDER!r}")
        return 2

    success, message_id = send_email_with_qr_attachment(
        to_email=volunteer_email,
        subject=f"Test QR Check-In: {shift_name}",
        html_content=html_content,
        qr_code_path=qr_path,
        text_content=text_content,
    )

    if success:
        print("[OK] Email sent.")
        print(f"  To:  {volunteer_email}")
        print(f"  QR:  {Path(qr_path).resolve()}")
        print(f"  URL: {check_in_url}")
        print(f"  Provider Message ID: {message_id}")
        return 0

    print("[ERROR] Email send failed:")
    print(f"  {message_id}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
