"""
Integration tests for GPC Reliability Tracker API.

These tests run against the deployed Databricks App to verify all endpoints work correctly.
Authentication is handled via Databricks SDK for OAuth token retrieval.
"""
import os
import pytest
import requests
from typing import Optional

# Get the API URL from environment or use default Databricks App URL
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "https://gpc-reliability-api-2638647091718210.aws.databricksapps.com"
)


def get_databricks_token() -> Optional[str]:
    """Get Databricks access token for API authentication."""
    # First check for explicit token
    token = os.environ.get("DATABRICKS_TOKEN")
    if token:
        return token

    # Try to get from SDK
    try:
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.config import Config

        config = Config()
        w = WorkspaceClient(config=config)
        # Get token from the config
        if hasattr(config, 'token') and config.token:
            return config.token
        # Try OAuth
        if config.authenticate:
            headers = config.authenticate()
            if 'Authorization' in headers:
                auth_header = headers['Authorization']
                if auth_header.startswith('Bearer '):
                    return auth_header[7:]
    except Exception as e:
        print(f"Could not get token from SDK: {e}")

    return None


@pytest.fixture(scope="session")
def auth_headers():
    """Get authentication headers for API requests."""
    token = get_databricks_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture(scope="session")
def api_session(auth_headers):
    """Create a requests session with authentication."""
    session = requests.Session()
    session.headers.update(auth_headers)
    session.headers.update({"Content-Type": "application/json"})
    return session


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_health_endpoint(self, api_session):
        """Test /health endpoint returns healthy status."""
        response = api_session.get(f"{API_BASE_URL}/health", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_root_endpoint(self, api_session):
        """Test root endpoint returns API info."""
        response = api_session.get(f"{API_BASE_URL}/", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "GPC Reliability Tracker API"
        assert "endpoints" in data


class TestDashboardAPI:
    """Test dashboard endpoints."""

    def test_dashboard_summary(self, api_session):
        """Test /api/v1/dashboard/summary endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/dashboard/summary", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_dashboard_status_distribution(self, api_session):
        """Test /api/v1/dashboard/status-distribution endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/dashboard/status-distribution", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_dashboard_region_distribution(self, api_session):
        """Test /api/v1/dashboard/region-distribution endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/dashboard/region-distribution", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_dashboard_next_actions(self, api_session):
        """Test /api/v1/dashboard/next-actions endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/dashboard/next-actions", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_dashboard_vendor_performance(self, api_session):
        """Test /api/v1/dashboard/vendor-performance endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/dashboard/vendor-performance", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_dashboard_recent_activity(self, api_session):
        """Test /api/v1/dashboard/recent-activity endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/dashboard/recent-activity", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestProjectsAPI:
    """Test projects endpoints."""

    def test_list_projects(self, api_session):
        """Test GET /api/v1/projects endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_list_projects_with_filters(self, api_session):
        """Test GET /api/v1/projects with filters."""
        params = {"status": "in_progress", "per_page": 5}
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects", params=params, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # All returned projects should have in_progress status
        for project in data["data"]:
            assert project.get("status") == "in_progress"

    def test_list_projects_pagination(self, api_session):
        """Test pagination on projects list."""
        params = {"page": 1, "per_page": 2}
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects", params=params, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert len(data["data"]) <= 2

    def test_get_project_not_found(self, api_session):
        """Test GET /api/v1/projects/:id returns 404 for non-existent project."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects/non-existent-id", timeout=30)
        assert response.status_code == 404


class TestVendorsAPI:
    """Test vendors endpoints."""

    def test_list_vendors(self, api_session):
        """Test GET /api/v1/vendors endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/vendors", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_list_vendors_active_only(self, api_session):
        """Test GET /api/v1/vendors with active_only filter."""
        params = {"active_only": "true"}
        response = api_session.get(f"{API_BASE_URL}/api/v1/vendors", params=params, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # All returned vendors should be active
        for vendor in data["data"]:
            assert vendor.get("is_active") == True

    def test_get_vendor_not_found(self, api_session):
        """Test GET /api/v1/vendors/:id returns 404 for non-existent vendor."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/vendors/non-existent-id", timeout=30)
        assert response.status_code == 404


