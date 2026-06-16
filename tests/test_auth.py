"""
Havilah OS — Authentication Tests

Tests for JWT auth, login, registration, and RBAC permission enforcement.
Core principle: AI agents can NEVER approve/execute — verified here.
"""

import pytest


class TestAuthRoutes:
    """Authentication endpoints: login, register, me, change-password."""

    def test_register_first_user_as_admin(self, client, db_session):
        """First registered user should automatically be admin."""
        response = client.post("/api/auth/register", json={
            "email": "founder@havilah.com",
            "full_name": "Havilah Founder",
            "password": "SecurePass123",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["is_admin"] is True
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_second_user_as_operator(self, client, db_session):
        """Second registered user should be operator (not admin)."""
        # Register admin first
        client.post("/api/auth/register", json={
            "email": "admin@havilah.com",
            "full_name": "Admin User",
            "password": "SecurePass123",
        })
        # Register second user
        response = client.post("/api/auth/register", json={
            "email": "operator@havilah.com",
            "full_name": "Operator User",
            "password": "SecurePass456",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["is_admin"] is False

    def test_register_duplicate_email_fails(self, client, db_session):
        """Cannot register with an already-used email."""
        client.post("/api/auth/register", json={
            "email": "dup@havilah.com",
            "full_name": "First User",
            "password": "SecurePass123",
        })
        response = client.post("/api/auth/register", json={
            "email": "dup@havilah.com",
            "full_name": "Second User",
            "password": "SecurePass456",
        })
        assert response.status_code == 409

    def test_login_success(self, client, db_session):
        """Login with correct credentials returns token."""
        client.post("/api/auth/register", json={
            "email": "login@havilah.com",
            "full_name": "Login User",
            "password": "SecurePass123",
        })
        response = client.post("/api/auth/token", json={
            "email": "login@havilah.com",
            "password": "SecurePass123",
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password_fails(self, client, db_session):
        """Login with wrong password returns 401."""
        client.post("/api/auth/register", json={
            "email": "wrong@havilah.com",
            "full_name": "Wrong Pass",
            "password": "SecurePass123",
        })
        response = client.post("/api/auth/token", json={
            "email": "wrong@havilah.com",
            "password": "WrongPassword",
        })
        assert response.status_code == 401

    def test_login_nonexistent_user_fails(self, client, db_session):
        """Login with non-existent email returns 401."""
        response = client.post("/api/auth/token", json={
            "email": "nobody@havilah.com",
            "password": "Whatever123",
        })
        assert response.status_code == 401

    def test_get_me_with_valid_token(self, client, admin_headers):
        """GET /api/auth/me returns current user info."""
        response = client.get("/api/auth/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@havilah.com"
        assert data["role"] == "admin"

    def test_get_me_without_token_fails(self, client):
        """GET /api/auth/me without token returns 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401


class TestRBACPermissionEnforcement:
    """RBAC: Role-based access control enforcement across endpoints."""

    def test_no_token_returns_401(self, client):
        """All /api/* routes (except auth) require a token."""
        response = client.get("/api/projects/")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Invalid JWT token returns 401."""
        response = client.get(
            "/api/projects/",
            headers={"Authorization": "Bearer invalid-token-here"},
        )
        assert response.status_code == 401

    def test_admin_can_create_project(self, client, admin_headers):
        """Admin user can create a project."""
        response = client.post(
            "/api/projects/",
            headers=admin_headers,
            json={"name": "Admin Project", "description": "Created by admin"},
        )
        assert response.status_code == 201

    def test_operator_can_create_project(self, client, operator_headers):
        """Operator can create a project (has project:create permission)."""
        response = client.post(
            "/api/projects/",
            headers=operator_headers,
            json={"name": "Operator Project", "description": "Created by operator"},
        )
        assert response.status_code == 201

    def test_viewer_cannot_create_project(self, client, viewer_headers):
        """Viewer cannot create a project (no project:create permission)."""
        response = client.post(
            "/api/projects/",
            headers=viewer_headers,
            json={"name": "Viewer Project", "description": "Should fail"},
        )
        assert response.status_code == 403

    def test_viewer_can_read_projects(self, client, viewer_headers):
        """Viewer can read projects (has project:read permission)."""
        response = client.get("/api/projects/", headers=viewer_headers)
        assert response.status_code == 200

    def test_viewer_cannot_update_project_status(self, client, viewer_headers):
        """Viewer cannot change project status (no project:update_status)."""
        # First create a project with admin
        create_resp = client.post(
            "/api/projects/",
            headers=client.headers if hasattr(client, 'headers') else {},
            json={"name": "Test Project"},
        )
        # Even if project doesn't exist, viewer should get 403, not 401
        response = client.patch(
            "/api/projects/00000000-0000-0000-0000-000000000001/status",
            headers=viewer_headers,
            json={"status": "completed"},
        )
        assert response.status_code == 403


class TestAgentRestrictions:
    """
    CRITICAL: Verify AI agents can NEVER approve/execute.
    These tests enforce the core architectural principle.
    """

    def test_agent_can_create_approval_request(self, client, agent_headers):
        """Agents CAN create approval requests (draft state)."""
        response = client.post(
            "/api/approvals/",
            headers=agent_headers,
            json={
                "action_type": "send_email",
                "summary": "Agent proposes sending email to client",
                "risk_level": "medium",
            },
        )
        assert response.status_code == 201

    def test_agent_can_read_approvals(self, client, agent_headers):
        """Agents CAN read approval requests."""
        response = client.get("/api/approvals/", headers=agent_headers)
        assert response.status_code == 200

    def test_agent_cannot_approve(self, client, agent_headers):
        """Agents CANNOT approve — HUMAN-ONLY permission."""
        response = client.post(
            "/api/approvals/00000000-0000-0000-0000-000000000001/approve",
            headers=agent_headers,
            json={"reason": "Agent trying to approve"},
        )
        assert response.status_code == 403
        assert "agent" in response.json()["detail"].lower() or "human" in response.json()["detail"].lower()

    def test_agent_cannot_reject(self, client, agent_headers):
        """Agents CANNOT reject — HUMAN-ONLY permission."""
        response = client.post(
            "/api/approvals/00000000-0000-0000-0000-000000000001/reject",
            headers=agent_headers,
            json={"reason": "Agent trying to reject"},
        )
        assert response.status_code == 403

    def test_agent_cannot_execute(self, client, agent_headers):
        """Agents CANNOT execute — HUMAN-ONLY permission."""
        response = client.post(
            "/api/approvals/00000000-0000-0000-0000-000000000001/execute",
            headers=agent_headers,
            json={"result": {"status": "done"}},
        )
        assert response.status_code == 403

    def test_agent_cannot_escalate(self, client, agent_headers):
        """Agents CANNOT escalate — HUMAN-ONLY permission."""
        response = client.post(
            "/api/approvals/00000000-0000-0000-0000-000000000001/escalate",
            headers=agent_headers,
            json={
                "escalated_to": "00000000-0000-0000-0000-000000000099",
                "reason": "Agent trying to escalate",
            },
        )
        assert response.status_code == 403

    def test_agent_cannot_approve_knowledge(self, client, agent_headers):
        """Agents CANNOT approve knowledge versions — HUMAN-ONLY."""
        response = client.post(
            "/api/knowledge/00000000-0000-0000-0000-000000000001/versions/00000000-0000-0000-0000-000000000002/approve",
            headers=agent_headers,
            json={"approved_by": "00000000-0000-0000-0000-000000000004"},
        )
        assert response.status_code == 403

    def test_agent_cannot_publish_knowledge(self, client, agent_headers):
        """Agents CANNOT publish knowledge — HUMAN-ONLY."""
        response = client.post(
            "/api/knowledge/00000000-0000-0000-0000-000000000001/publish",
            headers=agent_headers,
        )
        assert response.status_code == 403

    def test_agent_can_draft_content(self, client, agent_headers):
        """Agents CAN create content drafts (they're supposed to draft)."""
        response = client.post(
            "/api/content/drafts",
            headers=agent_headers,
            json={
                "title": "Agent Draft",
                "content_type": "article",
                "content": "AI-generated draft content",
            },
        )
        # May fail if DB not available, but should NOT fail with 403
        assert response.status_code in (201, 200, 409, 500)  # Not 403

    def test_operator_can_approve(self, client, operator_headers):
        """Operators CAN approve — they have human approval authority."""
        # This will fail with 404/409 because the approval doesn't exist,
        # but should NOT fail with 403 (permission denied)
        response = client.post(
            "/api/approvals/00000000-0000-0000-0000-000000000001/approve",
            headers=operator_headers,
            json={"reason": "Operator approves"},
        )
        # 403 would mean permission denied — that's wrong for operators
        # 404/409 means the approval doesn't exist — that's expected
        assert response.status_code != 403

    def test_admin_can_execute(self, client, admin_headers):
        """Admin CAN execute — has all permissions."""
        response = client.post(
            "/api/approvals/00000000-0000-0000-0000-000000000001/execute",
            headers=admin_headers,
            json={"result": {"status": "executed"}},
        )
        # Should NOT be 403 (permission denied)
        assert response.status_code != 403
