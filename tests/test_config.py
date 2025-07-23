"""
Unit tests for configuration system (mcconfig.py and mcoptions.py)
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcconfig import Config, initialize_config
from mcoptions import Options, get_system_locale, parse_options
from version import __app_name__


class TestConfig:
    """Test the Config class"""

    def test_tomllib_import_fallback(self):
        """Test fallback to tomli when tomllib is not available"""
        # This test verifies the import fallback works by checking both modules exist
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib

        # Just verify we can access the load function from whichever module is used
        assert hasattr(tomllib, "load")

    def test_config_initialization(self):
        """Test config initialization with default values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("mcconfig.Config._get_config_path", return_value=temp_dir):
                config = Config("test_config.toml")

                assert config.get("logLevel") == 20
                assert config.get("mkvmergePath") == ""
                assert config.get("mkvpropeditPath") == ""
                assert config.get("atomicParsleyPath") == ""

    def test_config_file_creation(self):
        """Test that config file is created if it doesn't exist"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("mcconfig.Config._get_config_path", return_value=temp_dir):
                Config("test_config.toml")

                config_file = str(Path(temp_dir) / "test_config.toml")
                assert Path(config_file).exists()

    def test_config_get_with_default(self):
        """Test getting config values with default fallback"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("mcconfig.Config._get_config_path", return_value=temp_dir):
                config = Config("test_config.toml")

                assert config.get("nonexistent", "default") == "default"
                assert config.get("logLevel", 10) == 20  # Should return actual value

    def test_config_file_generation(self):
        """Test that default config file is generated with correct content"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("mcconfig.Config._get_config_path", return_value=temp_dir):
                Config("test_config.toml")

                config_file = str(Path(temp_dir) / "test_config.toml")
                assert Path(config_file).exists()

                # Read the generated file and verify it contains expected content
                with Path(config_file).open() as f:
                    content = f.read()
                    assert "logLevel = 20" in content
                    assert "useSystemLocale = true" in content

    def test_config_file_copied_from_example(self):
        """Test that config file is copied from example and contains comments"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("mcconfig.Config._get_config_path", return_value=temp_dir):
                Config("test_config.toml")

                config_file = str(Path(temp_dir) / "test_config.toml")
                assert Path(config_file).exists()

                # Read the generated file and verify it contains example file content
                with Path(config_file).open() as f:
                    content = f.read()
                    # Verify it contains helpful comments from example file
                    assert "# Copy this file to your local config folder" in content
                    assert "# Log level as an integer" in content
                    assert "# Direct paths to binaries" in content
                    assert "logLevel = 20" in content
                    assert "useSystemLocale = true" in content
                    assert "onlyMkv = false" in content
                    assert "onlyMp4 = false" in content

    def test_config_file_fallback_when_example_missing(self):
        """Test fallback to old behavior when example config file is missing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a config instance and test _generate_default_config_file directly
            config = Config.__new__(Config)
            config.config = {
                "logLevel": 20,
                "mkvmergePath": "",
                "useSystemLocale": True,
            }

            config_file_path = str(Path(temp_dir) / "test_config.toml")

            # Test the fallback behavior by temporarily moving the example file
            import shutil

            # Find the real example file and temporarily rename it
            example_path = Path(__file__).parent.parent / "src" / "config.example.toml"
            backup_path = example_path.with_suffix(".toml.backup")

            try:
                # Temporarily rename the example file so it's not found
                if example_path.exists():
                    shutil.move(str(example_path), str(backup_path))

                # Call the method - should fallback to old behavior
                config._generate_default_config_file(config_file_path)

                assert Path(config_file_path).exists()

                # Read the generated file and verify it contains minimal content (no comments)
                with Path(config_file_path).open() as f:
                    content = f.read()
                    # Should not contain example file comments
                    assert "# Copy this file to your local config folder" not in content
                    assert "# Log level as an integer" not in content
                    # Should contain the basic values
                    assert "logLevel = 20" in content
                    assert "useSystemLocale = true" in content
            finally:
                # Restore the example file
                if backup_path.exists():
                    shutil.move(str(backup_path), str(example_path))

    @patch("mcconfig.platform.system")
    def test_get_config_path_windows(self, mock_system):
        """Test config path on Windows"""
        mock_system.return_value = "Windows"

        with patch.dict(
            os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}
        ):
            config = Config.__new__(Config)
            path = config._get_config_path()

            assert path == f"C:\\Users\\test\\AppData\\Local/{__app_name__}"

    @patch("mcconfig.platform.system")
    def test_get_config_path_linux(self, mock_system):
        """Test config path on Linux"""
        mock_system.return_value = "Linux"

        with patch.dict(os.environ, {"HOME": "/home/test"}, clear=True):
            config = Config.__new__(Config)
            path = config._get_config_path()

            assert path == f"/home/test/.config/{__app_name__}"

    @patch("mcconfig.platform.system")
    def test_get_config_path_macos(self, mock_system):
        """Test config path on macOS"""
        mock_system.return_value = "Darwin"

        with patch(
            "mcconfig.Path.expanduser",
            return_value=Path("/Users/test/Library/Application Support"),
        ):
            config = Config.__new__(Config)
            path = config._get_config_path()

            assert path == f"/Users/test/Library/Application Support/{__app_name__}"

    @patch("mcconfig.platform.system")
    def test_get_config_path_unsupported(self, mock_system):
        """Test config path on unsupported platform"""
        mock_system.return_value = "UnsupportedOS"

        config = Config.__new__(Config)
        with pytest.raises(NotImplementedError):
            config._get_config_path()

    @patch("mcconfig.platform.system")
    def test_get_config_path_windows_missing_localappdata(self, mock_system):
        """Test config path on Windows with missing LOCALAPPDATA"""
        mock_system.return_value = "Windows"

        with patch.dict(os.environ, {}, clear=True):
            config = Config.__new__(Config)
            with pytest.raises(EnvironmentError, match="LOCALAPPDATA is not set"):
                config._get_config_path()


class TestGetSystemLocale:
    """Test the get_system_locale function"""

    @patch("mcoptions.platform.system")
    def test_get_system_locale_windows(self, mock_system):
        """Test system locale detection on Windows"""
        mock_system.return_value = "Windows"

        # Mock the ctypes module when it's imported in the function
        with patch("builtins.__import__") as mock_import:
            mock_ctypes = Mock()
            mock_windll = mock_ctypes.windll.kernel32
            mock_windll.GetUserDefaultLCID.return_value = 1033

            mock_buffer = Mock()
            mock_buffer.value = "en-US"
            mock_ctypes.create_unicode_buffer.return_value = mock_buffer

            def side_effect(name, *args, **kwargs):
                if name == "ctypes":
                    return mock_ctypes
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = side_effect

            result = get_system_locale()
            assert result == "en"

    @patch("mcoptions.platform.system")
    def test_get_system_locale_linux(self, mock_system):
        """Test system locale detection on Linux"""
        mock_system.return_value = "Linux"

        with patch.dict(os.environ, {"LANG": "en_US.UTF-8"}):
            result = get_system_locale()

            assert result == "en"

    @patch("mcoptions.platform.system")
    def test_get_system_locale_fallback(self, mock_system):
        """Test system locale fallback to Python's locale"""
        mock_system.return_value = "Linux"

        with patch.dict(os.environ, {}, clear=True), patch(
            "mcoptions.locale.getdefaultlocale", return_value=("es_ES", "UTF-8")
        ):
            result = get_system_locale()

            assert result == "es"

    @patch("mcoptions.platform.system")
    def test_get_system_locale_failure(self, mock_system):
        """Test system locale detection failure"""
        mock_system.return_value = "Linux"

        with patch.dict(os.environ, {}, clear=True), patch(
            "mcoptions.locale.getdefaultlocale",
            side_effect=Exception("Locale error"),
        ):
            result = get_system_locale()

            assert result is None


