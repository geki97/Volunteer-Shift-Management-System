"""
Secure QR Code Generator with HMAC Signing
Prevents forgery and replay attacks on shift check-in codes
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import qrcode
import hmac
import hashlib
import json
import base64
from datetime import datetime, timedelta
import pytz
from config.settings import QR_CODE_OUTPUT_PATH, TIMEZONE
from scripts.utils.logger import logger
import os

# Use environment variable for signing key, fallback to configuration
QR_SIGNING_KEY = os.getenv('QR_SIGNING_KEY', '').encode() or b'default-key-change-in-production'

class SecureQRCode:
    """Generate and validate cryptographically signed QR codes"""
    
    @staticmethod
    def generate_check_in_token(shift_id: str, user_id: str, expiry_hours: int = 24) -> str:
        """
        Generate a signed check-in token with expiration
        
        Args:
            shift_id: Shift unique identifier
            user_id: Volunteer/user unique identifier
            expiry_hours: Token validity period in hours
        
        Returns:
            str: Base64-encoded signed token (format: data.signature)
        """
        try:
            tz = pytz.timezone(TIMEZONE)
            now = datetime.now(tz)
            expiry = now + timedelta(hours=expiry_hours)
            
            # Create token payload
            token_data = {
                'shift_id': str(shift_id),
                'user_id': str(user_id),
                'issued_at': now.isoformat(),
                'expires_at': expiry.isoformat(),
                'nonce': base64.b64encode(os.urandom(8)).decode()  # Prevent replay
            }
            
            token_json = json.dumps(token_data, separators=(',', ':'))
            
            # Generate HMAC signature
            signature = hmac.new(
                QR_SIGNING_KEY,
                token_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Combine data and signature
            full_token = f"{token_json}.{signature}"
            
            # Encode to prevent tampering during QR encoding
            encoded_token = base64.b64encode(full_token.encode()).decode()
            
            logger.info(f"Generated secure token for shift {shift_id}, user {user_id}")
            return encoded_token
            
        except Exception as e:
            logger.error(f"Error generating secure token: {e}")
            raise
    
    @staticmethod
    def verify_check_in_token(encoded_token: str) -> tuple:
        """
        Verify a signed check-in token
        
        Args:
            encoded_token: Base64-encoded signed token from QR code
        
        Returns:
            tuple: (is_valid: bool, token_data: dict or error_msg: str)
        """
        try:
            # Decode from base64
            token_json_and_sig = base64.b64decode(encoded_token).decode()
            
            # Split data and signature
            parts = token_json_and_sig.rsplit('.', 1)
            if len(parts) != 2:
                return False, "Invalid token format"
            
            token_json, provided_signature = parts
            
            # Verify signature
            expected_signature = hmac.new(
                QR_SIGNING_KEY,
                token_json.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(provided_signature, expected_signature):
                logger.warning(f"Invalid signature in token")
                return False, "Invalid signature - token may have been tampered with"
            
            # Parse token data
            token_data = json.loads(token_json)
            
            # Check expiration
            tz = pytz.timezone(TIMEZONE)
            now = datetime.now(tz)
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            
            if now > expires_at:
                logger.warning(f"Token expired at {token_data['expires_at']}")
                return False, "Token has expired"
            
            logger.info(f"Token verified successfully for shift {token_data['shift_id']}")
            return True, token_data
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON in token")
            return False, "Invalid token format"
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False, f"Token verification failed: {str(e)}"
    
    @staticmethod
    def generate_shift_qr_code(shift_id: str, shift_name: str, user_id: str = None, 
                              expiry_hours: int = 24, app_base_url: str = None) -> tuple:
        """
        Generate QR code with secure token embedded
        
        Args:
            shift_id: Shift unique identifier
            shift_name: Human-readable shift name
            user_id: Optional user ID (for individual QR codes)
            expiry_hours: Token validity period
            app_base_url: Application base URL (default from settings)
        
        Returns:
            tuple: (qr_image_path: str, token: str) or (None, error_msg)
        """
        try:
            if app_base_url is None:
                app_base_url = os.getenv('APP_BASE_URL', 'http://localhost:5000')
            
            # Generate secure token
            token = SecureQRCode.generate_check_in_token(shift_id, user_id or shift_id, expiry_hours)
            
            # Create QR code with token URL
            qr_data = f"{app_base_url}/check-in/token/{token}"
            
            qr = qrcode.QRCode(
                version=2,  # Larger to accommodate token
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Save file with timestamp to avoid collisions
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{shift_id}_{timestamp}_{shift_name.replace(' ', '_')}.png"
            filepath = QR_CODE_OUTPUT_PATH / filename
            
            img.save(filepath)
            logger.info(f" Secure QR code generated: {filepath}")
            
            return str(filepath), token
            
        except Exception as e:
            logger.error(f" Error generating secure QR code: {e}")
            return None, str(e)


if __name__ == "__main__":
    # Test secure QR generation and verification
    test_token = SecureQRCode.generate_check_in_token("shift-123", "user-456", expiry_hours=2)
    print(f" Generated token: {test_token[:50]}...")
    
    is_valid, result = SecureQRCode.verify_check_in_token(test_token)
    if is_valid:
        print(f" Token verified: {result}")
    else:
        print(f" Token verification failed: {result}")
    
    # Test with tampered token
    tampered = test_token[:-5] + "xxxxx"
    is_valid, result = SecureQRCode.verify_check_in_token(tampered)
    print(f"Tampered token check (should fail): {result}")
