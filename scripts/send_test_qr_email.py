#!/usr/bin/env python
"""
Send a single test reminder email with a QR code.

This is a developer smoke-test for the end-to-end flow:
exports -> QR generation -> email content -> email send (or dry-run output).

Usage:
    # Test SendGrid connectivity
    python send_test_qr_email.py --test-sendgrid --to your_email@example.com
    
    # Generate dry-run email with QR (no actual sending)
    python send_test_qr_email.py --dry-run
    
    # Send actual email to first volunteer with first shift
    python send_test_qr_email.py
    
    # Send to specific volunteer and shift
    python send_test_qr_email.py --to volunteer@example.com --shift-id 123 --volunteer-id 456
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.settings import (
    APPFLOWY_EXPORT_PATH, 
    APP_BASE_URL, 
    is_placeholder_value, 
    SENDGRID_API_KEY, 
    SENDGRID_FROM_EMAIL
)
from scripts.security.qr_secure import SecureQRCode
from scripts.utils.email_service_enhanced import (
    create_shift_reminder_email_with_qr,
    send_email_with_qr_attachment,
)
from scripts.utils.logger import logger

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False


def _load_json(path: Path):
    """Load JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def test_sendgrid_connectivity(test_email: str = None) -> bool:
    """
    Test SendGrid API connectivity and credentials.
    Sends a minimal test email to verify the API key and sender email are valid.
    
    Args:
        test_email: Email address to send test message to (defaults to from email)
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    if not SENDGRID_AVAILABLE:
        print("[ERROR] sendgrid package not installed. Run: pip install sendgrid")
        return False
    
    if is_placeholder_value(SENDGRID_API_KEY):
        print("[ERROR] SENDGRID_API_KEY appears to be a placeholder in .env")
        return False
    
    if is_placeholder_value(SENDGRID_FROM_EMAIL):
        print("[ERROR] SENDGRID_FROM_EMAIL appears to be a placeholder in .env")
        return False
    
    if not test_email:
        test_email = SENDGRID_FROM_EMAIL
    
    try:
        print("\n[*] Testing SendGrid API connectivity...")
        print(f"    From: {SENDGRID_FROM_EMAIL}")
        print(f"    To:   {test_email}")
        print()
        
        # Create a simple test email
        message = Mail(
            from_email=SENDGRID_FROM_EMAIL,
            to_emails=test_email,
            subject='Volunteer Management System - SendGrid Connectivity Test',
            html_content='''
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2>SendGrid Connection Test</h2>
                    <p>If you received this email, your <strong>SendGrid API key is working correctly!</strong></p>
                    <p>Your Volunteer Management System is ready to send shift reminders with QR codes.</p>
                    <hr>
                    <p style="color: #999; font-size: 12px;">Volunteer Management System - Connectivity Test</p>
                </body>
            </html>
            '''
        )
        
        # Send the message
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code in [200, 201, 202]:
            print("[OK] SendGrid connection test successful!")
            print(f"    Status Code: {response.status_code}")
            print(f"    Message ID: {response.headers.get('X-Message-Id', 'N/A')}")
            print()
            logger.info(f"SendGrid connectivity test passed - Status: {response.status_code}")
            return True
        else:
            print(f"[ERROR] SendGrid returned unexpected status: {response.status_code}")
            if hasattr(response, 'body'):
                print(f"    Response Body: {response.body}")
            logger.error(f"SendGrid test failed - Status: {response.status_code}")
            return False
            
    except Exception as e:
        print("[ERROR] SendGrid connection test failed:")
        print(f"    {type(e).__name__}: {str(e)}")
        print()
        logger.error(f"SendGrid connectivity test error: {e}")
        return False


def main(argv: list[str]) -> int:
    """Main function to send QR code email or test SendGrid."""
    parser = argparse.ArgumentParser(
        description="Send a test shift reminder email with QR code."
    )
    parser.add_argument(
        "--to", 
        dest="to_email", 
        required=False, 
        help="Recipient email address"
    )
    parser.add_argument(
        "--shift-id", 
        dest="shift_id", 
        required=False, 
        help="Shift id (defaults to first shift)"
    )
    parser.add_argument(
        "--volunteer-id", 
        dest="volunteer_id", 
        required=False, 
        help="Volunteer id (defaults to first assigned)"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Write output to outbox/ instead of sending"
    )
    parser.add_argument(
        "--test-sendgrid",
        action="store_true",
        help="Test SendGrid API connectivity without sending actual shift email"
    )
    
    args = parser.parse_args(argv)
    
    # Handle SendGrid connectivity test
    if args.test_sendgrid:
        success = test_sendgrid_connectivity(test_email=args.to_email)
        return 0 if success else 1
    
    # Load data files
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

    # Select shift
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

    # Extract shift details
    shift_id = str(shift.get("id"))
    shift_name = shift.get("shift_name", "Shift")
    shift_date_raw = shift.get("shift_date", "")
    shift_date = shift_date_raw.split("T")[0] if "T" in shift_date_raw else shift_date_raw
    shift_time = shift_date_raw.split("T")[1][:5] if "T" in shift_date_raw else "Unknown"
    location = shift.get("location", "TBD")

    # Select volunteer
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

    # Generate QR code (token points to /check-in.html?token=<token>)
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

    base_url = (APP_BASE_URL or "").strip().rstrip("/")
    import urllib.parse
    token_q = urllib.parse.quote(token, safe="")
    check_in_url = f"{base_url}/check-in.html?token={token_q}" if base_url else f"check-in.html?token={token_q}"

    if not args.dry_run:
        # For a real email meant to be scanned on a phone, the QR should contain
        # an absolute URL (GitHub Pages or your locally tunneled URL).
        if not base_url or not (base_url.startswith("http://") or base_url.startswith("https://")):
            print("[ERROR] APP_BASE_URL must be set to an absolute URL for a real send.")
            print("Set APP_BASE_URL in .env, e.g.:")
            print("  APP_BASE_URL=https://geki97.github.io/Volunteer-Shift-Management-System")
            print("  APP_BASE_URL=https://<your-backend-domain>")
            print("Then re-run without --dry-run.")
            return 2

    # Create email content
    html_content, text_content, _ = create_shift_reminder_email_with_qr(
        volunteer_name=volunteer_name,
        shift_name=shift_name,
        shift_date=shift_date,
        shift_time=shift_time,
        location=location,
        qr_code_path=qr_path,
        special_instructions=shift.get("special_instructions") or None,
    )

    # Dry-run mode: write to file instead of sending
    if args.dry_run:
        outbox = Path("outbox")
        outbox.mkdir(parents=True, exist_ok=True)
        html_path = outbox / "test_qr_email.html"
        with open(html_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html_content)
        print("\n[OK] Dry-run email preview generated:")
        print(f"    HTML File: {html_path.resolve()}")
        print(f"    QR Code:   {Path(qr_path).resolve()}")
        print(f"    Check-In URL: {check_in_url}")
        print(f"    Recipient: {volunteer_email or 'Not specified'}")
        print("\nTo send this email, run without --dry-run flag\n")
        return 0

    # Validate configuration before sending
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

    # Send the email
    print(f"\n[*] Sending shift reminder email via {provider}...")
    success, message_id = send_email_with_qr_attachment(
        to_email=volunteer_email,
        subject=f"Shift Reminder: {shift_name}",
        html_content=html_content,
        qr_code_path=qr_path,
        text_content=text_content,
    )

    if success:
        print("\n[OK] Email sent successfully!")
        print(f"    To: {volunteer_email}")
        print(f"    Shift: {shift_name} on {shift_date} at {shift_time}")
        print(f"    Location: {location}")
        print(f"    QR Code: {Path(qr_path).resolve()}")
        print(f"    Check-In URL: {check_in_url}")
        print(f"    Provider Message ID: {message_id}")
        print()
        return 0

    print("\n[ERROR] Email send failed:")
    print(f"    {message_id}")
    print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
