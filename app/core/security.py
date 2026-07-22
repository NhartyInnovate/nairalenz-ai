from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt, JWTError
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError
from app.core.config import settings

# Constant representing the token type
ACCESS_TOKEN_TYPE = "access"

# Initialize password hashing using pwdlib (default is argon2)
password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """
    Hash a password securely using Argon2.
    """
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against the hashed password.
    """
    try:
        return password_hash.verify(plain_password, hashed_password)
    except (PwdlibError, ValueError):
        return False

def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token. Keep payload minimal: sub, exp, and type.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "type": ACCESS_TOKEN_TYPE
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode a JWT access token and return the payload.
    Centralized JWT decoding helper.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

def verify_access_token(token: str) -> bool:
    """
    Verify if a JWT token is valid and of access type.
    Extension point for future validation rules (e.g. jti/revocation checks).
    """
    payload = decode_access_token(token)
    if not payload:
        return False
    return payload.get("type") == ACCESS_TOKEN_TYPE
