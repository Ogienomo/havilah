"""
Havilah OS — Authentication API

Login, token management, and user registration.
Core principle: AI agents can NEVER approve external execution.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    require_auth,
    require_admin,
)
from backend.repositories.base import get_session
from backend.models.user import User, Role, UserRole

from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=1)
    full_name: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    is_admin: bool = False


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


@router.post("/token", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Authenticate a user and return a JWT token.
    """
    with get_session() as db:
        user = db.query(User).filter(User.email == payload.email).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active",
            )
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Determine role
        role_name = "admin" if user.is_admin else "viewer"
        if user.roles:
            for ur in user.roles:
                if ur.role and ur.role.name:
                    role_name = ur.role.name
                    break

        token = create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "role": role_name,
        })

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
        )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest):
    """
    Register a new user account.
    First registered user is automatically admin.
    """
    with get_session() as db:
        # Check if email already exists
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # First user is admin
        user_count = db.query(User).count()
        is_admin = user_count == 0

        user = User(
            email=payload.email,
            full_name=payload.full_name,
            password_hash=get_password_hash(payload.password),
            is_admin=is_admin,
        )
        db.add(user)
        db.flush()

        # Assign default role
        default_role = db.query(Role).filter(Role.name == "admin" if is_admin else "operator").first()
        if default_role:
            db.add(UserRole(user_id=user.id, role_id=default_role.id))
            db.flush()

        # Determine role for token
        role_name = "admin" if is_admin else "operator"

        token = create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "role": role_name,
        })

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
        )


@router.get("/me")
def get_current_user_info(user: dict = Depends(require_auth)):
    """Get the current authenticated user's info."""
    return user


@router.post("/change-password")
def change_password(
    payload: PasswordChangeRequest,
    user: dict = Depends(require_auth),
):
    """Change the current user's password."""
    with get_session() as db:
        db_user = db.query(User).filter(User.id == user["id"]).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(payload.current_password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect",
            )

        db_user.password_hash = get_password_hash(payload.new_password)
        db.flush()

    return {"message": "Password changed successfully"}
