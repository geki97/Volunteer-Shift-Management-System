"""
Security Utilities for Input Validation and Security Checks
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import re
import bleach
from scripts.utils.logger import logger

# Allowed HTML tags for safe email content
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'img', 'h1', 'h2', 'h3', 'div', 'span', 'table', 'tr', 'td', 'th']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title'], 'img': ['src', 'alt', 'width', 'height']}

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class SecurityValidator:
    """Security validation utilities"""
    
    # Validation patterns
    UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$', re.IGNORECASE)
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    PHONE_PATTERN = re.compile(r'^\+?\d{10,15}$')
    
    @staticmethod
    def validate_shift_id(shift_id: str, allow_uuid: bool = True) -> bool:
        """
        Validate shift ID format
        
        Args:
            shift_id: Shift identifier to validate
            allow_uuid: Whether to allow UUID format (else requires alphanumeric)
        
        Returns:
            bool: True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if not shift_id or not isinstance(shift_id, str):
            raise ValidationError("Shift ID must be a non-empty string")
        
        shift_id = shift_id.strip()
        
        if len(shift_id) < 3 or len(shift_id) > 100:
            raise ValidationError("Shift ID must be between 3 and 100 characters")
        
        if allow_uuid and SecurityValidator.UUID_PATTERN.match(shift_id):
            return True
        
        if SecurityValidator.ALPHANUMERIC_PATTERN.match(shift_id):
            return True
        
        raise ValidationError(f"Invalid shift ID format: {shift_id}")
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """
        Validate user ID (can be UUID or alphanumeric)
        
        Args:
            user_id: User identifier to validate
        
        Returns:
            bool: True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("User ID must be a non-empty string")
        
        user_id = user_id.strip()
        
        if len(user_id) < 3 or len(user_id) > 100:
            raise ValidationError("User ID must be between 3 and 100 characters")
        
        if SecurityValidator.UUID_PATTERN.match(user_id):
            return True
        
        if SecurityValidator.ALPHANUMERIC_PATTERN.match(user_id):
            return True
        
        raise ValidationError(f"Invalid user ID format: {user_id}")
    
    @staticmethod
    def validate_token(token: str, max_length: int = 5000) -> bool:
        """
        Validate token format (base64-encoded)
        
        Args:
            token: Token to validate
            max_length: Maximum allowed token length
        
        Returns:
            bool: True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if not token or not isinstance(token, str):
            raise ValidationError("Token must be a non-empty string")
        
        if len(token) > max_length:
            raise ValidationError(f"Token exceeds maximum length of {max_length}")
        
        # Basic base64 validation (should contain only base64 chars)
        base64_pattern = re.compile(r'^[A-Za-z0-9+/=._-]+$')
        if not base64_pattern.match(token):
            raise ValidationError("Token contains invalid characters")
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address to validate
        
        Returns:
            bool: True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")
        
        email = email.strip().lower()
        
        if len(email) > 254:
            raise ValidationError("Email is too long (max 254 characters)")
        
        if not SecurityValidator.EMAIL_PATTERN.match(email):
            raise ValidationError(f"Invalid email format: {email}")
        
        return True
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        Validate phone number
        
        Args:
            phone: Phone number to validate
        
        Returns:
            bool: True if valid
        
        Raises:
            ValidationError: If validation fails
        """
        if not phone or not isinstance(phone, str):
            raise ValidationError("Phone must be a non-empty string")
        
        # Remove common phone formatting
        cleaned = re.sub(r'[\s\-().]', '', phone.strip())
        
        if not SecurityValidator.PHONE_PATTERN.match(cleaned):
            raise ValidationError(f"Invalid phone format: {phone}")
        
        return True
    
    @staticmethod
    def sanitize_html(html_content: str) -> str:
        """
        Sanitize HTML to prevent XSS attacks
        
        Args:
            html_content: HTML content to sanitize
        
        Returns:
            str: Cleaned HTML
        """
        if not html_content:
            return ""
        
        cleaned = bleach.clean(
            html_content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        return cleaned
    
    @staticmethod
    def escape_for_json(text: str) -> str:
        """
        Escape text for safe JSON inclusion
        
        Args:
            text: Text to escape
        
        Returns:
            str: Escaped text safe for JSON
        """
        if not text:
            return ""
        
        # Python's json module handles escaping, but be explicit
        return text.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')


def validate_request_data(data: dict, required_fields: list) -> bool:
    """
    Validate request data contains all required fields
    
    Args:
        data: Request data dictionary
        required_fields: List of required field names
    
    Returns:
        bool: True if all required fields present
    
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(data, dict):
        raise ValidationError("Data must be a dictionary")
    
    missing_fields = [f for f in required_fields if f not in data or not data[f]]
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True
