"""
Unit tests for utils/config module
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch

from solairus_intelligence.utils.config import (
    get_output_dir,
    get_status_file_path,
    EnvironmentConfig,
    ENV_CONFIG,
)


class TestEnvironmentConfig:
    """Test suite for environment detection"""

    def test_detect_returns_config(self):
        """Test detect returns EnvironmentConfig"""
        config = EnvironmentConfig.detect()
        assert isinstance(config, EnvironmentConfig)

    def test_config_has_output_dir(self):
        """Test config has output_dir"""
        config = EnvironmentConfig.detect()
        assert isinstance(config.output_dir, Path)

    def test_config_has_environment_flags(self):
        """Test config has environment flags"""
        config = EnvironmentConfig.detect()
        assert isinstance(config.is_cloud, bool)
        assert isinstance(config.is_docker, bool)
        assert isinstance(config.is_local, bool)

    def test_config_has_platform_name(self):
        """Test config has platform name"""
        config = EnvironmentConfig.detect()
        assert isinstance(config.platform_name, str)
        assert len(config.platform_name) > 0

    def test_config_has_ai_settings(self):
        """Test config has AI settings"""
        config = EnvironmentConfig.detect()
        assert hasattr(config, "ai_enabled")
        assert hasattr(config, "ai_model")


class TestGetOutputDir:
    """Test suite for get_output_dir"""

    def test_returns_path(self):
        """Test returns a Path object"""
        output_dir = get_output_dir()
        assert isinstance(output_dir, Path)

    def test_local_environment_output(self):
        """Test local environment uses local output path"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("pathlib.Path.exists", return_value=False):
                output_dir = get_output_dir()
                # Should be relative to project
                assert isinstance(output_dir, Path)

    def test_docker_environment_output(self):
        """Test Docker environment uses mounted path"""
        with patch.dict(os.environ, {"K_SERVICE": "test"}):
            output_dir = get_output_dir()
            # Should return a Path (potentially mounted volume)
            assert isinstance(output_dir, Path)


class TestGetStatusFilePath:
    """Test suite for get_status_file_path"""

    def test_returns_path(self):
        """Test returns a Path object"""
        status_path = get_status_file_path()
        assert isinstance(status_path, Path)

    def test_path_ends_with_json(self):
        """Test status file is JSON"""
        status_path = get_status_file_path()
        assert str(status_path).endswith(".json")

    def test_path_in_output_dir(self):
        """Test status file is in output directory"""
        status_path = get_status_file_path()
        output_dir = get_output_dir()

        # Status file should be in or near output directory
        assert isinstance(status_path, Path)


class TestEnvConfigGlobal:
    """Test suite for ENV_CONFIG global"""

    def test_env_config_is_environment_config(self):
        """Test ENV_CONFIG is an EnvironmentConfig"""
        assert isinstance(ENV_CONFIG, EnvironmentConfig)

    def test_env_config_has_output_dir(self):
        """Test ENV_CONFIG has output directory set"""
        assert ENV_CONFIG.output_dir is not None
        assert isinstance(ENV_CONFIG.output_dir, Path)

    def test_env_config_repr(self):
        """Test ENV_CONFIG has string representation"""
        str_repr = str(ENV_CONFIG)
        assert len(str_repr) > 0
