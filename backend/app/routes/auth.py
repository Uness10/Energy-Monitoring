import bcrypt
from fastapi import APIRouter, HTTPException
from ..models.schemas import UserLogin, UserRegister, TokenResponse
from ..auth.jwt_handler import create_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# In-memory user store (replace with DB table for production)
_users: dict[str, dict] = {}


@router.post("/register")
def register(body: UserRegister):
    if body.username in _users:
        raise HTTPException(status_code=409, detail="User already exists")
    password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    _users[body.username] = {"password_hash": password_hash, "role": body.role}
    return {"username": body.username, "role": body.role}


@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin):
    user = _users.get(body.username)
    if not user or not bcrypt.checkpw(body.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": body.username, "role": user["role"]})
    return TokenResponse(access_token=token)
