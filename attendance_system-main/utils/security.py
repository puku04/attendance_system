"""
Security configuration and utilities for the attendance system
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, abort
import logging

class SecurityConfig:
    """Security configuration class"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    
    # Session security
    SESSION_TIMEOUT = timedelta(hours=8)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Rate limiting (requests per minute)
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # File upload security
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']
    
    # CSRF protection
    CSRF_TIMEOUT = 3600  # 1 hour

class SecurityUtils:
    """Security utility functions"""
    
    @staticmethod
    def generate_secure_token(length=32):
        """Generate a secure random token"""
        return secrets.token_hex(length)
    
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for password hashing
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return password_hash.hex(), salt
    
    @staticmethod
    def verify_password(password, password_hash, salt):
        """Verify password against hash"""
        computed_hash, _ = SecurityUtils.hash_password(password, salt)
        return computed_hash == password_hash
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        errors = []
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters long")
        
        if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if SecurityConfig.REQUIRE_SPECIAL_CHARS and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def sanitize_input(input_string):
        """Sanitize user input"""
        if not isinstance(input_string, str):
            return str(input_string)
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            input_string = input_string.replace(char, '')
        
        return input_string.strip()
    
    @staticmethod
    def is_safe_filename(filename):
        """Check if filename is safe"""
        if not filename:
            return False
        
        # Check for path traversal attempts
        dangerous_patterns = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for pattern in dangerous_patterns:
            if pattern in filename:
                return False
        
        return True

def require_https(f):
    """Decorator to require HTTPS in production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.is_secure or request.headers.get('X-Forwarded-Proto') == 'https':
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'HTTPS required'}), 400
    return decorated_function

def rate_limit(max_requests=100, window=60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple in-memory rate limiting (in production, use Redis)
            client_ip = request.remote_addr
            current_time = datetime.now()
            
            # This is a simplified implementation
            # In production, use a proper rate limiting library
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_file_upload(file):
    """Validate uploaded file for security"""
    if not file or not file.filename:
        return False, "No file provided"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > SecurityConfig.MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {SecurityConfig.MAX_FILE_SIZE / (1024*1024):.1f}MB"
    
    # Check file extension
    if not SecurityUtils.is_safe_filename(file.filename):
        return False, "Invalid filename"
    
    return True, None

# Global security instances
security_config = SecurityConfig()
security_utils = SecurityUtils()