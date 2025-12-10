"""
Integration tests for the Web API
Tests the FastAPI endpoints and session management
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient


class TestWebIntegration:
    """Integration tests for the web application"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked generator"""
        with patch.dict('os.environ', {'AI_ENABLED': 'false'}):
            with patch('solairus_intelligence.web.app.generator') as mock_gen:
                mock_gen.generate_monthly_report = AsyncMock(
                    return_value=("/tmp/test_report.docx", {"success": True, "errors": []})
                )
                from solairus_intelligence.web.app import app
                return TestClient(app)

    def test_home_page_loads(self, client):
        """Test that the home page loads successfully"""
        response = client.get("/")

        assert response.status_code == 200
        assert "Ergo Intelligence Report" in response.text

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_generate_endpoint_returns_session(self, client):
        """Test that generate endpoint returns session ID"""
        response = client.post(
            "/generate",
            json={"test_mode": False, "focus_areas": []}
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["status"] == "processing"

    def test_status_endpoint_not_found(self, client):
        """Test status endpoint with invalid session"""
        response = client.get("/status/invalid-session-id")

        assert response.status_code == 404

    def test_download_not_found(self, client):
        """Test download endpoint with non-existent file"""
        response = client.get("/download/nonexistent.docx")

        assert response.status_code == 404


class TestSessionManagement:
    """Tests for session management and cleanup"""

    def test_session_creation(self):
        """Test that sessions are created properly"""
        from solairus_intelligence.web.app import sessions, cleanup_expired_sessions
        from datetime import datetime

        # Clear existing sessions
        sessions.clear()

        # Add a test session
        test_session_id = "test-session-123"
        sessions[test_session_id] = {
            "in_progress": False,
            "last_run": None,
            "last_report": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
        }

        assert test_session_id in sessions
        assert sessions[test_session_id]["in_progress"] == False

        # Clean up
        sessions.clear()

    def test_session_cleanup_removes_expired(self):
        """Test that cleanup removes expired sessions"""
        from solairus_intelligence.web.app import sessions, cleanup_expired_sessions
        from datetime import datetime, timedelta

        sessions.clear()

        # Add an expired session (2 hours old)
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        sessions["expired-session"] = {
            "in_progress": False,
            "created_at": old_time,
        }

        # Add a valid session
        sessions["valid-session"] = {
            "in_progress": False,
            "created_at": datetime.now().isoformat(),
        }

        removed = cleanup_expired_sessions()

        assert removed == 1
        assert "expired-session" not in sessions
        assert "valid-session" in sessions

        # Clean up
        sessions.clear()
