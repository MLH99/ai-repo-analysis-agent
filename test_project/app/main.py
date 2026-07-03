"""FastAPI-applikation med auth-endpoints."""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.auth import authenticate_user, create_access_token, decode_access_token
from app.users import create_user, get_user_profile

app = FastAPI(title="Demo API")
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Hämtar inloggad användare från Bearer-token."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ogiltig eller utgången token",
        )
    return {"user_id": int(payload["sub"]), "email": payload["email"]}


@app.post("/auth/login")
def login(request: LoginRequest) -> dict:
    """Loggar in användare och returnerar access token."""
    user = authenticate_user(request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Fel e-post eller lösenord",
        )
    token = create_access_token(user["id"], user["email"])
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/register")
def register(request: RegisterRequest) -> dict:
    """Registrerar ny användare."""
    user = create_user(request.email, request.password, request.name)
    token = create_access_token(user["id"], user["email"])
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me")
def read_current_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Returnerar profil för inloggad användare."""
    return get_user_profile(current_user["user_id"])
