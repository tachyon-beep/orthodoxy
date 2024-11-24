"""Configuration management for Magic: The Gathering card filtering application.

This module provides configuration handling for the card filtering application,
including version management, file operations settings, schema definitions,
filter configurations, and logging preferences.

Key features:
- Version compatibility checking with semantic versioning
- Configuration loading from YAML/JSON files with validation
- Environment variable support with automatic type conversion
- Validation of configuration values using Pydantic
- Default configuration management with field validation
- Serialization/deserialization of config data with type safety

The module uses Pydantic for robust data validation and provides two main classes:
- ConfigVersion: Handles semantic versioning and compatibility checks
- CardFilterConfig: Main configuration class with all application settings

Configuration can be loaded from:
- Environment variables (prefixed with CARD_FILTER_)
- YAML files (with schema validation)
- JSON files (with type checking)

Example usage:
    Basic config loading:
    >>> config = load_config()
    >>> print(config.buffer_size)
    8192

    Loading from file with version check:
    >>> config = CardFilterConfig()
    >>> config.load_from_file("config.yaml")  # Validates version compatibility
    >>> print(config.log_level)
    ERROR

    Environment variables with type conversion:
    >>> os.environ["CARD_FILTER_LOG_LEVEL"] = "DEBUG"
    >>> config = CardFilterConfig.from_env()  # Converts and validates types
    >>> print(config.log_level)
    DEBUG
"""

