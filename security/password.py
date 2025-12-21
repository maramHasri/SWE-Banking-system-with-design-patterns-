"""
Password hashing and verification utilities
Uses Werkzeug's secure password hashing
"""

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    """
    Hash a password using Werkzeug's secure hashing
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return generate_password_hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        password_hash: Hashed password from database
        password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    if not password_hash:
        return False
    return check_password_hash(password_hash, password)

