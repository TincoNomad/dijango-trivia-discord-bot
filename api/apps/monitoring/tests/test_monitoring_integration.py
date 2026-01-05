"""
Integration tests for monitoring functionality.
Tests logging across different endpoints and scenarios.

This module verifies:
- Request logging for different endpoints
- Error logging and handling
- Authentication logging
- Data logging in requests/responses
- Response time tracking
- Status code handling
"""

import pytest

from api.apps.monitoring.models import ErrorLog, RequestLog
from api.settings import TRIVIA_URL

from .test_base import MonitoringBaseTest


@pytest.mark.django_db
class TestMonitoringIntegration(MonitoringBaseTest):
    """Test cases for monitoring integration"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client):
        """Setup for each test"""
        self.client = api_client
        self.cleanup_logs()
        yield
        self.cleanup_logs()

    @pytest.mark.parametrize(
        "endpoint,method,expected_status",
        [
            ("/api/users/", "GET", 200),
            ("/api/score/", "POST", 200),
            ("/api/nonexistent/", "GET", 404),
        ],
    )
    def test_endpoint_logging(self, endpoint, method, expected_status):
        """
        Verify logging for different endpoints.

        Args:
            endpoint (str): Endpoint URL to test
            method (str): HTTP method (GET, POST)
            expected_status (int): Expected status code

        Verifies:
            - Correct log creation
            - Log fields match request
            - Response time is recorded
        """
        # Act
        response = (
            self.client.get(endpoint)
            if method == "GET"
            else self.client.post(endpoint, {})
        )

        # Assert
        self._assert_log_creation(endpoint, method, response.status_code)

    def _assert_log_creation(self, endpoint, method, status_code):
        """Helper method to validate log creation"""
        if status_code < 400:
            log = RequestLog.objects.filter(path=endpoint).first()
            assert log is not None, f"Log was not created for {endpoint}"
            assert log.method == method
            assert log.status_code == status_code
            assert log.response_time > 0
        else:
            error_log = ErrorLog.objects.filter(path=endpoint).first()
            assert error_log is not None
            assert error_log.error_type == str(status_code)

    def test_authenticated_request_logging(self, test_user, api_client_authenticated):
        """Verify logging for authenticated requests"""
        # Arrange
        endpoint = TRIVIA_URL

        # Act
        api_client_authenticated.get(endpoint)

        # Assert
        log = RequestLog.objects.filter(path__endswith="/api/trivias/").first()
        assert log is not None
        assert log.status_code == 200

    def test_request_with_data_logging(
        self, api_client_authenticated, test_leaderboard
    ):
        """Verify logging for requests with data"""
        # Arrange
        endpoint = "/api/score/"
        test_data = {
            "name": "test",
            "points": 100,
            "discord_channel": test_leaderboard.discord_channel,
        }

        # Act
        api_client_authenticated.post(endpoint, test_data, format="json")

        # Assert
        log = RequestLog.objects.filter(path=endpoint).first()
        assert log is not None
        assert log.request_data == test_data
        assert isinstance(log.response_data, dict)
