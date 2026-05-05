import os
from pathlib import Path

from dotenv import load_dotenv

# Load local environment variables from .env (never commit .env).
load_dotenv()

# Email Configuration
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "sendgrid").strip().lower()  # or "gmail"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "").strip()
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "").strip()
GMAIL_USER = os.getenv("GMAIL_USER", "").strip()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "").strip()

# Security: required for signing QR tokens (no insecure defaults)
QR_SIGNING_KEY = os.getenv("QR_SIGNING_KEY", "").strip()

# System Settings
TIMEZONE = os.getenv("TIMEZONE", "Europe/Dublin").strip()

# Base URL used in email links and QR content (GitHub Pages base URL).
APP_BASE_URL = os.getenv("APP_BASE_URL", "").strip().rstrip("/")

# File Paths
BASE_DIR = Path(__file__).resolve().parent.parent
APPFLOWY_EXPORT_PATH = BASE_DIR / os.getenv("APPFLOWY_EXPORT_PATH", "appflowy_exports/")
QR_CODE_OUTPUT_PATH = BASE_DIR / os.getenv("QR_CODE_OUTPUT_PATH", "qr_codes/")
LOG_FILE_PATH = BASE_DIR / os.getenv("LOG_FILE_PATH", "logs/")

for path in (APPFLOWY_EXPORT_PATH, QR_CODE_OUTPUT_PATH, LOG_FILE_PATH):
    path.mkdir(parents=True, exist_ok=True)


def is_placeholder_value(value):
    """Detect obvious placeholder credentials and template values."""
    if value is None:
        return False

    normalized = str(value).strip().lower()
    if not normalized:
        return False

    placeholder_markers = (
        "your_",
        "your-",
        "your.",
        "your ",
        "placeholder",
        "changeme",
        "change-me",
        "replace_me",
        "replace-me",
        "example",
        "dummy",
    )

    return (
        normalized.startswith("https://your-project.")
        or normalized.endswith(".example.com")
        or any(marker in normalized for marker in placeholder_markers)
    )


def validate_config():
    """
    Validate that required configuration is present.
    Returns list[str] of errors/warnings.
    """
    errors = []

    if EMAIL_PROVIDER == "sendgrid":
        if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
            errors.append("[WARN] SendGrid configuration incomplete (SENDGRID_API_KEY, SENDGRID_FROM_EMAIL)")
        elif is_placeholder_value(SENDGRID_API_KEY) or is_placeholder_value(SENDGRID_FROM_EMAIL):
            errors.append("[WARN] SendGrid configuration still uses placeholder values")
    elif EMAIL_PROVIDER == "gmail":
        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            errors.append("[WARN] Gmail configuration incomplete (GMAIL_USER, GMAIL_APP_PASSWORD)")
        elif is_placeholder_value(GMAIL_USER) or is_placeholder_value(GMAIL_APP_PASSWORD):
            errors.append("[WARN] Gmail configuration still uses placeholder values")
    else:
        errors.append(f"[ERROR] Unknown EMAIL_PROVIDER: {EMAIL_PROVIDER!r}")

    if not QR_SIGNING_KEY or is_placeholder_value(QR_SIGNING_KEY):
        errors.append("[ERROR] SECURITY: QR_SIGNING_KEY must be set to a strong random value (required).")

    if not APP_BASE_URL or not (APP_BASE_URL.startswith("http://") or APP_BASE_URL.startswith("https://")):
        errors.append("[WARN] APP_BASE_URL should be set to your GitHub Pages URL for clickable QR codes.")

    return errors


def print_config_status():
    errors = validate_config()
    if errors:
        print("\n[WARN] Configuration Issues Detected:")
        print("=" * 60)
        for err in errors:
            print(f"  {err}")
        print("=" * 60)
        print("\n[INFO] See .env.template for required variables.\n")
        return

    print("\n[OK] Configuration looks good.")
    print("=" * 60)
    print(f"  Email provider: {EMAIL_PROVIDER}")
    print("  QR signing key: configured")
    print(f"  Base URL: {APP_BASE_URL}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_config_status()

