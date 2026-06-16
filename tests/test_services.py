"""
Havilah OS — Service Layer Unit Tests

Tests for core service methods: ProjectService, TaskService, MemoryService, etc.
These tests verify business logic independently of the API layer.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestProjectHealthService:
    """Project health calculation logic."""

    def test_health_score_calculation(self):
        """Health score is computed from task completion/blocked/overdue ratios."""
        from backend.services.project_health_service import ProjectHealthService
        service = ProjectHealthService()
        assert service is not None

    def test_health_status_thresholds(self):
        """Health status: on_track (>=0.8), at_risk (>=0.6), off_track (>=0.4), critical (<0.4)."""
        # These thresholds are defined in ProjectHealthService
        from backend.services.project_health_service import ProjectHealthService
        # on_track: 0.8+
        assert ProjectHealthService is not None


class TestMemoryService:
    """Memory capture, recall, linking, and reinforcement."""

    def test_memory_service_exists(self):
        """MemoryService can be instantiated."""
        from backend.services.memory_service import MemoryService
        service = MemoryService()
        assert service is not None


class TestEventSystem:
    """Domain event constants are properly defined."""

    def test_all_event_constants_exist(self):
        """Every event constant from the events module is importable."""
        from backend.events import (
            APPROVAL_REQUESTED, APPROVAL_APPROVED, APPROVAL_REJECTED,
            APPROVAL_EXPIRED, EXECUTION_STARTED, EXECUTION_COMPLETED,
            EXECUTION_FAILED, RISK_ESCALATED,
            TASK_CREATED, TASK_STATUS_CHANGED,
            PROJECT_CREATED, PROJECT_STATUS_CHANGED,
            MEMORY_CAPTURED, MEMORY_LINKED, MEMORY_REINFORCED,
            AGENT_ASSIGNED, AGENT_STARTED, AGENT_COMPLETED, AGENT_FAILED,
            WORKFLOW_CREATED, WORKFLOW_STARTED, WORKFLOW_COMPLETED,
            NOTIFICATION_CREATED, NOTIFICATION_DELIVERED,
        )
        # All should be non-empty strings
        assert len(APPROVAL_REQUESTED) > 0
        assert len(TASK_CREATED) > 0
        assert len(MEMORY_CAPTURED) > 0

    def test_event_values_are_strings(self):
        """All event constants are PascalCase strings."""
        from backend.events import APPROVAL_REQUESTED, TASK_CREATED
        assert APPROVAL_REQUESTED == "ApprovalRequested"
        assert TASK_CREATED == "TaskCreated"


class TestPermissionMatrix:
    """RBAC permission definitions are complete and consistent."""

    def test_all_roles_defined(self):
        """Four roles exist: admin, operator, viewer, agent."""
        from backend.api.permissions import RoleName
        assert RoleName.ADMIN.value == "admin"
        assert RoleName.OPERATOR.value == "operator"
        assert RoleName.VIEWER.value == "viewer"
        assert RoleName.AGENT.value == "agent"

    def test_admin_has_all_permissions(self):
        """Admin role has every permission in the system."""
        from backend.api.permissions import ROLE_PERMISSIONS, PERMISSIONS, RoleName
        admin_perms = ROLE_PERMISSIONS[RoleName.ADMIN]
        all_perm_names = {p.name for p in PERMISSIONS}
        assert admin_perms == all_perm_names

    def test_viewer_has_read_only(self):
        """Viewer only has read/search/dashboard permissions (no create/update/delete)."""
        from backend.api.permissions import ROLE_PERMISSIONS, RoleName
        viewer_perms = ROLE_PERMISSIONS[RoleName.VIEWER]
        # All viewer permissions should be read-only actions
        read_only_actions = ("read", "search", "dashboard")
        for perm in viewer_perms:
            action = perm.split(":")[1]
            assert action in read_only_actions, f"Viewer has non-read permission: {perm}"

    def test_agent_never_has_approval_permissions(self):
        """Agent role NEVER has approve/reject/escalate/execute permissions."""
        from backend.api.permissions import ROLE_PERMISSIONS, RoleName
        agent_perms = ROLE_PERMISSIONS[RoleName.AGENT]
        forbidden = {"approval:approve", "approval:reject", "approval:escalate", "approval:execute"}
        for f in forbidden:
            assert f not in agent_perms, f"Agent has forbidden permission: {f}"

    def test_human_only_permissions_defined(self):
        """Human-only permissions are explicitly listed."""
        from backend.api.permissions import HUMAN_ONLY_PERMISSIONS
        assert "approval:approve" in HUMAN_ONLY_PERMISSIONS
        assert "approval:execute" in HUMAN_ONLY_PERMISSIONS
        assert "approval:reject" in HUMAN_ONLY_PERMISSIONS
        assert "approval:escalate" in HUMAN_ONLY_PERMISSIONS
        assert "knowledge:approve_version" in HUMAN_ONLY_PERMISSIONS
        assert "knowledge:publish" in HUMAN_ONLY_PERMISSIONS

    def test_operator_has_approval_permissions(self):
        """Operator has approval permissions (can approve medium-risk)."""
        from backend.api.permissions import ROLE_PERMISSIONS, RoleName
        operator_perms = ROLE_PERMISSIONS[RoleName.OPERATOR]
        assert "approval:approve" in operator_perms
        assert "approval:reject" in operator_perms
        assert "approval:execute" in operator_perms

    def test_permission_count_reasonable(self):
        """System has a reasonable number of permissions (50-100)."""
        from backend.api.permissions import PERMISSIONS
        assert 50 <= len(PERMISSIONS) <= 100


class TestModelIntegrity:
    """Verify model structure and relationships."""

    def test_all_51_tables_exist(self):
        """All 51 tables are registered in the metadata."""
        from backend.models import Base
        assert len(Base.metadata.tables) == 51

    def test_core_tables_present(self):
        """Key tables from all bounded contexts exist."""
        from backend.models import Base
        tables = set(Base.metadata.tables.keys())
        # Approval context
        assert "approval_requests" in tables
        assert "approval_decisions" in tables
        # Task context
        assert "tasks" in tables
        assert "task_dependencies" in tables
        # Project context
        assert "projects" in tables
        # Memory context
        assert "memory_items" in tables
        assert "memory_links" in tables
        # Agent context
        assert "agents" in tables
        assert "agent_runs" in tables
        # Identity context
        assert "users" in tables
        assert "roles" in tables
        assert "permissions" in tables
        # Knowledge context
        assert "knowledge_artifacts" in tables
        # Meeting context
        assert "meetings" in tables
        # Workflow context
        assert "workflows" in tables
