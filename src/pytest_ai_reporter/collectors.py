"""Data collectors for gathering test environment information."""

import os
import sys
import platform
import pkg_resources
from typing import Dict, Any
import pytest
from .models import TestEnvironment

class MetadataCollector:
    """Collects metadata about the test environment."""
    
    @staticmethod
    def collect() -> Dict[str, Any]:
        """Collect all relevant metadata."""
        return {
            "environment": MetadataCollector.collect_environment(),
            "git": MetadataCollector.collect_git_info(),
            "coverage": MetadataCollector.collect_coverage_info(),
            "runtime": MetadataCollector.collect_runtime_info()
        }
    
    @staticmethod
    def collect_environment() -> TestEnvironment:
        """Collect information about the test environment."""
        return TestEnvironment(
            python_version=platform.python_version(),
            platform=platform.platform(),
            packages=MetadataCollector._get_installed_packages(),
            pytest_version=pytest.__version__,
            pwd=os.getcwd(),
            username=os.getenv("USER", "unknown"),
            env_vars=MetadataCollector._get_relevant_env_vars()
        )
    
    @staticmethod
    def _get_installed_packages() -> Dict[str, str]:
        """Get list of installed Python packages and versions."""
        return {
            pkg.key: pkg.version
            for pkg in pkg_resources.working_set
        }
    
    @staticmethod
    def _get_relevant_env_vars() -> Dict[str, str]:
        """Get relevant environment variables (filtering out sensitive ones)."""
        relevant_prefixes = {"PYTEST_", "PYTHON", "PATH", "VIRTUAL_ENV", "CI"}
        return {
            key: value
            for key, value in os.environ.items()
            if any(key.startswith(prefix) for prefix in relevant_prefixes)
        }
    
    @staticmethod
    def collect_git_info() -> Dict[str, Any]:
        """Collect Git repository information if available."""
        try:
            import git
            repo = git.Repo(search_parent_directories=True)
            return {
                "branch": repo.active_branch.name,
                "commit": repo.head.object.hexsha,
                "commit_message": repo.head.object.message.strip(),
                "dirty": repo.is_dirty(),
                "remotes": [
                    {
                        "name": remote.name,
                        "url": remote.url
                    }
                    for remote in repo.remotes
                ]
            }
        except (ImportError, git.InvalidGitRepositoryError):
            return {}
    
    @staticmethod
    def collect_coverage_info() -> Dict[str, Any]:
        """Collect code coverage information if available."""
        try:
            import coverage
            cov = coverage.Coverage()
            return {
                "version": coverage.__version__,
                "config": cov.config.__dict__
            }
        except ImportError:
            return {}
    
    @staticmethod
    def collect_runtime_info() -> Dict[str, Any]:
        """Collect runtime information."""
        return {
            "argv": sys.argv,
            "executable": sys.executable,
            "cpu_count": os.cpu_count(),
            "max_workers": os.cpu_count() * 2 if os.cpu_count() else None,
            "encoding": sys.getfilesystemencoding(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            }
        }
