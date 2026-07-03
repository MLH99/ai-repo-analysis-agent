"""Användarhantering."""

from app.auth import hash_password
from app.database import create_user_record, get_user_by_id


def create_user(email: str, password: str, name: str) -> dict:
    """Skapar ny användare i databasen."""
    password_hash = hash_password(password)
    return create_user_record(email=email, password_hash=password_hash, name=name)


def get_user_profile(user_id: int) -> dict:
    """Hämtar offentlig profil för en användare."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValueError(f"Användare {user_id} hittades inte")
    return {"id": user["id"], "email": user["email"], "name": user["name"]}
