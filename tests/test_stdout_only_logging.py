"""
Tests for --stdout-only CLI option functionality
"""

import logging
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import main
from mclogger import Logger
from version import __app_name__


class TestStdoutOnlyLogging:
    """Test --stdout-only CLI option functionality"""

    def test_stdout_only_option_in_help(self):
        """Test that --stdout-only option appears in help text"""
        from mcoptions import _create_argument_parser

        parser = _create_argument_parser()
        help_text = parser.format_help()

        assert "--stdout-only" in help_text
        assert "-T" in help_text
        assert "console (stdout) only" in help_text
        assert "suppressing log file output" in help_text
        assert "DEBUG" in help_text

    def test_stdout_only_option_parsing(self):
        """Test that --stdout-only option is parsed correctly"""
        # Test with --stdout-only flag
        with patch("sys.argv", [__app_name__, "--stdout-only", "test.mkv"]):
            # Mock empty config to ensure we get default behavior
            with patch("mcoptions.mcconfig") as mock_config:
                mock_config.get.side_effect = lambda key, default=None: default

                from mcoptions import parse_options

                options = parse_options()

                assert options.stdout_only is True
                assert options.log_level == 20  # INFO level (default, not overridden)
                assert options.sources["stdout_only"] == "cli"
                assert options.sources["log_level"] == "default"

    def test_stdout_only_short_option_parsing(self):
        """Test that -O short option is parsed correctly"""
        # Test with -O flag
        with patch("sys.argv", [__app_name__, "-O", "test.mkv"]):
            # Mock empty config to ensure we get default behavior
            with patch("mcoptions.mcconfig") as mock_config:
                mock_config.get.side_effect = lambda key, default=None: default

                from mcoptions import parse_options

                options = parse_options()

                assert options.stdout_only is True
                assert options.log_level == 20  # INFO level (default, not overridden)
                assert options.sources["stdout_only"] == "cli"
                assert options.sources["log_level"] == "default"

    def test_stdout_only_option_disabled_by_default(self):
        """Test that stdout_only option is disabled by default"""
        with patch("sys.argv", [__app_name__, "test.mkv"]):
            # Mock the config to not have stdout_only setting, so it falls back to default
            with patch("mcoptions.mcconfig") as mock_config:
                mock_config.get.side_effect = lambda key, default=None: {
                    "logLevel": 20  # Standard config values, but no stdout_only
                }.get(key, default)

                from mcoptions import parse_options

                options = parse_options()

                assert options.stdout_only is False
                assert options.sources["stdout_only"] == "default"

    def test_stdout_only_does_not_override_log_level(self):
        """Test that --stdout-only does not override explicit log level"""
        # Test that --loglevel takes precedence over --stdout-only
        with patch(
            "sys.argv", [__app_name__, "--stdout-only", "--loglevel", "30", "test.mkv"]
        ):
            from mcoptions import parse_options

            options = parse_options()

            assert options.stdout_only is True
            assert options.log_level == 30  # WARNING (30), explicit setting honored
            assert options.sources["log_level"] == "cli"

    def test_logger_setup_with_stdout_only(self):
        """Test that logger setup correctly handles stdout_only option"""
        logger = Logger()

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Test setup with stdout_only enabled
            logger.setup(
                log_file_path=log_file_path, log_level=logging.DEBUG, stdout_only=True
            )

            # Should have only 1 handler: console (no file handler)
            assert len(logger.logger.handlers) == 1

            # Check handler type - should be StreamHandler only
            handler = logger.logger.handlers[0]
            assert isinstance(handler, logging.StreamHandler)

            # Check formatter - should be console format
            assert handler.formatter._fmt == "%(levelname)s: %(message)s"

        finally:
            # Clean up
            if Path(log_file_path).exists():
                Path(log_file_path).unlink()

    def test_logger_setup_with_both_stdout_and_stdout_only(self):
        """Test that stdout_only takes precedence and only creates console handler"""
        logger = Logger()

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Test setup with both stdout_enabled and stdout_only
            logger.setup(
                log_file_path=log_file_path,
                log_level=logging.DEBUG,
                stdout_enabled=True,
                stdout_only=True,
            )

            # Should have only 1 handler: console (stdout_only suppresses file)
            assert len(logger.logger.handlers) == 1

            # Check handler type
            handler = logger.logger.handlers[0]
            assert isinstance(handler, logging.StreamHandler)

        finally:
            # Clean up
            if Path(log_file_path).exists():
                Path(log_file_path).unlink()

    def test_logger_setup_without_stdout_only(self):
        """Test that logger setup works normally without stdout_only option"""
        logger = Logger()

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Test setup with stdout_only disabled (default)
            logger.setup(
                log_file_path=log_file_path, log_level=logging.INFO, stdout_only=False
            )

            # Should have only 1 handler: file
            assert len(logger.logger.handlers) == 1

            # Check handler type
            assert isinstance(logger.logger.handlers[0], logging.FileHandler)

        finally:
            # Clean up
            if Path(log_file_path).exists():
                Path(log_file_path).unlink()

    def test_stdout_only_with_main_function(self):
        """Test --stdout-only option in main() function integration"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Capture stdout
            captured_output = StringIO()

            # Mock sys.argv to simulate CLI execution with --stdout-only
            with patch(
                "sys.argv", [__app_name__, "--stdout-only", "--dry-run", tmp_file_path]
            ):
                # Mock parse_options to return test options
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=True,
                        stdout_only=True,
                        log_file_path="/tmp/test.log",
                        log_level=10,  # DEBUG
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock tool detection
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        # Mock process_mkv_file to avoid actual processing
                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.sys.exit"):
                                with patch("sys.stdout", captured_output):
                                    mock_process_mkv.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify output was captured (stdout was used)
                                    output = captured_output.getvalue()
                                    assert len(output) > 0

                                    # Should contain log messages
                                    assert "BEGINNING RUN" in output
                                    assert (
                                        "DEBUG:" in output
                                    )  # Should have DEBUG messages
                                    assert (
                                        "Python" in output
                                    )  # Should show Python version

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_stdout_only_config_file_option(self):
        """Test that stdout_only option can be set via config file"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Test with config file setting stdoutOnly = true
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                with patch("mcoptions.mcconfig") as mock_config:
                    # Mock config that has stdoutOnly = true
                    mock_config.get.side_effect = lambda key, default=None: {
                        "stdoutOnly": True,
                        "logLevel": 20,  # INFO, should be used as configured
                    }.get(key, default)

                    from mcoptions import parse_options

                    options = parse_options()

                    assert options.stdout_only is True
                    assert options.log_level == 20  # INFO, from config setting
                    assert options.sources["stdout_only"] == "config"
                    assert options.sources["log_level"] == "config"

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_stdout_only_cli_overrides_config(self):
        """Test that CLI --stdout-only overrides config file setting"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Test CLI overriding config (config has stdoutOnly = false, CLI has --stdout-only)
            with patch(
                "sys.argv", [__app_name__, "--stdout-only", "--dry-run", tmp_file_path]
            ), patch("mcoptions.mcconfig") as mock_config:
                # Mock config that has stdoutOnly = false
                mock_config.get.side_effect = lambda key, default=None: {
                    "stdoutOnly": False,
                    "logLevel": 30,  # WARNING
                }.get(key, default)

                from mcoptions import parse_options

                options = parse_options()

                assert options.stdout_only is True  # CLI overrides config
                assert options.log_level == 30  # WARNING from config
                assert options.sources["stdout_only"] == "cli"
                assert options.sources["log_level"] == "config"

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_stdout_only_vs_stdout_behavior(self):
        """Test that --stdout-only behaves differently from --stdout"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Test with --stdout-only
            with patch(
                "sys.argv", [__app_name__, "--stdout-only", "--dry-run", tmp_file_path]
            ):
                from mcoptions import parse_options

                stdout_only_options = parse_options()

            # Test with --stdout
            with patch(
                "sys.argv", [__app_name__, "--stdout", "--dry-run", tmp_file_path]
            ):
                from mcoptions import parse_options

                stdout_options = parse_options()

            # Both should have DEBUG log level
            assert stdout_only_options.log_level == 10
            assert stdout_options.log_level == 10

            # But only --stdout-only should have stdout_only enabled
            assert stdout_only_options.stdout_only is True
            assert stdout_only_options.stdout is False  # Regular stdout should be false

            assert stdout_options.stdout_only is False
            assert stdout_options.stdout is True

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_version_and_help_not_affected_by_stdout_only(self):
        """Test that --version and --help work normally even with --stdout-only"""
        # Test --version with --stdout-only
        with patch("sys.argv", [__app_name__, "--stdout-only", "--version"]):
            with patch("sys.exit"):
                try:
                    from mcoptions import parse_options

                    parse_options()
                except SystemExit:
                    # This is expected for --version
                    pass

        # Test --help with --stdout-only
        with patch("sys.argv", [__app_name__, "--stdout-only", "--help"]):
            with patch("sys.exit"):
                try:
                    from mcoptions import parse_options

                    parse_options()
                except SystemExit:
                    # This is expected for --help
                    pass