class TestParseOptions:
    """Test the parse_options function"""

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "test.mkv"])
    def test_parse_options_defaults(self, mock_config):
        """Test parsing with default values"""
        mock_config.get.side_effect = lambda key, default=None: {
            "useSystemLocale": True,
            "language": "en",
            "logLevel": 20,
            "setDefaultSubTrack": False,
            "forceDefaultFirstSubTrack": False,
            "onlyMkv": False,
            "onlyMp4": False,
            "mkvmergePath": "",
            "mkvpropeditPath": "",
            "atomicParsleyPath": "",
        }.get(key, default)
        mock_config.log_file_path = "/tmp/test.log"

        with patch("mcoptions.get_system_locale", return_value="en"):
            options = parse_options()

            assert options.paths == ["test.mkv"]
            assert options.language == "en"
            assert options.log_level == 20
            assert options.dry_run is False
            assert options.only_mkv is False
            assert options.only_mp4 is False

    @patch("mcoptions.mcconfig")
    @patch(
        "sys.argv", [__app_name__, "--dry-run", "--only-mkv", "-L", "es", "test.mkv"]
    )
    def test_parse_options_cli_overrides(self, mock_config):
        """Test CLI argument overrides"""
        mock_config.get.return_value = ""
        mock_config.log_file_path = "/tmp/test.log"

        options = parse_options()

        assert options.dry_run is True
        assert options.only_mkv is True
        assert options.language == "es"
        assert options.sources["dry_run"] == "cli"
        assert options.sources["only_mkv"] == "cli"
        assert options.sources["language"] == "cli"

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "--only-mkv", "--only-mp4", "test.mkv"])
    def test_parse_options_conflicting_file_types(self, mock_config):
        """Test validation of conflicting file type options"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__])
    def test_parse_options_no_paths(self, mock_config):
        """Test validation when no paths are provided"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch(
        "sys.argv",
        [
            __app_name__,
            "-M",
            "/usr/bin/mkvmerge",
            "-P",
            "/usr/bin/mkvpropedit",
            "test.mkv",
        ],
    )
    def test_parse_options_tool_paths(self, mock_config):
        """Test parsing tool path options"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with patch("mcoptions.get_system_locale", return_value="en"):
            options = parse_options()

            assert options.mkvmerge_path == "/usr/bin/mkvmerge"
            assert options.mkvpropedit_path == "/usr/bin/mkvpropedit"
            assert options.sources["mkvmerge_path"] == "cli"
            assert options.sources["mkvpropedit_path"] == "cli"

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "-l", "/tmp/custom.log", "test.mkv"])
    def test_parse_options_custom_log_file(self, mock_config):
        """Test parsing custom log file option"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with patch("mcoptions.get_system_locale", return_value="en"):
            options = parse_options()

            assert options.log_file_path == "/tmp/custom.log"
            assert options.sources["log_file_path"] == "cli"

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "-i", "input.txt"])
    def test_parse_options_input_file(self, mock_config):
        """Test parsing input file option"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with patch("mcoptions.get_system_locale", return_value="en"):
            options = parse_options()

            assert options.input_file == "input.txt"
            assert options.sources["input_file"] == "cli"


class TestCustomConfig:
    """Test custom configuration file functionality"""

    def test_custom_config_file_loading(self):
        """Test loading a custom configuration file"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config file
            custom_config_path = Path(temp_dir) / "custom_config.toml"
            with custom_config_path.open("w") as f:
                f.write(
                    """
logLevel = 10
mkvmergePath = "/custom/path/to/mkvmerge"
mkvpropeditPath = "/custom/path/to/mkvpropedit"
atomicParsleyPath = "/custom/path/to/AtomicParsley"
setDefaultSubTrack = true
forceDefaultFirstSubTrack = true
useSystemLocale = false
language = "fr"
onlyMkv = true
onlyMp4 = false
"""
                )

            # Initialize config with custom file
            config = initialize_config(custom_config_path)

            # Verify values from custom config
            assert config.get("logLevel") == 10
            assert config.get("mkvmergePath") == "/custom/path/to/mkvmerge"
            assert config.get("mkvpropeditPath") == "/custom/path/to/mkvpropedit"
            assert config.get("atomicParsleyPath") == "/custom/path/to/AtomicParsley"
            assert config.get("setDefaultSubTrack") is True
            assert config.get("forceDefaultFirstSubTrack") is True
            assert config.get("useSystemLocale") is False
            assert config.get("language") == "fr"
            assert config.get("onlyMkv") is True
            assert config.get("onlyMp4") is False

            # Verify config file path is set correctly
            assert config.config_file_path == custom_config_path

            # Verify log file path uses same directory as custom config
            expected_log_path = str(Path(temp_dir) / f"{__app_name__}.log")
            assert config.log_file_path == expected_log_path

    def test_custom_config_nonexistent_file(self):
        """Test error handling for nonexistent custom config file"""
        nonexistent_path = "/nonexistent/path/config.toml"

        with pytest.raises(FileNotFoundError) as exc_info:
            initialize_config(nonexistent_path)

        assert f"Custom config file not found: {nonexistent_path}" in str(
            exc_info.value
        )

    def test_custom_config_with_partial_settings(self):
        """Test custom config with only some settings specified"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config file with only some settings
            custom_config_path = Path(temp_dir) / "partial_config.toml"
            with custom_config_path.open("w") as f:
                f.write(
                    """
