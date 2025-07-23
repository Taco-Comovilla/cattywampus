"""
Tests for CLI interface and argument parsing
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcconfig import initialize_config
from mcoptions import _create_argument_parser, _validate_options, parse_options
from version import __app_name__


class TestArgumentParser:
    """Test the argument parser creation"""

    def test_create_argument_parser(self):
        """Test argument parser creation"""
        parser = _create_argument_parser()

        # Test that parser exists and has expected arguments
        assert parser is not None
        assert parser.prog == __app_name__

        # Test help output contains expected options
        help_text = parser.format_help()
        assert "--dry-run" in help_text
        assert "--only-mkv" in help_text
        assert "--only-mp4" in help_text
        assert "--mkvmerge-path" in help_text
        assert "--mkvpropedit-path" in help_text
        assert "--config" in help_text
        assert "--atomicparsley-path" in help_text
        assert "--language" in help_text
        assert "--logfile" in help_text

    def test_parse_basic_arguments(self):
        """Test parsing basic arguments"""
        parser = _create_argument_parser()

        args = parser.parse_args(["test.mkv"])

        assert args.paths == ["test.mkv"]
        assert args.dry_run is False
        assert args.only_mkv is False
        assert args.only_mp4 is False

    def test_parse_dry_run_flag(self):
        """Test parsing dry run flag"""
        parser = _create_argument_parser()

        args = parser.parse_args(["--dry-run", "test.mkv"])

        assert args.dry_run is True
        assert args.paths == ["test.mkv"]

    def test_parse_file_type_filters(self):
        """Test parsing file type filter flags"""
        parser = _create_argument_parser()

        args_mkv = parser.parse_args(["--only-mkv", "test.mkv"])
        assert args_mkv.only_mkv is True
        assert args_mkv.only_mp4 is False

        args_mp4 = parser.parse_args(["--only-mp4", "test.mp4"])
        assert args_mp4.only_mkv is False
        assert args_mp4.only_mp4 is True

    def test_parse_tool_paths(self):
        """Test parsing tool path arguments"""
        parser = _create_argument_parser()

        args = parser.parse_args(
            [
                "-M",
                "/usr/bin/mkvmerge",
                "-P",
                "/usr/bin/mkvpropedit",
                "-T",
                "/usr/bin/AtomicParsley",
                "test.mkv",
            ]
        )

        assert args.mkvmerge_path == "/usr/bin/mkvmerge"
        assert args.mkvpropedit_path == "/usr/bin/mkvpropedit"
        assert args.atomicparsley_path == "/usr/bin/AtomicParsley"

    def test_parse_language_option(self):
        """Test parsing language option"""
        parser = _create_argument_parser()

        args = parser.parse_args(["-L", "es", "test.mkv"])

        assert args.language == "es"

    def test_parse_log_options(self):
        """Test parsing log-related options"""
        parser = _create_argument_parser()

        args = parser.parse_args(["-g", "10", "-l", "/tmp/custom.log", "test.mkv"])

        assert args.loglevel == 10
        assert args.logfile == "/tmp/custom.log"

    def test_parse_input_file(self):
        """Test parsing input file option"""
        parser = _create_argument_parser()

        args = parser.parse_args(["-i", "input.txt"])

        assert args.input == "input.txt"
        assert args.paths == []

    def test_parse_subtitle_options(self):
        """Test parsing subtitle-related options"""
        parser = _create_argument_parser()

        args = parser.parse_args(["-s", "-f", "test.mkv"])

        assert args.set_default_subtitle is True
        assert args.default_first is True

    def test_parse_multiple_files(self):
        """Test parsing multiple file arguments"""
        parser = _create_argument_parser()

        args = parser.parse_args(["file1.mkv", "file2.mp4", "file3.mkv"])

        assert args.paths == ["file1.mkv", "file2.mp4", "file3.mkv"]


class TestValidateOptions:
    """Test the options validation"""

    def test_validate_options_success(self):
        """Test successful options validation"""
        # Create mock args
        args = MagicMock()
        args.paths = ["test.mkv"]
        args.input = None

        # Should not raise any exception
        _validate_options(args, False, False)

    def test_validate_options_with_input_file(self):
        """Test validation with input file"""
        args = MagicMock()
        args.paths = []
        args.input = "input.txt"

        # Should not raise any exception
        _validate_options(args, False, False)

    def test_validate_options_no_paths_or_input(self):
        """Test validation failure when no paths or input file"""
        args = MagicMock()
        args.paths = []
        args.input = None

        with pytest.raises(SystemExit):
            _validate_options(args, False, False)

    def test_validate_options_conflicting_file_types(self):
        """Test validation failure with conflicting file type options"""
        args = MagicMock()
        args.paths = ["test.mkv"]
        args.input = None

        with pytest.raises(SystemExit):
            _validate_options(args, True, True)  # Both only_mkv and only_mp4


class TestFullCLIIntegration:
    """Test full CLI integration"""

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "--help"])
    def test_help_output(self, mock_config):
        """Test help output"""
        mock_config.get.return_value = ""
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "--version"])
    def test_version_output(self, mock_config):
        """Test version output handling"""
        mock_config.get.return_value = ""
        mock_config.log_file_path = "/tmp/test.log"

        # Should exit gracefully (version not implemented yet)
        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "test.mkv"])
    def test_minimal_valid_command(self, mock_config):
        """Test minimal valid command"""
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
            assert options.dry_run is False

    @patch("mcoptions.mcconfig")
    @patch(
        "sys.argv", [__app_name__, "--dry-run", "--only-mkv", "-L", "fr", "test.mkv"]
    )
    def test_complex_command(self, mock_config):
        """Test complex command with multiple options"""
        mock_config.get.return_value = ""
        mock_config.log_file_path = "/tmp/test.log"

        options = parse_options()

        assert options.paths == ["test.mkv"]
        assert options.dry_run is True
        assert options.only_mkv is True
        assert options.only_mp4 is False
        assert options.language == "fr"
        assert options.sources["dry_run"] == "cli"
        assert options.sources["only_mkv"] == "cli"
        assert options.sources["language"] == "cli"

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "-i", "input.txt", "-l", "/tmp/custom.log"])
    def test_input_file_with_custom_log(self, mock_config):
        """Test input file with custom log location"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/default.log"

        with patch("mcoptions.get_system_locale", return_value="en"):
            options = parse_options()

            assert options.paths == []
            assert options.input_file == "input.txt"
            assert options.log_file_path == "/tmp/custom.log"
            assert options.sources["input_file"] == "cli"
            assert options.sources["log_file_path"] == "cli"

    def test_custom_config_integration(self):
        """Integration test for custom config functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a custom config file

            custom_config_path = Path(temp_dir) / "integration_test.toml"
            with custom_config_path.open("w") as f:
                f.write(
                    """
