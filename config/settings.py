import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Email Configuration
EMAIL_PROVIDER = os.getenv('EMAIL_PROVIDER', 'sendgrid')  # or 'gmail'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', '')
GMAIL_USER = os.getenv('GMAIL_USER', '')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', '')

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

# Supabase Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '')

# Google Calendar Configuration
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'config/credentials.json')
GOOGLE_TOKEN_FILE = os.getenv('GOOGLE_TOKEN_FILE', 'config/token.json')

# ⚠️  SECURITY: These must be set to random values in production
# Never use defaults or weak values for security keys
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not FLASK_SECRET_KEY or len(FLASK_SECRET_KEY) < 32:
    # Generate a warning but allow dev mode
    if os.getenv('FLASK_DEBUG') == 'False':
        raise ValueError("FLASK_SECRET_KEY must be set to a random value (min 32 chars) for production")

QR_SIGNING_KEY = os.getenv('QR_SIGNING_KEY', '').encode() if os.getenv('QR_SIGNING_KEY') else b'default-key-change-in-production'
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '')
SECURITY_TOKEN_KEY = os.getenv('SECURITY_TOKEN_KEY', '')

# Application Settings
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# ⚠️  SECURITY: Debug mode should NEVER be True in production
if FLASK_DEBUG and SUPABASE_URL and 'production' in SUPABASE_URL.lower():
    raise ValueError("❌ SECURITY: Flask debug mode cannot be enabled in production!")

# System Settings
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Dublin')
REMINDER_HOURS_BEFORE = int(os.getenv('REMINDER_HOURS_BEFORE', 24))
SYNC_INTERVAL_MINUTES = int(os.getenv('SYNC_INTERVAL_MINUTES', 5))
APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://localhost:5000')

# File Paths
BASE_DIR = Path(__file__).resolve().parent.parent
APPFLOWY_EXPORT_PATH = BASE_DIR / os.getenv('APPFLOWY_EXPORT_PATH', 'appflowy_exports/')
QR_CODE_OUTPUT_PATH = BASE_DIR / os.getenv('QR_CODE_OUTPUT_PATH', 'qr_codes/')
LOG_FILE_PATH = BASE_DIR / os.getenv('LOG_FILE_PATH', 'logs/')

# Create directories if they don't exist
for path in [APPFLOWY_EXPORT_PATH, QR_CODE_OUTPUT_PATH, LOG_FILE_PATH]:
    path.mkdir(parents=True, exist_ok=True)


def is_placeholder_value(value):
    """Detect obvious placeholder credentials and template values."""
    if value is None:
        return False

    normalized = str(value).strip().lower()
    if not normalized:
        return False

    placeholder_markers = (
        'your_',
        'your-',
        'your.',
        'your ',
        'placeholder',
        'changeme',
        'change-me',
        'replace_me',
        'replace-me',
        'example',
        'dummy',
    )

    return (
        normalized.startswith('https://your-project.')
        or normalized.endswith('.example.com')
        or any(marker in normalized for marker in placeholder_markers)
    )

# Validate required settings
def validate_config():
    """
    Validate that all required configuration is present
    
    Returns:
        list: Error messages, empty if valid
    """
    errors = []
    
    # Database configuration
    if not SUPABASE_URL or not SUPABASE_KEY:
        errors.append("⚠️  Supabase credentials missing (SUPABASE_URL, SUPABASE_KEY)")
    else:
        if is_placeholder_value(SUPABASE_URL) or is_placeholder_value(SUPABASE_KEY):
            errors.append("⚠️  Supabase configuration still uses placeholder values")
    
    # Email configuration
    if EMAIL_PROVIDER == 'sendgrid':
        if not SENDGRID_API_KEY or not SENDGRID_FROM_EMAIL:
            errors.append("⚠️  SendGrid configuration incomplete (SENDGRID_API_KEY, SENDGRID_FROM_EMAIL)")
        elif is_placeholder_value(SENDGRID_API_KEY) or is_placeholder_value(SENDGRID_FROM_EMAIL):
            errors.append("⚠️  SendGrid configuration still uses placeholder values")
    elif EMAIL_PROVIDER == 'gmail':
        if not GMAIL_USER or not GMAIL_APP_PASSWORD:
            errors.append("⚠️  Gmail configuration incomplete (GMAIL_USER, GMAIL_APP_PASSWORD)")
        elif is_placeholder_value(GMAIL_USER) or is_placeholder_value(GMAIL_APP_PASSWORD):
            errors.append("⚠️  Gmail configuration still uses placeholder values")
    
    # SMS configuration
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        errors.append("⚠️  Twilio SMS configuration incomplete (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)")
    elif (
        is_placeholder_value(TWILIO_ACCOUNT_SID)
        or is_placeholder_value(TWILIO_AUTH_TOKEN)
        or is_placeholder_value(TWILIO_PHONE_NUMBER)
    ):
        errors.append("⚠️  Twilio SMS configuration still uses placeholder values")
    
    # Security configuration
    if not FLASK_DEBUG and (not FLASK_SECRET_KEY or len(FLASK_SECRET_KEY) < 32):
        errors.append("❌ SECURITY: FLASK_SECRET_KEY must be set to a strong random value (min 32 chars)")
    
    if not FLASK_DEBUG and (not QR_SIGNING_KEY or QR_SIGNING_KEY == b'default-key-change-in-production'):
        errors.append("❌ SECURITY: QR_SIGNING_KEY must be set to a strong random value in production")
    
    if os.path.exists(GOOGLE_CREDENTIALS_FILE):
        pass  # Optional, only warning if used
    else:
        if EMAIL_PROVIDER != 'sendgrid' or GMAIL_USER:
            pass  # Not critical if not using Google Calendar
    
    return errors

def print_config_status():
    """Print configuration status for debugging"""
    errors = validate_config()
    
    if errors:
        print("\n⚠️  Configuration Issues Detected:")
        print("=" * 60)
        for error in errors:
            print(f"  {error}")
        print("=" * 60)
        print("\nℹ️  Some features may not work until these are configured.")
        print("See .env.template for required variables.\n")
    else:
        print("\n✅ All required configurations are present!")
        print("=" * 60)
        print(f"  Database: {'Configured' if SUPABASE_URL and not is_placeholder_value(SUPABASE_URL) else 'Not configured'}")
        print(f"  Email: {EMAIL_PROVIDER.upper()}")
        print(f"  SMS: Twilio {'Configured' if TWILIO_ACCOUNT_SID and not is_placeholder_value(TWILIO_ACCOUNT_SID) else 'Not configured'}")
        print(f"  Debug Mode: {'ENABLED' if FLASK_DEBUG else 'Disabled'}")
        print(f"  Security Keys: {'Generated' if FLASK_SECRET_KEY else 'Using defaults (dev only)'}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    print_config_status()