logLevel = 40
language = "de"
onlyMkv = true
"""
                )

            # Initialize config with custom file
            config = initialize_config(custom_config_path)

            # Verify custom values are loaded
            assert config.get("logLevel") == 40
            assert config.get("language") == "de"
            assert config.get("onlyMkv") is True

            # Verify default values are preserved for unspecified settings
            assert config.get("setDefaultSubTrack") is False  # default value

    @patch("sys.argv", [__app_name__, "--config", "custom.toml", "test.mkv"])
    def test_parse_options_with_custom_config(self):
        """Test parse_options with --config argument"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config file
            custom_config_path = Path(temp_dir) / "custom.toml"
            with custom_config_path.open("w") as f:
                f.write(
                    """
logLevel = 10
language = "es"
useSystemLocale = false
setDefaultSubTrack = true
onlyMkv = true
"""
                )

            # Mock the args.config to use our test file
            with patch("mcoptions._create_argument_parser") as mock_parser_func:
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.config = custom_config_path
                mock_args.paths = ["test.mkv"]
                mock_args.input = None
                mock_args.dry_run = False
                mock_args.only_mkv = False
                mock_args.only_mp4 = False
                mock_args.language = None
                mock_args.loglevel = None
                mock_args.mkvmerge_path = None
                mock_args.mkvpropedit_path = None
                mock_args.atomicparsley_path = None
                mock_args.set_default_subtitle = False
                mock_args.default_first = False
                mock_args.logfile = None

                mock_parser.parse_args.return_value = mock_args
                mock_parser_func.return_value = mock_parser

                with patch("mcoptions.get_system_locale", return_value="en"):
                    options = parse_options()

                # Verify values from custom config are used
                assert options.log_level == 10
                assert options.language == "es"
                assert options.set_default_sub_track is True
                assert options.only_mkv is True

    @patch(
        "sys.argv",
        [
            __app_name__,
            "--config",
            "custom.toml",
            "--language",
            "fr",
            "--loglevel",
            "40",
            "test.mkv",
        ],
    )
    def test_config_precedence_cli_over_custom(self):
        """Test that CLI arguments override custom config values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config file
            custom_config_path = Path(temp_dir) / "custom.toml"
            with custom_config_path.open("w") as f:
                f.write(
                    """
