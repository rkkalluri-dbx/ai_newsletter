"""
Pytest configuration for integration tests.
"""
import pytest
import os


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "crud: marks tests that perform CRUD operations"
    )


def pytest_report_header(config):
    """Add custom header to test report."""
    api_url = os.environ.get(
        "API_BASE_URL",
        "https://gpc-reliability-api-2638647091718210.aws.databricksapps.com"
    )
    return f"Testing against: {api_url}"


@pytest.fixture(scope="session")
def api_base_url():
    """Fixture providing the API base URL."""
    return os.environ.get(
        "API_BASE_URL",
        "https://gpc-reliability-api-2638647091718210.aws.databricksapps.com"
    )
