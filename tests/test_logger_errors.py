"""
Tests for logger error conditions and edge cases
"""

import tempfile
from unittest.mock import patch

import pytest

import mclogger
from mclogger import logger


class TestLoggerErrors:
    """Test logger error handling and edge cases"""

    @patch("mclogger.logging.FileHandler")
    def test_logger_setup_makedirs_permission_error(self, mock_file_handler):
        """Test logger setup when file handler creation fails due to permissions"""
        mock_file_handler.side_effect = PermissionError("Permission denied")

        # This should raise a PermissionError since the logger doesn't handle it gracefully
        with tempfile.NamedTemporaryFile() as tmp_file:
            with pytest.raises(PermissionError, match="Permission denied"):
                logger.setup(log_file_path=tmp_file.name, log_level=20)

    def test_logger_setup_invalid_log_level(self):
        """Test logger setup with invalid log level"""
        with tempfile.NamedTemporaryFile() as tmp_file:
            # Should handle invalid log levels gracefully
            logger.setup(log_file_path=tmp_file.name, log_level=999)
            # Logger should still be functional
            assert logger.logger is not None

    def test_logger_setup_with_nonexistent_directory(self):
        """Test logger setup with a path in a non-existent directory"""
        # Use a path that definitely doesn't exist
        nonexistent_path = "/tmp/definitely_does_not_exist_12345/test.log"

        # Should raise FileNotFoundError since the logger doesn't create directories
        with pytest.raises(FileNotFoundError):
            logger.setup(log_file_path=nonexistent_path, log_level=20)

    @patch("mclogger.sys.stdout.isatty")
    def test_logger_non_interactive_detection(self, mock_isatty):
        """Test logger behavior in non-interactive environments"""
        mock_isatty.return_value = False

        with tempfile.NamedTemporaryFile() as tmp_file:
            logger.setup(log_file_path=tmp_file.name, log_level=20)

            # Should still work in non-interactive mode
            logger.info("Test message")
            assert logger.logger is not None

    @patch("mclogger.sys.stdout.isatty")
    def test_logger_interactive_detection(self, mock_isatty):
        """Test logger behavior in interactive environments"""
        mock_isatty.return_value = True

        with tempfile.NamedTemporaryFile() as tmp_file:
            logger.setup(log_file_path=tmp_file.name, log_level=20)

            # Should work in interactive mode
            logger.info("Test message")
            assert logger.logger is not None

    def test_logger_setup_with_empty_log_path(self):
        """Test logger setup with empty log file path"""
        # Should raise an error with empty path
        with pytest.raises((FileNotFoundError, OSError)):
            logger.setup(log_file_path="", log_level=20)

    def test_logger_multiple_setup_calls(self):
        """Test that multiple logger setup calls work correctly"""
        with tempfile.NamedTemporaryFile() as tmp_file1:
            with tempfile.NamedTemporaryFile() as tmp_file2:
                # First setup
                logger.setup(log_file_path=tmp_file1.name, log_level=20)
                first_logger = logger.logger

                # Second setup should work
                logger.setup(log_file_path=tmp_file2.name, log_level=10)
                second_logger = logger.logger

                # Should have updated the logger
                assert first_logger is not None
                assert second_logger is not None

    @patch("mclogger.logging.FileHandler")
    def test_logger_file_handler_creation_error(self, mock_file_handler):
        """Test logger behavior when file handler creation fails"""
        mock_file_handler.side_effect = OSError("Cannot create file handler")

        with tempfile.NamedTemporaryFile() as tmp_file:
            # Should raise the IOError since the logger doesn't handle it gracefully
            with pytest.raises(IOError, match="Cannot create file handler"):
                logger.setup(log_file_path=tmp_file.name, log_level=20)

    def test_logger_functions_before_setup(self):
        """Test that logger functions work even before setup is called"""
        # Create a fresh logger instance
        fresh_logger = mclogger.Logger()

        # These should not raise exceptions
        fresh_logger.debug("Debug message")
        fresh_logger.info("Info message")
        fresh_logger.error("Error message")
        fresh_logger.critical("Critical message")

        # Logger should always exist
        assert fresh_logger.logger is not None
