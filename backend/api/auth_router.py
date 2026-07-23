from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as g_requests

from database import get_db
from models.user import User
from utils.auth import hash_password, verify_password, create_access_token
from api.schemas import RegisterRequest, LoginRequest, GoogleAuthRequest, TokenResponse, UserOut
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        full_name=body.full_name,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not user.hashed_password or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/google", response_model=TokenResponse)
def google_auth(body: GoogleAuthRequest, db: Session = Depends(get_db)):
    try:
        info = id_token.verify_oauth2_token(body.id_token, g_requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")

    google_id = info["sub"]
    email = info.get("email", "")
    full_name = info.get("name", email)

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            user = User(full_name=full_name, email=email, google_id=google_id)
            db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
