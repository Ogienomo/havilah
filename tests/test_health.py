"""
Havilah OS — Health & System Endpoint Tests

Tests for the root health check and system info endpoints.
These are the only truly public endpoints.
"""

import pytest


class TestHealthEndpoints:
    """System health and info endpoints — no auth required."""

    def test_root_returns_system_info(self, client):
        """GET / returns system info with principle statement."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Havilah OS"
        assert data["status"] == "running"
        assert "principle" in data
        assert "auth" in data

    def test_health_check(self, client):
        """GET /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_openapi_schema_available(self, client):
        """GET /openapi.json returns the OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        # Verify key routes are in the schema
        assert "/api/approvals/" in data["paths"]
        assert "/api/tasks/" in data["paths"]
        assert "/api/auth/token" in data["paths"]

    def test_docs_available(self, client):
        """GET /docs returns the Swagger UI."""
        response = client.get("/docs")
        assert response.status_code == 200
