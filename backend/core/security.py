"""
JWT token management and password hashing for authentication.
"""
import logging
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# --- Monkeypatch passlib for bcrypt compatibility ---
# Recent bcrypt versions changed their internal structure,
# which passlib's bcrypt handler expects to find in __about__.
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("About", (), {"__version__": bcrypt.__version__})

from backend.config import get_config

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    config = get_config()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=config.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.jwt_secret, algorithm=config.jwt_algorithm)
    logger.debug("Access token created for sub=%s", data.get("sub"))
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT token. Returns payload or None."""
    config = get_config()
    try:
        payload = jwt.decode(token, config.jwt_secret, algorithms=[config.jwt_algorithm])
        return payload
    except JWTError as e:
        logger.warning("JWT decode failed: %s", str(e))
        return None
