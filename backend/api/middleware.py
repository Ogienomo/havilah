"""
Havilah OS — Auth Middleware & RBAC Enforcement

FastAPI middleware and dependency that enforces:
1. JWT authentication on all /api/* routes (except auth & health)
2. Role-based access control via permission matrix
3. Human-only gate for approval/execution endpoints
4. Request audit logging

Core principle: AI agents can NEVER approve external execution — ever.
"""

import time
import logging
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from backend.api.auth import decode_access_token, get_current_user
from backend.api.permissions import (
    ROLE_PERMISSIONS,
    HUMAN_ONLY_PERMISSIONS,
    RoleName,
)

logger = logging.getLogger("havilah.auth")

# ── OAuth2 scheme (optional — returns None if no token) ───────────
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/token", auto_error=False
)


# ── Permission Check Dependency ───────────────────────────────────

class RequirePermission:
    """
    FastAPI dependency factory: `Depends(RequirePermission("approval:approve"))`

    Checks:
    1. User is authenticated (valid JWT)
    2. User's role has the required permission
    3. If the permission is human-only, user must NOT be an agent
    """

    def __init__(self, permission: str):
        self.permission = permission

    def __call__(self, user: dict = Depends(get_current_user)):
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check human-only gate
        if self.permission in HUMAN_ONLY_PERMISSIONS:
            if user.get("role") == "agent":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"AI agents cannot perform '{self.permission}' — "
                        "human approval required. This is a non-negotiable "
                        "architectural principle of Havilah OS."
                    ),
                )

        # Check role-based permission
        user_role = user.get("role", "viewer")
        try:
            role_enum = RoleName(user_role)
        except ValueError:
            role_enum = RoleName.VIEWER

        allowed = ROLE_PERMISSIONS.get(role_enum, set())
        if self.permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permission denied: '{self.permission}' "
                    f"not available for role '{user_role}'"
                ),
            )

        return user


# ── Convenience aliases for common auth patterns ──────────────────

# Any authenticated user
require_auth = get_current_user

# Admin only
from backend.api.auth import require_admin

# Human only (blocks agents from approval/execution)
from backend.api.auth import require_human

# Approval authority (admin or operator, never agent)
from backend.api.auth import require_approval_authority

# Permission-specific factories
require_approval_approve = RequirePermission("approval:approve")
require_approval_execute = RequirePermission("approval:execute")
require_approval_reject = RequirePermission("approval:reject")
require_approval_escalate = RequirePermission("approval:escalate")


# ── Audit Middleware ──────────────────────────────────────────────

class AuditMiddleware:
    """
    ASGI middleware that logs every API request with auth context.
    Records: timestamp, method, path, user_id, role, response_code, duration_ms
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        request = Request(scope)

        # Extract auth info from headers
        auth_header = request.headers.get("authorization", "")
        user_id = None
        user_role = None
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_access_token(token)
            if payload:
                user_id = payload.get("sub")
                user_role = payload.get("role", "viewer")

        # Collect response status
        response_status = None

        async def send_wrapper(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message.get("status", 0)
            await send(message)

        await self.app(scope, receive, send_wrapper)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        # Log the request
        method = scope.get("method", "?")
        path = scope.get("path", "?")
        logger.info(
            f"AUDIT | {method} {path} | "
            f"user={user_id} role={user_role} | "
            f"status={response_status} duration={duration_ms}ms"
        )


# ── Permission Seeding Utility ────────────────────────────────────

def seed_roles_and_permissions():
    """
    Seed the database with default roles and permissions.
    Called at app startup to ensure RBAC tables are populated.
    Idempotent — safe to call multiple times.
    """
    from backend.repositories.base import get_session
    from backend.models.user import Role, Permission, RolePermission
    from backend.api.permissions import PERMISSIONS, ROLE_PERMISSIONS, RoleName

    with get_session() as db:
        # Seed roles
        for role_enum in RoleName:
            existing = db.query(Role).filter(Role.name == role_enum.value).first()
            if not existing:
                role = Role(
                    name=role_enum.value,
                    description=_ROLE_DESCRIPTIONS.get(role_enum, ""),
                    is_system=True,
                )
                db.add(role)
                logger.info(f"Created role: {role_enum.value}")

        db.flush()

        # Seed permissions
        for perm in PERMISSIONS:
            existing = db.query(Permission).filter(
                Permission.name == perm.name
            ).first()
            if not existing:
                p = Permission(
                    name=perm.name,
                    resource=perm.resource,
                    action=perm.action,
                    description=f"{perm.action} {perm.resource}",
                )
                db.add(p)

        db.flush()

        # Seed role-permission mappings
        for role_enum, perm_names in ROLE_PERMISSIONS.items():
            role = db.query(Role).filter(Role.name == role_enum.value).first()
            if not role:
                continue
            for perm_name in perm_names:
                perm = db.query(Permission).filter(
                    Permission.name == perm_name
                ).first()
                if not perm:
                    continue
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == perm.id,
                ).first()
                if not existing:
                    db.add(RolePermission(
                        role_id=role.id,
                        permission_id=perm.id,
                    ))

        db.flush()
        logger.info("RBAC roles and permissions seeded successfully")


_ROLE_DESCRIPTIONS = {
    RoleName.ADMIN: "Full system access. Can approve critical actions and manage users.",
    RoleName.OPERATOR: "Day-to-day operations. Can approve medium-risk actions.",
    RoleName.VIEWER: "Read-only access across all resources.",
    RoleName.AGENT: "AI agent — can only read and draft. NEVER approve/execute.",
}
