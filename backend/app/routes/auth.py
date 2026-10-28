import hmac
import hashlib
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..auth_utils import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "dev-only-change-this-secret-before-deployment"
)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash new passwords using the recommended password-hashing algorithm."""
    return password_hash.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    """Support existing SHA-256 hashes and upgrade them after successful login."""
    if not stored_hash:
        return False

    # Legacy SHA-256 hashes are 64 hexadecimal characters.
    if len(stored_hash) == 64:
        try:
            int(stored_hash, 16)
        except ValueError:
            pass
        else:
            legacy_hash = hashlib.sha256(
                password.encode("utf-8")
            ).hexdigest()

            return hmac.compare_digest(
                legacy_hash,
                stored_hash.lower()
            )

    try:
        return password_hash.verify(password, stored_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


@router.post("/register")
def register(
    name: str,
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    name = name.strip()
    email = email.strip().lower()

    if not name or not email or not password:
        raise HTTPException(
            status_code=400,
            detail="Name, email and password are required"
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )

    existing_user = db.query(User).filter(
        User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = User(
        name=name,
        email=email,
        password=hash_password(password),
        role="user"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.strip().lower()
    password = form_data.password

    user = db.query(User).filter(
        User.email == email
    ).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Upgrade a legacy SHA-256 hash after successful verification.
    if len(user.password) == 64:
        try:
            int(user.password, 16)
        except ValueError:
            pass
        else:
            user.password = hash_password(password)
            db.commit()
            db.refresh(user)

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }


@router.get("/me")
def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role
    }
