"""
Havilah OS — Test Configuration

Shared fixtures for all test modules.
Uses FastAPI TestClient with in-memory SQLite for speed.
No PostgreSQL required for unit/integration tests.

Note: SQLite doesn't support JSONB/UUID natively, so we patch model types
before table creation to use JSON/Text instead.
"""

import os
import sys
from uuid import UUID

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Override database URL BEFORE importing any backend modules
os.environ["HAVILAH_DB_HOST"] = "localhost"
os.environ["HAVILAH_DB_NAME"] = "havilah_test"
os.environ["HAVILAH_SECRET_KEY"] = "test-secret-key-for-testing-only"

import pytest
from contextlib import contextmanager
from sqlalchemy import create_engine, event, Text, JSON as SA_JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID

from backend.database import Base, get_db, SessionLocal
from backend.main import app
from backend.api.auth import create_access_token, get_password_hash
from backend.repositories.base import get_session as _orig_get_session


def _patch_types_for_sqlite():
    """
    Replace JSONB → JSON and UUID → Text for SQLite compatibility.
    Must be called BEFORE Base.metadata.create_all().
    """
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, JSONB):
                column.type = SA_JSON()
            elif isinstance(column.type, PG_UUID):
                # SQLite doesn't have native UUID — use Text
                column.type = Text()


# ── SQLite In-Memory Test Database ──────────────────────────────

SQLALCHEMY_DATABASE_URL = "sqlite:///file:test_havilah?mode=memory&cache=shared&uri=true"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

# Enable WAL mode for SQLite shared memory
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Patch types for SQLite compatibility
_patch_types_for_sqlite()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """FastAPI dependency override: yields test DB session."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the app's database dependency
app.dependency_overrides[get_db] = override_get_db


# ── Override repositories.base.get_session to use test DB ───────

import backend.repositories.base as _base_module

@contextmanager
def _test_get_session():
    """Context manager for test database sessions."""
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Monkey-patch get_session in the base module
_base_module.get_session = _test_get_session


# ── Test User IDs ──────────────────────────────────────────────

TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000001"
TEST_OPERATOR_ID = "00000000-0000-0000-0000-000000000002"
TEST_VIEWER_ID = "00000000-0000-0000-0000-000000000003"
TEST_AGENT_ID = "00000000-0000-0000-0000-000000000004"


def _seed_test_users():
    """Create test users in the test database."""
    from backend.models.user import User, Role, UserRole
    session = TestingSessionLocal()
    try:
        # Only seed if users table is empty
        if session.query(User).count() == 0:
            # Create roles
            for role_name in ["admin", "operator", "viewer", "agent"]:
                role = Role(name=role_name, description=f"{role_name} role", is_system=True)
                session.add(role)
            session.flush()

            admin_role = session.query(Role).filter(Role.name == "admin").first()
            operator_role = session.query(Role).filter(Role.name == "operator").first()
            viewer_role = session.query(Role).filter(Role.name == "viewer").first()

            # Admin user
            admin = User(
                id=TEST_ADMIN_ID,
                email="admin@havilah.com",
                full_name="Admin User",
                password_hash=get_password_hash("test1234"),
                is_admin=True,
                status="active",
            )
            session.add(admin)
            session.flush()
            session.add(UserRole(user_id=admin.id, role_id=admin_role.id))

            # Operator user
            operator = User(
                id=TEST_OPERATOR_ID,
                email="operator@havilah.com",
                full_name="Operator User",
                password_hash=get_password_hash("test1234"),
                is_admin=False,
                status="active",
            )
            session.add(operator)
            session.flush()
            session.add(UserRole(user_id=operator.id, role_id=operator_role.id))

            # Viewer user
            viewer = User(
                id=TEST_VIEWER_ID,
                email="viewer@havilah.com",
                full_name="Viewer User",
                password_hash=get_password_hash("test1234"),
                is_admin=False,
                status="active",
            )
            session.add(viewer)
            session.flush()
            session.add(UserRole(user_id=viewer.id, role_id=viewer_role.id))

            # Agent user
            agent = User(
                id=TEST_AGENT_ID,
                email="planner-agent@havilah.internal",
                full_name="Planner Agent",
                password_hash=get_password_hash("test1234"),
                is_admin=False,
                status="active",
            )
            session.add(agent)

        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once per test session."""
    Base.metadata.create_all(bind=engine)
    # Note: User seeding is done per-test in test_auth.py where needed,
    # because SQLite doesn't support UUID type natively.
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    """Provide a clean database session for each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client():
    """FastAPI TestClient with test DB."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture()
def admin_token():
    """JWT token for an admin user."""
    return create_access_token(data={
        "sub": TEST_ADMIN_ID,
        "email": "admin@havilah.com",
        "full_name": "Admin User",
        "is_admin": True,
        "role": "admin",
    })


@pytest.fixture()
def operator_token():
    """JWT token for an operator user."""
    return create_access_token(data={
        "sub": TEST_OPERATOR_ID,
        "email": "operator@havilah.com",
        "full_name": "Operator User",
        "is_admin": False,
        "role": "operator",
    })


@pytest.fixture()
def viewer_token():
    """JWT token for a viewer (read-only) user."""
    return create_access_token(data={
        "sub": TEST_VIEWER_ID,
        "email": "viewer@havilah.com",
        "full_name": "Viewer User",
        "is_admin": False,
        "role": "viewer",
    })


@pytest.fixture()
def agent_token():
    """JWT token for an AI agent (restricted permissions)."""
    return create_access_token(data={
        "sub": TEST_AGENT_ID,
        "email": "planner-agent@havilah.internal",
        "full_name": "Planner Agent",
        "is_admin": False,
        "role": "agent",
    })


@pytest.fixture()
def admin_headers(admin_token):
    """Auth headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def operator_headers(operator_token):
    """Auth headers for operator user."""
    return {"Authorization": f"Bearer {operator_token}"}


@pytest.fixture()
def viewer_headers(viewer_token):
    """Auth headers for viewer user."""
    return {"Authorization": f"Bearer {viewer_token}"}


@pytest.fixture()
def agent_headers(agent_token):
    """Auth headers for AI agent."""
    return {"Authorization": f"Bearer {agent_token}"}
