"""Autentisering och auktorisering."""

from datetime import datetime, timedelta, timezone

import jwt

from app.database import get_user_by_email
from config import JWT_SECRET, JWT_ALGORITHM, TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """Hashar lösenord innan lagring (förenklad demo)."""
    return f"hashed::{password}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifierar lösenord mot hash."""
    return hash_password(plain_password) == hashed_password


def create_access_token(user_id: int, email: str) -> str:
    """Skapar JWT-token för inloggad användare."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def authenticate_user(email: str, password: str) -> dict | None:
    """Autentiserar användare med e-post och lösenord."""
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


def decode_access_token(token: str) -> dict | None:
    """Avkodar och validerar JWT-token."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
