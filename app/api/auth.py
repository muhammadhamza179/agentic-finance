# app/api/auth.py

from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

bearer_scheme = HTTPBearer()

# bcrypt only hashes the first 72 bytes; normalize explicitly to avoid surprises.
_BCRYPT_MAX_BYTES = 72


def _password_bytes(password: str) -> bytes:
    raw = password.encode("utf-8")
    if len(raw) > _BCRYPT_MAX_BYTES:
        return raw[:_BCRYPT_MAX_BYTES]
    return raw


def hash_password(password: str) -> str:
    digest = bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt())
    return digest.decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_password_bytes(plain), hashed.encode("ascii"))
    except ValueError:
        return False


def create_token(user_id: int, username: str) -> str:
    """Create a JWT that expires in 60 minutes."""
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises if expired or tampered."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}") from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency — add to any route to require auth.

    Usage:
        @app.post("/query")
        async def query(user = Depends(get_current_user)):
            ...
    """
    return decode_token(credentials.credentials)
