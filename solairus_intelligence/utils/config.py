"""
Environment-aware Configuration for Solairus Intelligence
Automatically detects and adapts to local development, Docker, or cloud environments
"""

import os
import platform
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class EnvironmentConfig:
    """Configuration that adapts to the runtime environment"""

    output_dir: Path
    is_cloud: bool
    is_docker: bool
    is_local: bool
    platform_name: str
    # AI configuration
    anthropic_api_key: Optional[str] = None
    ai_enabled: bool = True
    ai_model: str = "claude-opus-4-5-20251101"

    @classmethod
    def detect(cls) -> 'EnvironmentConfig':
        """
        Intelligently detect the runtime environment and configure paths

        Detection logic:
        1. Cloud Run: Check for K_SERVICE environment variable
        2. Docker: Check for /.dockerenv or docker in cgroup
        3. Local: Default fallback with platform-specific paths
        """
        # Detect cloud environment
        is_cloud = os.getenv('K_SERVICE') is not None or os.getenv('GAE_ENV') is not None

        # Detect Docker
        is_docker = os.path.exists('/.dockerenv') or cls._is_in_docker()

        # Determine if local development
        is_local = not is_cloud and not is_docker

        # Get platform name
        platform_name = platform.system()

        # Determine output directory based on environment
        if is_cloud or is_docker:
            # Use /mnt/user-data/outputs in cloud/container environments
            output_dir = Path("/mnt/user-data/outputs")
        else:
            # Local development: use project root directory
            # Path(__file__) is utils/config.py, so .parents[2] reaches project root
            project_root = Path(__file__).parents[2]
            output_dir = project_root / "outputs"

        # Ensure directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load AI configuration from environment
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        ai_enabled = os.getenv('AI_ENABLED', 'true').lower() == 'true'
        ai_model = os.getenv('AI_MODEL', 'claude-opus-4-5-20251101')

        # Disable AI if no API key provided
        if not anthropic_api_key and ai_enabled:
            ai_enabled = False

        return cls(
            output_dir=output_dir,
            is_cloud=is_cloud,
            is_docker=is_docker,
            is_local=is_local,
            platform_name=platform_name,
            anthropic_api_key=anthropic_api_key,
            ai_enabled=ai_enabled,
            ai_model=ai_model
        )

    @staticmethod
    def _is_in_docker() -> bool:
        """Check if running inside Docker container"""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except (FileNotFoundError, PermissionError):
            return False

    def get_report_path(self, filename: str) -> Path:
        """Get full path for a report file"""
        return self.output_dir / filename

    def get_status_file_path(self) -> Path:
        """Get path for the status tracking file"""
        return self.output_dir / "last_run_status.json"

    def __str__(self) -> str:
        """String representation for logging"""
        env_type = "Cloud" if self.is_cloud else "Docker" if self.is_docker else "Local"
        return f"{env_type} environment on {self.platform_name} | Output: {self.output_dir}"


# Global configuration instance - initialized once when module is imported
ENV_CONFIG = EnvironmentConfig.detect()


def get_config() -> EnvironmentConfig:
    """Get the current environment configuration"""
    return ENV_CONFIG


def get_output_dir() -> Path:
    """Convenience function to get the output directory"""
    return ENV_CONFIG.output_dir


def get_report_path(filename: str) -> Path:
    """Convenience function to get a report file path"""
    return ENV_CONFIG.get_report_path(filename)


def get_status_file_path() -> Path:
    """Convenience function to get the status file path"""
    return ENV_CONFIG.get_status_file_path()


# Print configuration on import for transparency
if __name__ != "__main__":
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Environment detected: {ENV_CONFIG}")
