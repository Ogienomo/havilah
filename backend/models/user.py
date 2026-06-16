"""
Havilah OS — Identity & Access Domain Model

Entities: User, Role, Permission, UserRole, RolePermission

Combines RBAC (broad access) + ABAC (contextual checks).
"""

from sqlalchemy import Column, Text, ForeignKey, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from backend.database import Base
from backend.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, MetadataMixin, Base):
    __tablename__ = "users"

    email = Column(Text, nullable=False, unique=True)
    full_name = Column(Text, nullable=False)
    password_hash = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="active")  # active, suspended, deactivated
    is_admin = Column(Boolean, nullable=False, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    whatsapp_id = Column(Text, nullable=True, unique=True)

    # ── Relationships ─────────────────────────────────────────
    roles = relationship("UserRole", back_populates="user", lazy="selectin")


class Role(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name = Column(Text, nullable=False, unique=True)  # admin, operator, viewer, agent
    description = Column(Text)
    is_system = Column(Boolean, nullable=False, default=False)

    # ── Relationships ─────────────────────────────────────────
    permissions = relationship("RolePermission", back_populates="role", lazy="selectin")
    users = relationship("UserRole", back_populates="role", lazy="selectin")


class Permission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "permissions"

    name = Column(Text, nullable=False, unique=True)  # approval:approve, task:create, memory:read
    resource = Column(Text, nullable=False)  # approval, task, project, memory, etc.
    action = Column(Text, nullable=False)  # create, read, update, delete, approve, execute
    description = Column(Text)

    # ── Relationships ─────────────────────────────────────────
    roles = relationship("RolePermission", back_populates="permission")


class UserRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)

    # ── Relationships ─────────────────────────────────────────
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="users")


class RolePermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)

    # ── Relationships ─────────────────────────────────────────
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="roles")
