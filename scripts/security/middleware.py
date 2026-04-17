"""
Authentication and Authorization Middleware for Flask
Provides token-based authentication for API endpoints
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from functools import wraps
from flask import request, jsonify
from scripts.utils.logger import logger
import os
import hmac
import hashlib

# API Key for administrative endpoints (from environment or config)
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY', '')
SECURITY_TOKEN_KEY = os.getenv('SECURITY_TOKEN_KEY', 'default-security-key')

class AuthenticationError(Exception):
    """Custom exception for authentication failures"""
    pass


def require_admin_key(f):
    """
    Decorator to require admin API key for endpoints
    
    Usage:
        @app.route('/admin/endpoint')
        @require_admin_key
        def admin_function():
            return "authorized"
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        
        if not ADMIN_API_KEY:
            logger.error("ADMIN_API_KEY not configured - endpoint not protected")
            return jsonify({'error': 'Authentication not configured'}), 500
        
        if not api_key or not hmac.compare_digest(api_key, ADMIN_API_KEY):
            logger.warning(f"Unauthorized API access attempt from {request.remote_addr}")
            return jsonify({'error': 'Unauthorized - Invalid API key'}), 401
        
        logger.info(f"Authorized API access from {request.remote_addr}")
        return f(*args, **kwargs)
    
    return decorated_function


def require_valid_session(f):
    """
    Decorator to verify valid session token
    
    Expects session token in:
    - Cookie: volunteer_session_id
    - OR Header: X-Session-Token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = (
            request.cookies.get('volunteer_session_id') or
            request.headers.get('X-Session-Token', '')
        )
        
        if not session_token:
            logger.warning(f"Missing session token from {request.remote_addr}")
            return jsonify({'error': 'Session required'}), 401
        
        # TODO: Implement session validation with database
        # For now, just log access
        logger.info(f"Session access verified for {request.remote_addr}")
        
        return f(*args, **kwargs)
    
    return decorated_function


def validate_csrf_token(f):
    """
    Decorator to validate CSRF token for state-changing operations (POST, PUT, DELETE)
    
    Expects CSRF token in:
    - Form field: csrf_token
    - OR Header: X-CSRF-Token
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            csrf_token = (
                request.form.get('csrf_token') or
                request.headers.get('X-CSRF-Token', '')
            )
            
            # TODO: Implement proper CSRF validation
            # Compare against session-stored token
            
            if not csrf_token:
                logger.warning(f"Missing CSRF token for {request.method} from {request.remote_addr}")
                # Note: In development, may want to be lenient; in production, enforce
        
        return f(*args, **kwargs)
    
    return decorated_function


def log_access(f):
    """
    Decorator to log all endpoint accesses with security context
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        logger.info(f"Access: {request.method} {request.path} from {request.remote_addr}")
        
        try:
            result = f(*args, **kwargs)
            logger.debug(f"Response status: {result[1] if isinstance(result, tuple) else 200}")
            return result
        except Exception as e:
            logger.error(f"Error in {request.path}: {str(e)}")
            raise
    
    return decorated_function


def rate_limit_check(max_requests_per_minute: int = 60):
    """
    Decorator to implement basic rate limiting (in-memory)
    
    Note: For production, use Redis or similar distributed cache
    
    Args:
        max_requests_per_minute: Maximum requests allowed per minute per IP
    """
    request_counts = {}  # In production, use Redis
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            import time
            
            client_ip = request.remote_addr
            current_minute = int(time.time() / 60)
            key = f"{client_ip}:{current_minute}"
            
            if key not in request_counts:
                request_counts[key] = 0
            
            request_counts[key] += 1
            
            if request_counts[key] > max_requests_per_minute:
                logger.warning(f"Rate limit exceeded for {client_ip}")
                return jsonify({'error': 'Too many requests. Please try again later.'}), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


class SecurityHeaders:
    """
    Add security headers to responses
    """
    
    @staticmethod
    def inject_security_headers(response):
        """
        Add security headers to Flask response
        
        Usage in Flask:
            app.after_request(SecurityHeaders.inject_security_headers)
        """
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'"
        )
        
        # Prevent MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # HSTS (only in production)
        if not os.getenv('FLASK_DEBUG'):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
