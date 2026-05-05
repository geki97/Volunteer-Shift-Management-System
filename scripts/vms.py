#!/usr/bin/env python
"""
Volunteer Management System - CLI

Keeps the repo tidy by providing one main entrypoint for common tasks:
- Convert AppFlowy CSV exports to JSON
- Publish JSON into docs/ for GitHub Pages
- Generate QR codes for shifts (QR links open GitHub Pages check-in)

Examples:
  python scripts/vms.py convert
  python scripts/vms.py publish-pages
  python scripts/vms.py publish-pages --convert-first
  python scripts/vms.py generate-qrs
  python scripts/vms.py send-email --dry-run --to you@example.com
  python scripts/vms.py test-sendgrid --to you@example.com
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import APPFLOWY_EXPORT_PATH, APP_BASE_URL
from scripts.csv_to_json_converter import convert_appflowy_exports
from scripts.publish_github_pages_data import main as publish_pages_main
from scripts.security.qr_secure import SecureQRCode
from scripts.utils.email_service_enhanced import (
    create_shift_reminder_email_with_qr,
    send_email_with_qr_attachment,
)

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except Exception:
    SENDGRID_AVAILABLE = False


def _load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def cmd_convert(_: argparse.Namespace) -> int:
    convert_appflowy_exports()
    return 0


def cmd_publish_pages(args: argparse.Namespace) -> int:
    if args.convert_first:
        convert_appflowy_exports()
    return int(publish_pages_main())


def cmd_generate_qrs(args: argparse.Namespace) -> int:
    export_dir = Path(APPFLOWY_EXPORT_PATH)
    shifts_file = export_dir / "shifts.json"
    if not shifts_file.exists():
        print(f"[ERROR] Missing shifts export: {shifts_file}")
        return 2

    shifts = _load_json(shifts_file) or []
    if not shifts:
        print("[ERROR] shifts.json is empty")
        return 2

    base_url = (APP_BASE_URL or "").strip().rstrip("/")
    if not base_url:
        print("[WARN] APP_BASE_URL is empty; QR codes will use a relative URL (check-in.html?token=...).")
        print("       For GitHub Pages, set APP_BASE_URL in .env to:")
        print("       https://geki97.github.io/Volunteer-Shift-Management-System\n")

    limit = args.limit if args.limit and args.limit > 0 else None
    count = 0
    for shift in shifts[:limit] if limit else shifts:
        shift_id = shift.get("id")
        shift_name = shift.get("shift_name") or str(shift_id or "shift")
        if not shift_id:
            continue

        qr_path, token = SecureQRCode.generate_shift_qr_code(
            shift_id=str(shift_id),
            shift_name=str(shift_name),
            app_base_url=base_url if base_url else None,
        )
        if not qr_path:
            print(f"[WARN] Failed to generate QR for shift {shift_id}: {token}")
            continue
        count += 1

    print(f"[OK] Generated {count} QR codes.")
    return 0


def cmd_test_sendgrid(args: argparse.Namespace) -> int:
    from config.settings import SENDGRID_API_KEY, SENDGRID_FROM_EMAIL, is_placeholder_value

    if not SENDGRID_AVAILABLE:
        print("[ERROR] sendgrid package not installed. Install dependencies from requirements.txt.")
        return 2

    if is_placeholder_value(SENDGRID_API_KEY):
        print("[ERROR] SENDGRID_API_KEY appears to be a placeholder in .env")
        return 2

    if is_placeholder_value(SENDGRID_FROM_EMAIL):
        print("[ERROR] SENDGRID_FROM_EMAIL appears to be a placeholder in .env")
        return 2

    to_email = args.to_email or SENDGRID_FROM_EMAIL
    if not to_email:
        print("[ERROR] Missing recipient email (use --to)")
        return 2

    try:
        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject="Volunteer Management System - SendGrid Connectivity Test",
            html_content="""
            <html><body style="font-family: Arial, sans-serif;">
              <h2>SendGrid Connection Test</h2>
              <p>If you received this email, your SendGrid API key is working.</p>
            </body></html>
            """,
        )
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        resp = sg.send(message)
        if resp.status_code in (200, 201, 202):
            print("[OK] SendGrid connection test successful.")
            print(f"  Status: {resp.status_code}")
            return 0
        print(f"[ERROR] SendGrid returned status {resp.status_code}")
        return 1
    except Exception as e:
        print("[ERROR] SendGrid connectivity test failed:")
        print(f"  {type(e).__name__}: {e}")
        return 1


def cmd_send_email(args: argparse.Namespace) -> int:
    from config import settings as settings_module
    from config.settings import is_placeholder_value

    export_dir = Path(APPFLOWY_EXPORT_PATH)
    shifts_file = export_dir / "shifts.json"
    volunteers_file = export_dir / "volunteers.json"
    if not shifts_file.exists() or not volunteers_file.exists():
        print("[ERROR] Missing exports. Ensure appflowy_exports/shifts.json and appflowy_exports/volunteers.json exist.")
        return 2

    shifts = _load_json(shifts_file) or []
    volunteers = _load_json(volunteers_file) or []
    if not shifts:
        print("[ERROR] shifts.json is empty")
        return 2

    volunteer_lookup = {str(v.get("id")): v for v in volunteers if v.get("id")}

    # Select shift
    shift = None
    if args.shift_id:
        shift = next((s for s in shifts if str(s.get("id")) == str(args.shift_id)), None)
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
    recipient = args.to_email or volunteer.get("email")

    if not args.dry_run and not recipient:
        print("[ERROR] No recipient email. Provide --to or ensure volunteer has an email in volunteers.json.")
        return 2

    base_url = (APP_BASE_URL or "").strip().rstrip("/")
    token_qr_path, token = SecureQRCode.generate_shift_qr_code(
        shift_id=shift_id,
        shift_name=shift_name,
        user_id=str(volunteer_id),
        expiry_hours=25,
        app_base_url=base_url if base_url else None,
    )
    if not token_qr_path:
        print(f"[ERROR] Failed to generate QR code: {token}")
        return 2

    token_q = urllib.parse.quote(token, safe="")
    check_in_url = f"{base_url}/check-in.html?token={token_q}" if base_url else f"check-in.html?token={token_q}"

    html_content, text_content, _ = create_shift_reminder_email_with_qr(
        volunteer_name=volunteer_name,
        shift_name=shift_name,
        shift_date=shift_date,
        shift_time=shift_time,
        location=location,
        qr_code_path=token_qr_path,
        special_instructions=shift.get("special_instructions") or None,
    )

    if args.dry_run:
        outbox = Path("outbox")
        outbox.mkdir(parents=True, exist_ok=True)
        html_path = outbox / "test_qr_email.html"
        with open(html_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html_content)
        print("[OK] Dry-run email preview generated:")
        print(f"  HTML: {html_path.resolve()}")
        print(f"  QR:   {Path(token_qr_path).resolve()}")
        print(f"  URL:  {check_in_url}")
        return 0

    if not base_url or not (base_url.startswith("http://") or base_url.startswith("https://")):
        print("[ERROR] APP_BASE_URL must be set to an absolute URL for a real send.")
        print("Set APP_BASE_URL in .env to:")
        print("  https://geki97.github.io/Volunteer-Shift-Management-System")
        return 2

    provider = (settings_module.EMAIL_PROVIDER or "").strip().lower()
    if provider == "sendgrid":
        if is_placeholder_value(settings_module.SENDGRID_API_KEY) or is_placeholder_value(settings_module.SENDGRID_FROM_EMAIL):
            print("[ERROR] SendGrid credentials look like placeholders in .env.")
            return 2
    elif provider == "gmail":
        if is_placeholder_value(settings_module.GMAIL_USER) or is_placeholder_value(settings_module.GMAIL_APP_PASSWORD):
            print("[ERROR] Gmail credentials look like placeholders in .env.")
            return 2
    else:
        print(f"[ERROR] Unknown EMAIL_PROVIDER: {settings_module.EMAIL_PROVIDER!r}")
        return 2

    print(f"[*] Sending email via {provider}...")
    ok, msg = send_email_with_qr_attachment(
        to_email=recipient,
        subject=f"Shift Reminder: {shift_name}",
        html_content=html_content,
        qr_code_path=token_qr_path,
        text_content=text_content,
    )
    if ok:
        print("[OK] Email sent.")
        print(f"  To: {recipient}")
        print(f"  URL: {check_in_url}")
        print(f"  Provider message id: {msg}")
        return 0
    print("[ERROR] Email send failed:")
    print(f"  {msg}")
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="vms", description="Volunteer Management System CLI")
    sub = p.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="Convert AppFlowy CSV exports to JSON")
    p_convert.set_defaults(func=cmd_convert)

    p_publish = sub.add_parser("publish-pages", help="Copy JSON exports into docs/appflowy_exports for GitHub Pages")
    p_publish.add_argument("--convert-first", action="store_true", help="Run convert before publishing")
    p_publish.set_defaults(func=cmd_publish_pages)

    p_qr = sub.add_parser("generate-qrs", help="Generate QR codes for shifts")
    p_qr.add_argument("--limit", type=int, default=0, help="Only generate the first N shifts")
    p_qr.set_defaults(func=cmd_generate_qrs)

    p_send = sub.add_parser("send-email", help="Generate and send (or dry-run) a shift reminder email with QR")
    p_send.add_argument("--to", dest="to_email", required=False, help="Recipient email (overrides volunteers.json)")
    p_send.add_argument("--shift-id", dest="shift_id", required=False, help="Shift id (defaults to first shift)")
    p_send.add_argument("--volunteer-id", dest="volunteer_id", required=False, help="Volunteer id (defaults to first assigned)")
    p_send.add_argument("--dry-run", action="store_true", help="Write output to outbox/ instead of sending")
    p_send.set_defaults(func=cmd_send_email)

    p_test = sub.add_parser("test-sendgrid", help="Send a minimal SendGrid test email (connectivity)")
    p_test.add_argument("--to", dest="to_email", required=False, help="Recipient email (defaults to SENDGRID_FROM_EMAIL)")
    p_test.set_defaults(func=cmd_test_sendgrid)

    return p


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