logLevel = 10
language = "es"
setDefaultSubTrack = true
onlyMkv = true
"""
                )

            # Mock the args to use our test file and CLI overrides
            with patch("mcoptions._create_argument_parser") as mock_parser_func:
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.config = custom_config_path
                mock_args.paths = ["test.mkv"]
                mock_args.input = None
                mock_args.dry_run = False
                mock_args.only_mkv = False  # CLI default (not specified)
                mock_args.only_mp4 = False
                mock_args.language = "fr"  # CLI override
                mock_args.loglevel = 40  # CLI override
                mock_args.mkvmerge_path = None
                mock_args.mkvpropedit_path = None
                mock_args.atomicparsley_path = None
                mock_args.set_default_subtitle = False
                mock_args.default_first = False
                mock_args.clear_audio = False
                mock_args.logfile = None
                mock_args.stdout = False  # CLI default (not specified)
                mock_args.stdout_only = False  # CLI default (not specified)

                mock_parser.parse_args.return_value = mock_args
                mock_parser_func.return_value = mock_parser

                options = parse_options()

                # Verify CLI values override custom config
                assert options.log_level == 40  # CLI override
                assert options.language == "fr"  # CLI override
                assert options.sources["log_level"] == "cli"
                assert options.sources["language"] == "cli"

                # Verify custom config values are used when no CLI override
                assert options.set_default_sub_track is True  # from custom config
                assert options.only_mkv is True  # from custom config

    def test_config_precedence_custom_over_default(self):
        """Test that custom config values override defaults when no CLI override"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config file with different values from defaults
            custom_config_path = Path(temp_dir) / "custom.toml"
            with custom_config_path.open("w") as f:
                f.write(
                    """
logLevel = 10
setDefaultSubTrack = true
language = "de"
useSystemLocale = false
"""
                )

            # Mock minimal CLI args (no overrides)
            with patch("mcoptions._create_argument_parser") as mock_parser_func:
                mock_parser = Mock()
                mock_args = Mock()
                mock_args.config = custom_config_path
                mock_args.paths = ["test.mkv"]
                mock_args.input = None
                mock_args.dry_run = False
                mock_args.only_mkv = False
                mock_args.only_mp4 = False
                mock_args.language = None  # No CLI override
                mock_args.loglevel = None  # No CLI override
                mock_args.mkvmerge_path = None
                mock_args.mkvpropedit_path = None
                mock_args.atomicparsley_path = None
                mock_args.set_default_subtitle = False  # No CLI override
                mock_args.default_first = False
                mock_args.clear_audio = False
                mock_args.logfile = None
                mock_args.stdout = False  # No CLI override
                mock_args.stdout_only = False  # No CLI override

                mock_parser.parse_args.return_value = mock_args
                mock_parser_func.return_value = mock_parser

                with patch("mcoptions.get_system_locale", return_value="en"):
                    options = parse_options()

                # Verify custom config values override defaults
                assert options.log_level == 10  # custom config (default is 30)
                assert (
                    options.set_default_sub_track is True
                )  # custom config (default is False)
                assert options.language == "de"  # custom config

                # Verify source tracking
                assert options.sources["log_level"] == "config"
                assert options.sources["set_default_sub_track"] == "config"
                assert options.sources["language"] == "config"


class TestOptions:
    """Test the Options dataclass"""

    def test_options_creation(self):
        """Test Options dataclass creation"""
        from langcodes import Language

        options = Options(
            paths=["test.mkv"],
            input_file=None,
            dry_run=False,
            only_mkv=False,
            only_mp4=False,
            language="en",
            lang_object=Language.get("en"),
            lang3="eng",
            use_system_locale=True,
            detected_locale="en",
            mkvmerge_path="",
            mkvpropedit_path="",
            atomicparsley_path="",
            log_level=20,
            log_file_path="/tmp/test.log",
            stdout=False,
            stdout_only=False,
            set_default_sub_track=False,
            force_default_first_sub_track=False,
            set_default_audio_track=False,
            clear_audio_track_names=False,
            sources={},
        )

        assert options.paths == ["test.mkv"]
        assert options.language == "en"
        assert options.lang3 == "eng"
        assert options.dry_run is False
