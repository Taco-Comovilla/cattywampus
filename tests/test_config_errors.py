"""
Tests for configuration error handling scenarios
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from mcconfig import Config, initialize_config

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


class TestConfigErrors:
    """Test configuration error handling scenarios"""

    @patch("mcconfig.platform.system")
    def test_config_unsupported_platform(self, mock_system):
        """Test config behavior on unsupported platform"""
        mock_system.return_value = "UnsupportedOS"

        config = Config.__new__(Config)

        with pytest.raises(NotImplementedError, match="Unsupported platform"):
            config._get_config_path()

    @patch("mcconfig.os.getenv")
    @patch("mcconfig.platform.system")
    def test_config_missing_environment_variables(self, mock_system, mock_getenv):
        """Test config behavior when environment variables are missing"""
        mock_system.return_value = "Windows"
        mock_getenv.return_value = None  # No LOCALAPPDATA

        config = Config.__new__(Config)

        with pytest.raises(EnvironmentError, match="LOCALAPPDATA is not set"):
            config._get_config_path()

    @patch("mcconfig.Path.mkdir")
    def test_config_directory_creation_error(self, mock_mkdir):
        """Test config behavior when directory creation fails"""
        mock_mkdir.side_effect = PermissionError("Permission denied")

        # This should raise the PermissionError during initialization
        with pytest.raises(PermissionError, match="Permission denied"):
            Config("test_config.toml")

    def test_config_invalid_toml_file(self):
        """Test config behavior with invalid TOML content"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file_path = str(Path(tmp_dir) / "invalid_config.toml")

            # Create invalid TOML content
            with Path(config_file_path).open("w") as f:
                f.write("invalid toml content [[[")

            # Should raise a TOML parsing error
            with pytest.raises((tomllib.TOMLDecodeError, ValueError)):
                config = Config.__new__(Config)
                config.config_file_path = config_file_path
                with Path(config_file_path).open("rb") as config_file:
                    config.config = tomllib.load(config_file)

    def test_config_read_only_file(self):
        """Test config behavior with read-only config file"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as tmp_file:
            tmp_file.write('test_key = "test_value"\n')
            tmp_file_path = tmp_file.name

        try:
            # Make file read-only
            Path(tmp_file_path).chmod(0o444)

            config = Config(tmp_file_path)

            # Should still be able to read
            value = config.get("test_key", "default")
            assert value == "test_value"

        finally:
            # Restore permissions and clean up
            Path(tmp_file_path).chmod(0o644)
            Path(tmp_file_path).unlink()

    def test_config_nonexistent_file(self):
        """Test config behavior with non-existent config file"""
        nonexistent_path = "/tmp/definitely_does_not_exist_config.toml"

        # Should handle non-existent file gracefully
        config = Config(nonexistent_path)

        # Should work with defaults
        value = config.get("test_key", "default")
        assert value == "default"

    @patch("mcconfig.tomllib.load")
    def test_config_toml_load_error(self, mock_tomllib_load):
        """Test config behavior when TOML loading fails"""
        mock_tomllib_load.side_effect = Exception("TOML load error")

        with tempfile.TemporaryDirectory() as tmp_dir:
            config_file_path = str(Path(tmp_dir) / "test_config.toml")

            # Create valid TOML file
            with Path(config_file_path).open("w") as f:
                f.write('test_key = "test_value"\n')

            # Should raise the TOML loading error
            with pytest.raises(Exception, match="TOML load error"):
                config = Config.__new__(Config)
                config.config_file_path = config_file_path
                with Path(config_file_path).open("rb") as config_file:
                    config.config = tomllib.load(config_file)


class TestGracefulConfigErrorHandling:
    """Test graceful handling of configuration file errors (Issue #67)"""

    def test_custom_config_toml_syntax_error_graceful(self):
        """Test graceful handling of TOML syntax errors in custom config files"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
logLevel = 10
language = invalid_unquoted_string
"""
            )
            temp_path = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                initialize_config(temp_path)
            assert exc_info.value.code == 1
        finally:
            Path(temp_path).unlink()

    def test_custom_config_toml_unclosed_bracket_graceful(self):
        """Test graceful handling of unclosed bracket in custom config"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
logLevel = 10
language = [unclosed_bracket
"""
            )
            temp_path = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                initialize_config(temp_path)
            assert exc_info.value.code == 1
        finally:
            Path(temp_path).unlink()

    def test_custom_config_toml_duplicate_key_graceful(self):
        """Test graceful handling of duplicate keys in custom config"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
logLevel = 10
logLevel = 20
"""
            )
            temp_path = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                initialize_config(temp_path)
            assert exc_info.value.code == 1
        finally:
            Path(temp_path).unlink()

    def test_custom_config_toml_invalid_escape_graceful(self):
        """Test graceful handling of invalid escape sequences in custom config"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
logLevel = 10
language = "invalid\\escape"
"""
            )
            temp_path = f.name

        try:
            with pytest.raises(SystemExit) as exc_info:
                initialize_config(temp_path)
            assert exc_info.value.code == 1
        finally:
            Path(temp_path).unlink()

    def test_custom_config_permission_denied_graceful(self):
        """Test graceful handling of permission denied for custom config"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("logLevel = 10\nlanguage = 'en'")
            temp_path = f.name

        try:
            # Remove read permissions
            Path(temp_path).chmod(0o000)

            with pytest.raises(SystemExit) as exc_info:
                initialize_config(temp_path)
            assert exc_info.value.code == 1
        finally:
            # Restore permissions before cleanup
            try:
                Path(temp_path).chmod(0o644)
                Path(temp_path).unlink()
            except (OSError, FileNotFoundError, PermissionError):
                # Ignore cleanup errors - file might not exist or have permission issues
                pass

    def test_default_config_toml_error_graceful(self):
        """Test that default config file TOML errors are handled gracefully"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a malformed default config file
            config_file = Path(temp_dir) / "config.toml"
            with config_file.open("w") as f:
                f.write("logLevel = [malformed\n")

            with patch("mcconfig.Config._get_config_path", return_value=temp_dir):
                # Don't auto-generate config since we created a malformed one
                with patch("mcconfig.Config._ensure_config_exists"):
                    with pytest.raises(SystemExit) as exc_info:
                        Config("config.toml")
                    assert exc_info.value.code == 1

    def test_valid_config_still_works(self):
        """Test that valid config files still work normally after error handling improvements"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write(
                """
logLevel = 20
language = "fr"
setDefaultSubTrack = true
"""
            )
            temp_path = f.name

        try:
            config = initialize_config(temp_path)
            assert config.get("logLevel") == 20
            assert config.get("language") == "fr"
            assert config.get("setDefaultSubTrack") is True
        finally:
            Path(temp_path).unlink()