class TestAlertsAPI:
    """Test alerts endpoints."""

    def test_list_alerts(self, api_session):
        """Test GET /api/v1/alerts endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/alerts", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data

    def test_list_alerts_with_filters(self, api_session):
        """Test GET /api/v1/alerts with severity filter."""
        params = {"severity": "critical"}
        response = api_session.get(f"{API_BASE_URL}/api/v1/alerts", params=params, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # All returned alerts should have critical severity
        for alert in data["data"]:
            assert alert.get("severity") == "critical"

    def test_alert_stats(self, api_session):
        """Test GET /api/v1/alerts/stats endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/alerts/stats", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestMilestonesAPI:
    """Test milestones endpoints."""

    def test_list_milestones(self, api_session):
        """Test GET /api/v1/milestones endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/milestones", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_overdue_milestones(self, api_session):
        """Test GET /api/v1/milestones/overdue endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/milestones/overdue", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_upcoming_milestones(self, api_session):
        """Test GET /api/v1/milestones/upcoming endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/milestones/upcoming", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestGanttAPI:
    """Test Gantt chart endpoints."""

    def test_gantt_data(self, api_session):
        """Test GET /api/v1/gantt endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/gantt", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_gantt_timeline(self, api_session):
        """Test GET /api/v1/gantt/timeline endpoint."""
        response = api_session.get(f"{API_BASE_URL}/api/v1/gantt/timeline", timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestCRUDOperations:
    """Test create, update, delete operations."""

    def test_create_and_delete_vendor(self, api_session):
        """Test creating and deleting a vendor."""
        import uuid
        test_vendor_data = {
            "vendor_name": f"Test Vendor {uuid.uuid4().hex[:8]}",
            "contact_name": "Test Contact",
            "contact_email": "test@example.com",
            "contact_phone": "555-0100",
            "is_active": True
        }

        # Create vendor
        response = api_session.post(
            f"{API_BASE_URL}/api/v1/vendors",
            json=test_vendor_data,
            timeout=30
        )
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        vendor_id = data["data"]["vendor_id"]

        # Verify vendor exists
        response = api_session.get(f"{API_BASE_URL}/api/v1/vendors/{vendor_id}", timeout=30)
        assert response.status_code == 200

        # Delete vendor
        response = api_session.delete(f"{API_BASE_URL}/api/v1/vendors/{vendor_id}", timeout=30)
        assert response.status_code == 200

        # Verify vendor is deleted
        response = api_session.get(f"{API_BASE_URL}/api/v1/vendors/{vendor_id}", timeout=30)
        assert response.status_code == 404

    def test_create_update_delete_project(self, api_session):
        """Test full CRUD cycle for a project."""
        import uuid

        # First, get a vendor to associate with the project
        vendors_response = api_session.get(f"{API_BASE_URL}/api/v1/vendors", timeout=30)
        vendors = vendors_response.json().get("data", [])

        if not vendors:
            pytest.skip("No vendors available for project creation test")

        test_project_data = {
            "project_name": f"Test Project {uuid.uuid4().hex[:8]}",
            "vendor_id": vendors[0]["vendor_id"],
            "region": "Metro",
            "status": "planning",
            "priority": "medium",
            "start_date": "2025-01-01",
            "target_completion_date": "2025-06-30",
            "budget": 100000,
            "description": "Integration test project"
        }

        # Create project
        response = api_session.post(
            f"{API_BASE_URL}/api/v1/projects",
            json=test_project_data,
            timeout=30
        )
        assert response.status_code == 201
        data = response.json()
        project_id = data["data"]["project_id"]

        # Update project
        update_data = {"status": "in_progress", "priority": "high"}
        response = api_session.patch(
            f"{API_BASE_URL}/api/v1/projects/{project_id}",
            json=update_data,
            timeout=30
        )
        assert response.status_code == 200
        updated = response.json()["data"]
        assert updated["status"] == "in_progress"
        assert updated["priority"] == "high"

        # Get project to verify
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects/{project_id}", timeout=30)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "in_progress"

        # Delete project
        response = api_session.delete(f"{API_BASE_URL}/api/v1/projects/{project_id}", timeout=30)
        assert response.status_code == 200

        # Verify deletion
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects/{project_id}", timeout=30)
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_json(self, api_session):
        """Test that invalid JSON returns 400 error."""
        response = api_session.post(
            f"{API_BASE_URL}/api/v1/projects",
            data="not valid json",
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        assert response.status_code == 400

    def test_missing_required_fields(self, api_session):
        """Test that missing required fields returns validation error."""
        response = api_session.post(
            f"{API_BASE_URL}/api/v1/projects",
            json={"project_name": "Test"},  # Missing other required fields
            timeout=30
        )
        assert response.status_code == 400

    def test_invalid_status_filter(self, api_session):
        """Test that invalid filter values are handled gracefully."""
        params = {"status": "invalid_status"}
        response = api_session.get(f"{API_BASE_URL}/api/v1/projects", params=params, timeout=30)
        # Should return 200 with empty results, not crash
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
