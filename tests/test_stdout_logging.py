"""
Tests for --stdout CLI option functionality
"""

import logging
import os
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import main
from mclogger import Logger


class TestStdoutLogging:
    """Test --stdout CLI option functionality"""

    def test_stdout_option_in_help(self):
        """Test that --stdout option appears in help text"""
        from mcoptions import _create_argument_parser

        parser = _create_argument_parser()
        help_text = parser.format_help()

        assert "--stdout" in help_text
        assert "-S" in help_text
        assert "console (stdout)" in help_text
        assert "DEBUG" in help_text

    def test_stdout_option_parsing(self):
        """Test that --stdout option is parsed correctly"""
        # Test with --stdout flag
        with patch("sys.argv", [__app_name__, "--stdout", "test.mkv"]):
            from mcoptions import parse_options

            options = parse_options()

            assert options.stdout is True
            assert options.log_level == 10  # DEBUG level
            assert options.sources["stdout"] == "cli"
            assert options.sources["log_level"] == "stdout option"

    def test_stdout_short_option_parsing(self):
        """Test that -S short option is parsed correctly"""
        # Test with -S flag
        with patch("sys.argv", [__app_name__, "-S", "test.mkv"]):
            from mcoptions import parse_options

            options = parse_options()

            assert options.stdout is True
            assert options.log_level == 10  # DEBUG level
            assert options.sources["stdout"] == "cli"
            assert options.sources["log_level"] == "stdout option"

    def test_stdout_option_disabled_by_default(self):
        """Test that stdout option is disabled by default"""
        with patch("sys.argv", [__app_name__, "test.mkv"]):
            # Mock the config to not have stdout setting, so it falls back to default
            with patch("mcoptions.mcconfig") as mock_config:
                mock_config.get.side_effect = lambda key, default=None: {
                    "logLevel": 20  # Standard config values, but no stdout
                }.get(key, default)

                from mcoptions import parse_options

                options = parse_options()

                assert options.stdout is False
                assert options.sources["stdout"] == "default"

    def test_stdout_overrides_log_level(self):
        """Test that --stdout overrides explicit log level"""
        # Test that --stdout takes precedence over --loglevel
        with patch(
            "sys.argv", [__app_name__, "--stdout", "--loglevel", "30", "test.mkv"]
        ):
            from mcoptions import parse_options

            options = parse_options()

            assert options.stdout is True
            assert options.log_level == 10  # DEBUG, not WARNING (30)
            assert options.sources["log_level"] == "stdout option"

    def test_logger_setup_with_stdout(self):
        """Test that logger setup correctly handles stdout option"""
        logger = Logger()

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Test setup with stdout enabled
            logger.setup(
                log_file_path=log_file_path,
                log_level=logging.DEBUG,
                stdout_enabled=True,
            )

            # Should have 2 handlers: file and console
            assert len(logger.logger.handlers) == 2

            # Check handler types
            handler_types = [type(handler) for handler in logger.logger.handlers]
            assert logging.FileHandler in handler_types
            assert logging.StreamHandler in handler_types

            # Find the StreamHandler that was explicitly added for stdout
            # (there might be multiple StreamHandlers, so we check for the right formatter)
            stdout_handler = None
            for h in logger.logger.handlers:
                if (
                    isinstance(h, logging.StreamHandler)
                    and h.formatter._fmt == "%(levelname)s: %(message)s"
                ):
                    stdout_handler = h
                    break

            assert (
                stdout_handler is not None
            ), "Could not find stdout StreamHandler with correct formatter"

        finally:
            # Clean up
            if Path(log_file_path).exists():
                Path(log_file_path).unlink()

    def test_logger_setup_without_stdout(self):
        """Test that logger setup works normally without stdout option"""
        logger = Logger()

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            # Test setup with stdout disabled (default)
            logger.setup(
                log_file_path=log_file_path,
                log_level=logging.INFO,
                stdout_enabled=False,
            )

            # Should have only 1 handler: file
            assert len(logger.logger.handlers) == 1

            # Check handler type
            assert isinstance(logger.logger.handlers[0], logging.FileHandler)

        finally:
            # Clean up
            if Path(log_file_path).exists():
                Path(log_file_path).unlink()

    def test_console_formatter_different_from_file(self):
        """Test that console and file use different formatters"""
        logger = Logger()

        # Create temporary log file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            log_file_path = tmp_file.name

        try:
            logger.setup(
                log_file_path=log_file_path,
                log_level=logging.DEBUG,
                stdout_enabled=True,
            )

            file_handler = next(
                h for h in logger.logger.handlers if isinstance(h, logging.FileHandler)
            )

            # Find the console handler specifically by its formatter
            console_handler = None
            for h in logger.logger.handlers:
                if (
                    isinstance(h, logging.StreamHandler)
                    and h.formatter._fmt == "%(levelname)s: %(message)s"
                ):
                    console_handler = h
                    break

            assert console_handler is not None, "Could not find console StreamHandler"

            # File formatter should include timestamp
            file_format = file_handler.formatter._fmt
            assert "%(asctime)s" in file_format
            assert "%(levelname)s" in file_format
            assert "%(message)s" in file_format

            # Console formatter should be simpler
            console_format = console_handler.formatter._fmt
            assert console_format == "%(levelname)s: %(message)s"
            assert "%(asctime)s" not in console_format  # No timestamp for console
            assert "%(levelname)s" in console_format
            assert "%(message)s" in console_format

        finally:
            # Clean up
            if Path(log_file_path).exists():
                Path(log_file_path).unlink()

    def test_stdout_with_main_function(self):
        """Test --stdout option in main() function integration"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Capture stdout
            captured_output = StringIO()

            # Mock sys.argv to simulate CLI execution with --stdout
            with patch(
                "sys.argv", [__app_name__, "--stdout", "--dry-run", tmp_file_path]
            ):
                # Mock parse_options to return test options
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=True,
                        stdout=True,
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
                            with patch("main.sys.exit") as mock_exit:
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

    def test_version_and_help_not_affected_by_stdout(self):
        """Test that --version and --help work normally even with --stdout"""
        # Test --version with --stdout
        with patch("sys.argv", [__app_name__, "--stdout", "--version"]):
            with patch("sys.exit") as mock_exit:
                try:
                    from mcoptions import parse_options

                    parse_options()
                except SystemExit:
                    # This is expected for --version
                    pass

        # Test --help with --stdout
        with patch("sys.argv", [__app_name__, "--stdout", "--help"]):
            with patch("sys.exit") as mock_exit:
                try:
                    from mcoptions import parse_options

                    parse_options()
                except SystemExit:
                    # This is expected for --help
                    pass

    def test_stdout_option_equivalence(self):
        """Test that --stdout acts like --loglevel 10 with console output"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Test with --stdout
            with patch(
                "sys.argv", [__app_name__, "--stdout", "--dry-run", tmp_file_path]
            ):
                from mcoptions import parse_options

                stdout_options = parse_options()

            # Test with --loglevel 10
            with patch(
                "sys.argv",
                [__app_name__, "--loglevel", "10", "--dry-run", tmp_file_path],
            ):
                from mcoptions import parse_options

                loglevel_options = parse_options()

            # Both should have DEBUG log level
            assert stdout_options.log_level == 10
            assert loglevel_options.log_level == 10

            # But only --stdout should have stdout enabled
            assert stdout_options.stdout is True
            assert loglevel_options.stdout is False

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_stdout_config_file_option(self):
        """Test that stdout option can be set via config file"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Test with config file setting stdout = true
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                with patch("mcoptions.mcconfig") as mock_config:
                    # Mock config that has stdout = true
                    mock_config.get.side_effect = lambda key, default=None: {
                        "stdout": True,
                        "logLevel": 20,  # INFO, but should be overridden by stdout
                    }.get(key, default)

                    from mcoptions import parse_options

                    options = parse_options()

                    assert options.stdout is True
                    assert options.log_level == 10  # DEBUG, overridden by stdout
                    assert options.sources["stdout"] == "config"
                    assert options.sources["log_level"] == "stdout option"

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_stdout_cli_overrides_config(self):
        """Test that CLI --stdout overrides config file setting"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Test CLI overriding config (config has stdout = false, CLI has --stdout)
            with patch(
                "sys.argv", [__app_name__, "--stdout", "--dry-run", tmp_file_path]
            ):
                with patch("mcoptions.mcconfig") as mock_config:
                    # Mock config that has stdout = false
                    mock_config.get.side_effect = lambda key, default=None: {
                        "stdout": False,
                        "logLevel": 30,  # WARNING
                    }.get(key, default)

                    from mcoptions import parse_options

                    options = parse_options()

                    assert options.stdout is True  # CLI overrides config
                    assert options.log_level == 10  # DEBUG from stdout
                    assert options.sources["stdout"] == "cli"
                    assert options.sources["log_level"] == "stdout option"

        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()
