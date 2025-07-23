"""
Tests for logger error conditions and edge cases
"""

import logging
import tempfile
from unittest.mock import patch

import mclogger
from mclogger import logger


class TestLoggerErrors:
    """Test logger error handling and edge cases"""

    @patch("mclogger.logging.FileHandler")
    def test_logger_setup_makedirs_permission_error(self, mock_file_handler):
        """Test logger setup when file handler creation fails due to permissions"""
        mock_file_handler.side_effect = PermissionError("Permission denied")

        # Logger should handle the error gracefully and fall back to stderr
        with tempfile.NamedTemporaryFile() as tmp_file:
            # Should not raise an exception
            logger.setup(log_file_path=tmp_file.name, log_level=20)

            # Should have a stderr handler since file handler failed
            assert len(logger.logger.handlers) >= 1
            # At least one handler should be a StreamHandler (stderr fallback)
            stream_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(stream_handlers) >= 1

    def test_logger_setup_invalid_log_level(self):
        """Test logger setup with invalid log level"""
        with tempfile.NamedTemporaryFile() as tmp_file:
            # Should handle invalid log levels gracefully
            logger.setup(log_file_path=tmp_file.name, log_level=999)
            # Logger should still be functional
            assert logger.logger is not None

    def test_logger_setup_with_nonexistent_directory(self):
        """Test logger setup with a path in a non-existent directory"""
        from pathlib import Path

        # Use a path that definitely doesn't exist
        nonexistent_path = "/tmp/definitely_does_not_exist_12345/test.log"

        # Logger should create the directory and succeed
        logger.setup(log_file_path=nonexistent_path, log_level=20)

        # Directory should now exist
        assert Path(nonexistent_path).parent.exists()

        # Clean up
        if Path(nonexistent_path).exists():
            Path(nonexistent_path).unlink()
        if Path(nonexistent_path).parent.exists():
            Path(nonexistent_path).parent.rmdir()

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
        # Logger should handle empty path gracefully and fall back to stderr
        logger.setup(log_file_path="", log_level=20)

        # Should have at least one handler (stderr fallback)
        assert len(logger.logger.handlers) >= 1
        # Should have a StreamHandler for stderr fallback
        stream_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

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
            # Logger should handle the error gracefully and fall back to stderr
            logger.setup(log_file_path=tmp_file.name, log_level=20)

            # Should have at least one handler (stderr fallback)
            assert len(logger.logger.handlers) >= 1
            # Should have a StreamHandler for stderr fallback
            stream_handlers = [h for h in logger.logger.handlers if isinstance(h, logging.StreamHandler)]
            assert len(stream_handlers) >= 1

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
