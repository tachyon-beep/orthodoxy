"""Tests for configuration management."""

import pytest
import os
import yaml
import json
from pathlib import Path
from src.core.config import ConfigVersion, CardFilterConfig, load_config

@pytest.fixture
def version():
    """Create a test version."""
    return ConfigVersion(major=1, minor=2, patch=3)

@pytest.fixture
def config():
    """Create a test configuration."""
    return CardFilterConfig()

class TestConfigVersion:
    def test_version_init(self):
        """Test version initialization."""
        version = ConfigVersion(major=1, minor=2, patch=3)
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_defaults(self):
        """Test version default values."""
        version = ConfigVersion()
        assert version.major == 1
        assert version.minor == 0
        assert version.patch == 0

    def test_version_str(self, version):
        """Test version string representation."""
        assert str(version) == "1.2.3"

    def test_version_equality(self, version):
        """Test version equality comparison."""
        same_version = ConfigVersion(major=1, minor=2, patch=3)
        different_version = ConfigVersion(major=1, minor=2, patch=4)
        
        assert version == same_version
        assert version != different_version
        assert version != "1.2.3"  # Compare with non-ConfigVersion

    def test_version_ordering(self, version):
        """Test version ordering comparisons."""
        lower_version = ConfigVersion(major=1, minor=2, patch=2)
        higher_version = ConfigVersion(major=1, minor=2, patch=4)
        same_version = ConfigVersion(major=1, minor=2, patch=3)
        
        # Test less than
        assert lower_version < version
        assert version < higher_version
        assert version >= lower_version
        
        # Test less than or equal
        assert lower_version <= version
        assert version <= higher_version
        assert version <= same_version
        assert higher_version > version
        
        # Test greater than
        assert version > lower_version
        assert higher_version > version
        assert version <= higher_version
        
        # Test greater than or equal
        assert version >= lower_version
        assert higher_version >= version
        assert version >= same_version
        assert lower_version < version

    def test_version_from_str(self):
        """Test version creation from string."""
        version = ConfigVersion.from_str("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

        # Test invalid formats
        with pytest.raises(ValueError):
            ConfigVersion.from_str("1.2")
        with pytest.raises(ValueError):
            ConfigVersion.from_str("invalid")
        with pytest.raises(ValueError):
            ConfigVersion.from_str("1.2.three")

    def test_version_from_dict(self):
        """Test version creation from dictionary."""
        version = ConfigVersion.from_str({
            "major": 1,
            "minor": 2,
            "patch": 3
        })
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3

    def test_version_compatibility(self):
        """Test version compatibility checking."""
        v1_0_0 = ConfigVersion(major=1, minor=0, patch=0)
        v1_1_0 = ConfigVersion(major=1, minor=1, patch=0)
        v1_2_0 = ConfigVersion(major=1, minor=2, patch=0)
        v2_0_0 = ConfigVersion(major=2, minor=0, patch=0)
        
        # Same major version, higher minor is compatible
        assert v1_2_0.is_compatible_with(v1_0_0)
        assert v1_2_0.is_compatible_with(v1_1_0)
        
        # Lower minor version is not compatible
        assert not v1_0_0.is_compatible_with(v1_1_0)
        
        # Different major versions are not compatible
        assert not v2_0_0.is_compatible_with(v1_0_0)
        assert not v1_0_0.is_compatible_with(v2_0_0)

class TestCardFilterConfig:
    def test_config_defaults(self, config):
        """Test configuration default values."""
        assert isinstance(config.version, ConfigVersion)
        assert config.max_file_size_mb == 100
        assert config.buffer_size == 8192
        assert isinstance(config.default_schema, list)
        assert isinstance(config.valid_operators, set)
        assert config.log_level == "ERROR"

    def test_log_level_validation(self):
        """Test log level validation."""
        config = CardFilterConfig(log_level="DEBUG")
        assert config.log_level == "DEBUG"

        with pytest.raises(ValueError):
            CardFilterConfig(log_level="INVALID")

    def test_load_from_yaml(self, tmp_path):
        """Test loading configuration from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "version": {"major": 1, "minor": 0, "patch": 0},
            "max_file_size_mb": 200,
            "log_level": "DEBUG"
        }
        config_file.write_text(yaml.dump(config_data))

        config = CardFilterConfig()
        config.load_from_file(str(config_file))
        assert config.max_file_size_mb == 200
        assert config.log_level == "DEBUG"

    def test_load_from_json(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "version": {"major": 1, "minor": 0, "patch": 0},
            "max_file_size_mb": 200,
            "log_level": "DEBUG"
        }
        config_file.write_text(json.dumps(config_data))

        config = CardFilterConfig()
        config.load_from_file(str(config_file))
        assert config.max_file_size_mb == 200
        assert config.log_level == "DEBUG"

    def test_load_invalid_file(self, tmp_path):
        """Test loading from invalid file."""
        config = CardFilterConfig()
        
        # Test nonexistent file
        with pytest.raises(FileNotFoundError):
            config.load_from_file("nonexistent.yaml")
        
        # Test invalid file extension
        invalid_file = tmp_path / "config.txt"
        invalid_file.touch()
        with pytest.raises(ValueError):
            config.load_from_file(str(invalid_file))

    def test_load_incompatible_version(self, tmp_path):
        """Test loading configuration with incompatible version."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "version": {"major": 2, "minor": 0, "patch": 0},
            "max_file_size_mb": 200
        }
        config_file.write_text(yaml.dump(config_data))

        config = CardFilterConfig()
        with pytest.raises(ValueError) as exc_info:
            config.load_from_file(str(config_file))
        assert "not compatible" in str(exc_info.value)

    def test_save_to_file(self, tmp_path, config):
        """Test saving configuration to file."""
        # Test YAML
        yaml_file = tmp_path / "config.yaml"
        config.save_to_file(str(yaml_file))
        assert yaml_file.exists()
        
        loaded_config = CardFilterConfig()
        loaded_config.load_from_file(str(yaml_file))
        assert loaded_config.model_dump() == config.model_dump()
        
        # Test JSON
        json_file = tmp_path / "config.json"
        config.save_to_file(str(json_file))
        assert json_file.exists()
        
        loaded_config = CardFilterConfig()
        loaded_config.load_from_file(str(json_file))
        assert loaded_config.model_dump() == config.model_dump()

    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        env_vars = {
            "CARD_FILTER_MAX_FILE_SIZE_MB": "200",
            "CARD_FILTER_LOG_LEVEL": "DEBUG",
            "CARD_FILTER_VERSION": "1.1.0"
        }
        for key, value in env_vars.items():
            monkeypatch.setenv(key, value)

        config = CardFilterConfig.from_env()
        assert config.max_file_size_mb == 200
        assert config.log_level == "DEBUG"
        assert config.version == ConfigVersion(major=1, minor=1, patch=0)

    def test_load_config_function(self, tmp_path):
        """Test the load_config function."""
        # Test loading from environment
        config = load_config()
        assert isinstance(config, CardFilterConfig)

        # Test loading from file
        config_file = tmp_path / "config.yaml"
        config_data = {
            "version": {"major": 1, "minor": 0, "patch": 0},
            "max_file_size_mb": 200,
            "log_level": "DEBUG"
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))
        assert config.max_file_size_mb == 200
        assert config.log_level == "DEBUG"
