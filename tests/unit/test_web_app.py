"""
Unit tests for web application
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from solairus_intelligence.web.app import (
    SESSION_TTL_MINUTES,
    GenerationRequest,
    cleanup_expired_sessions,
    get_generator,
    sessions,
)


class TestSessionCleanup:
    """Test session cleanup functionality"""

    def test_cleanup_removes_expired_sessions(self):
        """Test cleanup removes expired sessions"""
        sessions.clear()

        expired_time = (datetime.now() - timedelta(minutes=SESSION_TTL_MINUTES + 10)).isoformat()
        sessions["expired-session"] = {
            "created_at": expired_time,
            "in_progress": False,
        }

        valid_time = datetime.now().isoformat()
        sessions["valid-session"] = {
            "created_at": valid_time,
            "in_progress": False,
        }

        removed = cleanup_expired_sessions()

        assert removed == 1
        assert "expired-session" not in sessions
        assert "valid-session" in sessions

    def test_cleanup_handles_invalid_timestamps(self):
        """Test cleanup handles invalid timestamps"""
        sessions.clear()

        sessions["invalid-session"] = {
            "created_at": "invalid-timestamp",
            "in_progress": False,
        }

        removed = cleanup_expired_sessions()

        assert removed == 1
        assert "invalid-session" not in sessions

    def test_cleanup_enforces_max_sessions(self):
        """Test cleanup enforces max sessions limit"""
        sessions.clear()

        for i in range(150):
            sessions[f"session-{i}"] = {
                "created_at": datetime.now().isoformat(),
                "in_progress": False,
            }

        cleanup_expired_sessions()

        assert len(sessions) <= 100


class TestGetGenerator:
    """Test generator initialization"""

    def test_get_generator_creates_instance(self):
        """Test get_generator creates instance"""
        with patch("solairus_intelligence.web.app.generator", None):
            with patch("solairus_intelligence.web.app.SolairusIntelligenceGenerator") as MockGen:
                mock_instance = MagicMock()
                MockGen.return_value = mock_instance

                _ = get_generator()

                MockGen.assert_called_once()


class TestGenerationRequest:
    """Test GenerationRequest model"""

    def test_default_values(self):
        """Test default request values"""
        request = GenerationRequest()
        assert request.test_mode is False

    def test_custom_values(self):
        """Test custom request values"""
        request = GenerationRequest(test_mode=True)
        assert request.test_mode is True


class TestAppConfiguration:
    """Test app configuration"""

    def test_app_title(self):
        """Test app has correct title"""
        from solairus_intelligence.web.app import app

        assert app.title == "Ergo Intelligence Report Generator"

    def test_app_version(self):
        """Test app has version"""
        from solairus_intelligence.web.app import app

        assert app.version == "1.0.0"

    def test_app_has_routes(self):
        """Test app has expected routes"""
        from solairus_intelligence.web.app import app

        routes = [route.path for route in app.routes]

        assert "/" in routes
        assert "/generate" in routes
        assert "/health" in routes
        assert "/status" in routes


class TestRunGeneration:
    """Test run_generation function"""

    @pytest.mark.asyncio
    async def test_run_generation_success(self):
        """Test successful generation updates session"""
        from solairus_intelligence.web.app import run_generation

        sessions.clear()
        session_id = "test-session"
        sessions[session_id] = {
            "in_progress": True,
            "last_run": None,
            "last_report": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
        }

        with patch("solairus_intelligence.web.app.get_generator") as mock_get_gen:
            mock_gen = MagicMock()
            mock_gen.generate_monthly_report = AsyncMock(
                return_value=("/tmp/test_report.docx", {"success": True, "errors": []})
            )
            mock_get_gen.return_value = mock_gen

            await run_generation(session_id, test_mode=True)

            assert sessions[session_id]["in_progress"] is False
            assert sessions[session_id]["last_report"] == "/tmp/test_report.docx"
            assert sessions[session_id]["error"] is None

    @pytest.mark.asyncio
    async def test_run_generation_failure(self):
        """Test failed generation updates session with error"""
        from solairus_intelligence.web.app import run_generation

        sessions.clear()
        session_id = "test-session-fail"
        sessions[session_id] = {
            "in_progress": True,
            "last_run": None,
            "last_report": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
        }

        with patch("solairus_intelligence.web.app.get_generator") as mock_get_gen:
            mock_gen = MagicMock()
            mock_gen.generate_monthly_report = AsyncMock(
                return_value=("/tmp/report.docx", {"success": False, "errors": ["API Error"]})
            )
            mock_get_gen.return_value = mock_gen

            await run_generation(session_id, test_mode=True)

            assert sessions[session_id]["in_progress"] is False
            assert sessions[session_id]["error"] is not None
            assert "API Error" in sessions[session_id]["error"]

    @pytest.mark.asyncio
    async def test_run_generation_exception(self):
        """Test exception during generation updates session"""
        from solairus_intelligence.web.app import run_generation

        sessions.clear()
        session_id = "test-session-exception"
        sessions[session_id] = {
            "in_progress": True,
            "last_run": None,
            "last_report": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
        }

        with patch("solairus_intelligence.web.app.get_generator") as mock_get_gen:
            mock_gen = MagicMock()
            mock_gen.generate_monthly_report = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get_gen.return_value = mock_gen

            await run_generation(session_id, test_mode=True)

            assert sessions[session_id]["in_progress"] is False
            assert sessions[session_id]["error"] == "Connection failed"
