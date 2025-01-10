"""Configuration management system."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import toml
from loguru import logger

class ConfigError(Exception):
    """Base class for configuration errors."""
    pass

class Config:
    """Configuration management class.
    
    Handles loading, validation, and access to configuration settings.
    Supports environment variable overrides and secure handling of
    sensitive data.
    """
    
    def __init__(
        self,
        config_file: Path,
        env_prefix: str = "GPTME_",
        auto_create: bool = True
    ):
        """Initialize configuration manager.
        
        Args:
            config_file: Path to TOML config file
            env_prefix: Prefix for environment variables
            auto_create: Whether to create config file if missing
        """
        self.config_file = config_file
        self.env_prefix = env_prefix
        self.data: Dict[str, Any] = {}
        
        if not config_file.exists() and auto_create:
            self._create_default_config()
        
        self.load()
        
    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            "gptme": {
                "default_model": "gemini-2-0-experimental",
                "worker_model": "gemini-2-0-experimental",
                "supervisor_model": "gemini-2-0-flash-thinking-exp"
            },
            "env": {
                "GEMINI_API_KEY": {"env": "GEMINI_API_KEY"},
                "ANTHROPIC_API_KEY": {"env": "ANTHROPIC_API_KEY"}
            },
            "workflow": {
                "parallel_tasks": 3,
                "task_timeout": 300,
                "retry_attempts": 3,
                "quality_check_frequency": 5
            },
            "security": {
                "allow_file_write": True,
                "allowed_directories": ["src", "tests"],
                "restricted_files": ["config/*.toml", "secrets.env"]
            },
            "logging": {
                "level": "info",
                "format": "{timestamp} - {level} - {message}",
                "file": "gptme.log",
                "rotate": True,
                "max_size": 10485760,
                "backup_count": 5
            }
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            toml.dump(default_config, f)
        
        logger.info(f"Created default configuration at {self.config_file}")
    
    def load(self) -> None:
        """Load configuration from file and environment."""
        try:
            # Load from file
            self.data = toml.load(self.config_file)
            
            # Apply environment variable overrides
            self._apply_env_overrides()
            
            # Validate configuration
            self._validate_config()
            
            logger.info(f"Loaded configuration from {self.config_file}")
            
        except toml.TomlDecodeError as e:
            raise ConfigError(f"Failed to parse config file: {e}")
        except OSError as e:
            raise ConfigError(f"Failed to read config file: {e}")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # Convert GPTME_SECTION_KEY to section.key
                config_key = key[len(self.env_prefix):].lower().replace("_", ".")
                self.set(config_key, value)
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        required_sections = ["gptme", "workflow", "security", "logging"]
        
        for section in required_sections:
            if section not in self.data:
                raise ConfigError(f"Missing required section: {section}")
        
        # Validate workflow settings
        workflow = self.data["workflow"]
        if not isinstance(workflow.get("parallel_tasks", 0), int):
            raise ConfigError("workflow.parallel_tasks must be an integer")
        if not isinstance(workflow.get("task_timeout", 0), int):
            raise ConfigError("workflow.task_timeout must be an integer")
        
        # Validate security settings
        security = self.data["security"]
        if not isinstance(security.get("allowed_directories", []), list):
            raise ConfigError("security.allowed_directories must be a list")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Dot-notation key (e.g. "workflow.parallel_tasks")
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        try:
            value = self.data
            for part in key.split("."):
                value = value[part]
            return value
        except KeyError:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Dot-notation key
            value: Value to set
        """
        parts = key.split(".")
        current = self.data
        
        # Navigate to the correct nested dict
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the value
        current[parts[-1]] = value
    
    def save(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                toml.dump(self.data, f)
            logger.info(f"Saved configuration to {self.config_file}")
        except OSError as e:
            raise ConfigError(f"Failed to save config file: {e}")
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Section configuration dict
        """
        if section not in self.data:
            raise ConfigError(f"Section not found: {section}")
        return dict(self.data[section])
    
    def is_file_allowed(self, file_path: Path) -> bool:
        """Check if file operations are allowed on given path.
        
        Args:
            file_path: Path to check
            
        Returns:
            Whether file operations are allowed
        """
        if not self.get("security.allow_file_write", False):
            return False
            
        allowed_dirs = self.get("security.allowed_directories", [])
        restricted_files = self.get("security.restricted_files", [])
        
        # Check if path matches any restricted pattern
        for pattern in restricted_files:
            if file_path.match(pattern):
                return False
        
        # Check if path is in allowed directory
        for allowed_dir in allowed_dirs:
            if str(file_path).startswith(allowed_dir):
                return True
        
        return False