logLevel = 50
language = "ja"
useSystemLocale = false
setDefaultSubTrack = true
onlyMkv = true
"""
                )

            # Test custom config loading
            config = initialize_config(custom_config_path)
            assert config.get("logLevel") == 50
            assert config.get("language") == "ja"
            assert config.get("useSystemLocale") is False
            assert config.get("setDefaultSubTrack") is True
            assert config.get("onlyMkv") is True

            # Test that defaults are preserved for unspecified values
            assert config.get("forceDefaultFirstSubTrack") is False  # default
            assert config.get("onlyMp4") is False  # default

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "-g", "10", "-s", "-f", "test.mkv"])
    def test_debug_with_subtitle_options(self, mock_config):
        """Test debug logging with subtitle options"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with patch("mcoptions.get_system_locale", return_value="en"):
            options = parse_options()

            assert options.log_level == 10
            assert options.set_default_sub_track is True
            assert options.force_default_first_sub_track is True
            assert options.sources["log_level"] == "cli"
            assert options.sources["set_default_sub_track"] == "cli"
            assert options.sources["force_default_first_sub_track"] == "cli"


class TestErrorHandling:
    """Test CLI error handling"""

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__])
    def test_no_arguments_error(self, mock_config):
        """Test error when no arguments provided"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "--only-mkv", "--only-mp4", "test.mkv"])
    def test_conflicting_options_error(self, mock_config):
        """Test error with conflicting options"""

        def mock_get(key, default=None):
            if key == "language":
                return "en"
            return ""

        mock_config.get.side_effect = mock_get
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "-g", "999", "test.mkv"])
    def test_invalid_log_level_error(self, mock_config):
        """Test error with invalid log level"""
        mock_config.get.return_value = ""
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "--unknown-option", "test.mkv"])
    def test_unknown_option_error(self, mock_config):
        """Test error with unknown option"""
        mock_config.get.return_value = ""
        mock_config.log_file_path = "/tmp/test.log"

        with pytest.raises(SystemExit):
            parse_options()


class TestConfigIntegration:
    """Test integration between CLI and config"""

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "test.mkv"])
    def test_config_defaults_used(self, mock_config):
        """Test that config defaults are used when CLI options not provided"""
        mock_config.get.side_effect = lambda key, default=None: {
            "useSystemLocale": False,
            "language": "fr",
            "logLevel": 10,
            "setDefaultSubTrack": True,
            "forceDefaultFirstSubTrack": True,
            "onlyMkv": False,
            "onlyMp4": False,
            "mkvmergePath": "/custom/mkvmerge",
            "mkvpropeditPath": "/custom/mkvpropedit",
            "atomicParsleyPath": "/custom/AtomicParsley",
        }.get(key, default)
        mock_config.log_file_path = "/custom/log.log"

        options = parse_options()

        assert options.language == "fr"
        assert options.log_level == 10
        assert options.set_default_sub_track is True
        assert options.force_default_first_sub_track is True
        assert options.mkvmerge_path == "/custom/mkvmerge"
        assert options.mkvpropedit_path == "/custom/mkvpropedit"
        assert options.atomicparsley_path == "/custom/AtomicParsley"
        assert options.log_file_path == "/custom/log.log"

        # Check sources
        assert options.sources["language"] == "config"
        assert options.sources["log_level"] == "config"
        assert options.sources["mkvmerge_path"] == "config"

    @patch("mcoptions.mcconfig")
    @patch("sys.argv", [__app_name__, "-L", "es", "-g", "50", "test.mkv"])
    def test_cli_overrides_config(self, mock_config):
        """Test that CLI options override config values"""
        mock_config.get.side_effect = lambda key, default=None: {
            "useSystemLocale": False,
            "language": "fr",
            "logLevel": 10,
            "setDefaultSubTrack": True,
            "forceDefaultFirstSubTrack": True,
            "onlyMkv": False,
            "onlyMp4": False,
            "mkvmergePath": "/custom/mkvmerge",
            "mkvpropeditPath": "/custom/mkvpropedit",
            "atomicParsleyPath": "/custom/AtomicParsley",
        }.get(key, default)
        mock_config.log_file_path = "/custom/log.log"

        options = parse_options()

        # CLI should override config
        assert options.language == "es"
        assert options.log_level == 50

        # Config should still be used for non-overridden values
        assert options.set_default_sub_track is True
        assert options.mkvmerge_path == "/custom/mkvmerge"

        # Check sources
        assert options.sources["language"] == "cli"
        assert options.sources["log_level"] == "cli"
        assert options.sources["mkvmerge_path"] == "config"
