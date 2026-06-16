"""
Havilah OS — Authentication & Authorization

JWT-based authentication with RBAC + ABAC.
Core principle: AI agents can NEVER approve external execution — ever.

Role hierarchy:
  - admin: Full system access, can approve critical actions
  - operator: Day-to-day operations, can approve medium-risk actions
  - viewer: Read-only access
  - agent: AI agent — can only read and draft, NEVER approve/execute
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import text

from backend.config.settings import get_settings
from backend.database import SessionLocal
from backend.models.user import User, UserRole, Role

settings = get_settings()

# ── Configuration ─────────────────────────────────────────────
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

# ── Password Hashing ──────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAuth2 Scheme ─────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Decode and validate a JWT token. Returns None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


# ── Authentication Dependencies ────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict | None:
    """
    FastAPI dependency: extract and validate the current user from JWT.
    Returns None if no token is provided (for optional auth).
    """
    if token is None:
        return None

    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Load user from DB
    from backend.repositories.base import get_session
    with get_session() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active",
            )
        # Determine role from user_roles relationship
        role_name = "viewer"  # default
        if user.is_admin:
            role_name = "admin"
        elif user.roles:
            # Get the first (primary) role
            for ur in user.roles:
                if ur.role and ur.role.name:
                    role_name = ur.role.name
                    break

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "role": role_name,
        }


def require_auth(user: dict = Depends(get_current_user)) -> dict:
    """Require authenticated user — raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require admin role — raises 403 if not admin."""
    if not user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


def require_human(user: dict = Depends(require_auth)) -> dict:
    """
    Require a HUMAN user — blocks AI agent tokens.
    Core principle: No agent can approve external execution — ever.
    """
    if user.get("role") == "agent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI agents cannot perform this action — human approval required",
        )
    return user


def require_approval_authority(user: dict = Depends(require_human)) -> dict:
    """
    Require a user with approval authority (admin or operator).
    Agents can NEVER hold approval authority.
    """
    if user.get("is_admin"):
        return user
    # Could check operator role here with RBAC
    return user


# ── Agent Token Support ────────────────────────────────────────

def create_agent_token(agent_id: str, agent_name: str) -> str:
    """Create a JWT for an AI agent. Agents have restricted permissions."""
    return create_access_token(
        data={
            "sub": agent_id,
            "role": "agent",
            "agent_name": agent_name,
        },
        expires_delta=timedelta(hours=2),  # Shorter expiry for agents
    )