from typing import List, Optional, Set, Dict, Any, Union
from pathlib import Path
import yaml
import json
import os
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ConfigVersion(BaseModel):
    """Version information for configuration with semantic versioning support.
    
    Handles version compatibility checking using semantic versioning rules.
    Major version changes indicate breaking changes, minor versions add
    backwards-compatible features, and patch versions fix bugs.

    Attributes:
        major (int): Major version number (breaking changes)
        minor (int): Minor version number (new features)
        patch (int): Patch version number (bug fixes)
    """
    major: int = Field(default=1, description="Major version number")
    minor: int = Field(default=0, description="Minor version number")
    patch: int = Field(default=0, description="Patch version number")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConfigVersion):
            return NotImplemented
        return (self.major == other.major and 
                self.minor == other.minor and 
                self.patch == other.patch)

    def __lt__(self, other: "ConfigVersion") -> bool:
        if not isinstance(other, ConfigVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other: "ConfigVersion") -> bool:
        if not isinstance(other, ConfigVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other: "ConfigVersion") -> bool:
        if not isinstance(other, ConfigVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other: "ConfigVersion") -> bool:
        if not isinstance(other, ConfigVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    @classmethod
    def from_str(cls, version_str: Union[str, dict]) -> "ConfigVersion":
        """Create version from string or dict with validation.
        
        Args:
            version_str: Version string ('major.minor.patch') or version dict

        Returns:
            ConfigVersion: Validated version instance

        Raises:
            ValueError: If version format is invalid
        """
        try:
            if isinstance(version_str, dict):
                return cls(**version_str)
            
            parts = version_str.split(".")
            if len(parts) != 3:
                raise ValueError()
            
            return cls(
                major=int(parts[0]),
                minor=int(parts[1]),
                patch=int(parts[2])
            )
        except (ValueError, TypeError):
            raise ValueError("Version must be in format 'major.minor.patch' or a valid dictionary")

    def is_compatible_with(self, other: "ConfigVersion") -> bool:
        """Check if this version is compatible with another version.
        
        Compatibility rules:
        - Major versions must match (except 0.x.x)
        - Minor version must be greater or equal
        - Patch version is not considered for compatibility

        Args:
            other: Version to check compatibility with

        Returns:
            bool: True if versions are compatible
        """
        return self.major == other.major and (
            self.minor >= other.minor or self.major == 0
        )


class CardFilterConfig(BaseModel):
    """Configuration settings for the card filter application.
    
    Provides comprehensive configuration management with validation,
    type checking, and default values. Supports loading from files
    and environment variables with automatic type conversion.

    Attributes:
        version (ConfigVersion): Configuration version information
        max_file_size_mb (int): Maximum allowed input file size
        buffer_size (int): Buffer size for file operations
        default_schema (List[str]): Default fields to include
        valid_operators (Set[str]): Valid filter operators
        log_file (str): Log file path
        log_format (str): Log message format
        log_level (str): Logging level
    """

    # Version information with semantic versioning
    version: ConfigVersion = Field(
        default=ConfigVersion(),
        description="Configuration version"
    )

    # File handling settings with validation
    max_file_size_mb: int = Field(
        default=100, description="Maximum allowed input file size in MB"
    )
    buffer_size: int = Field(
        default=8192, description="Buffer size for file operations"
    )

    # Schema settings with defaults
    default_schema: List[str] = Field(
        default=[
            "name",
            "type",
            "colors",
            "colorIdentity",
            "convertedManaCost",
            "availability",
            "text",
            "edhrecSaltiness",
            "language",
            "foreignData",
        ],
        description="Default schema fields to include",
    )

    # Filter settings with type checking
    valid_operators: Set[str] = Field(
        default={"eq", "contains", "gt", "lt"}, description="Valid filter operators"
    )

    # Logging settings with validation
    log_file: str = Field(default="filter_cards.log", description="Log file path")
    log_format: str = Field(
        default="%(asctime)s - %(levelname)s - %(message)s",
        description="Log message format",
    )
    log_level: str = Field(default="ERROR", description="Logging level")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        str_strip_whitespace=True,
        frozen=False
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the standard logging levels.
        
        Args:
            v: Log level to validate

        Returns:
            str: Validated log level in uppercase

        Raises:
            ValueError: If log level is invalid
        """
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    def load_from_file(self, file_path: str) -> None:
        """Load configuration from a YAML or JSON file with validation.
        
        Args:
            file_path: Path to configuration file

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If file format is invalid or version incompatible
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        content = path.read_text()
        if path.suffix.lower() in {".yaml", ".yml"}:
            config_data = yaml.safe_load(content)
        elif path.suffix.lower() == ".json":
            config_data = json.loads(content)
        else:
            raise ValueError("Configuration file must be YAML or JSON")

        # Handle version compatibility with validation
        if "version" in config_data:
            version_value = config_data["version"]
            file_version = ConfigVersion.from_str(version_value)
            current_version = self.version
            if not file_version.is_compatible_with(current_version):
                raise ValueError(
                    f"Configuration version {file_version} is not compatible with "
                    f"current version {current_version}"
                )
            # Update version in config_data to be a dict for validation
            config_data["version"] = file_version.model_dump()

        # Update instance with new values using model_validate
        updated_config = self.model_validate(config_data)
        for key, value in updated_config.model_dump().items():
            setattr(self, key, value)

    @classmethod
    def from_env(cls) -> "CardFilterConfig":
        """Create instance from environment variables with type conversion.
        
        Environment variables are prefixed with CARD_FILTER_ and automatically
        converted to appropriate types based on field definitions.

        Returns:
            CardFilterConfig: Configuration instance from environment
        """
        env_vars = {}
        prefix = "CARD_FILTER_"
        
        for key, field in cls.model_fields.items():
            env_key = f"{prefix}{key}".upper()
            if env_key in os.environ:
                # Special handling for version
                if key == "version" and env_key in os.environ:
                    env_vars[key] = ConfigVersion.from_str(os.environ[env_key])
                else:
                    env_vars[key] = os.environ[env_key]

        return cls.model_validate(env_vars) if env_vars else cls()

    def save_to_file(self, file_path: str) -> None:
        """Save configuration to a file with proper serialization.
        
        Args:
            file_path: Path to save configuration to
        """
        path = Path(file_path)
        config_data = self.model_dump()
        
        # Convert version to dictionary for serialization
        version_dict = config_data["version"]
        config_data["version"] = {
            "major": version_dict["major"],
            "minor": version_dict["minor"],
            "patch": version_dict["patch"]
        }
        
        # Convert sets to lists for JSON serialization
        if "valid_operators" in config_data:
            config_data["valid_operators"] = list(config_data["valid_operators"])
        
        content = (
            yaml.dump(config_data, default_flow_style=False, sort_keys=False)
            if path.suffix.lower() in {".yaml", ".yml"}
            else json.dumps(config_data, indent=2)
        )
        
        path.write_text(content)


def load_config(config_file: Optional[str] = None) -> CardFilterConfig:
    """Load configuration from environment variables and optionally from a file.
    
    Args:
        config_file: Optional path to configuration file

    Returns:
        CardFilterConfig: Loaded configuration instance
    """
    config = CardFilterConfig.from_env()

    if config_file:
        config.load_from_file(config_file)

    return config
