"""Enkel in-memory databas för demo."""

_USERS: list[dict] = [
    {
        "id": 1,
        "email": "admin@example.com",
        "password_hash": "hashed::admin123",
        "name": "Admin",
    }
]


def get_user_by_email(email: str) -> dict | None:
    """Hämtar användare via e-post."""
    for user in _USERS:
        if user["email"] == email:
            return user
    return None


def get_user_by_id(user_id: int) -> dict | None:
    """Hämtar användare via ID."""
    for user in _USERS:
        if user["id"] == user_id:
            return user
    return None


def create_user_record(email: str, password_hash: str, name: str) -> dict:
    """Skapar ny användarpost."""
    new_id = max((user["id"] for user in _USERS), default=0) + 1
    user = {
        "id": new_id,
        "email": email,
        "password_hash": password_hash,
        "name": name,
    }
    _USERS.append(user)
    return user
