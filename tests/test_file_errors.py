"""
Tests for file I/O error handling scenarios
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from main import read_paths_from_file


class TestFileErrorHandling:
    """Test file I/O error handling scenarios"""

    def test_read_paths_from_file_permission_denied(self):
        """Test reading paths from file with permission denied"""
        # Create a file and then remove read permissions
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("test.mkv\n")
            tmp_file_path = tmp_file.name

        try:
            # Remove read permissions
            os.chmod(tmp_file_path, 0o000)

            # Should exit with error code 1
            with pytest.raises(SystemExit) as exc_info:
                read_paths_from_file(tmp_file_path)

            assert exc_info.value.code == 1

        finally:
            # Restore permissions and clean up
            os.chmod(tmp_file_path, 0o644)
            Path(tmp_file_path).unlink()

    def test_read_paths_from_file_unicode_decode_error(self):
        """Test reading paths from file with invalid UTF-8 encoding"""
        # Create a file with invalid UTF-8 content
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp_file:
            # Write invalid UTF-8 bytes
            tmp_file.write(b"\xff\xfe\x00\x00invalid utf-8")
            tmp_file_path = tmp_file.name

        try:
            # Should exit with error code 1
            with pytest.raises(SystemExit) as exc_info:
                read_paths_from_file(tmp_file_path)

            assert exc_info.value.code == 1

        finally:
            # Clean up
            Path(tmp_file_path).unlink()

    @patch("main.open")
    def test_read_paths_from_file_general_exception(self, mock_file_open):
        """Test reading paths from file with general exception"""
        mock_file_open.side_effect = OSError("Unexpected I/O error")

        # Should exit with error code 1
        with pytest.raises(SystemExit) as exc_info:
            read_paths_from_file("test_file.txt")

        assert exc_info.value.code == 1

    def test_read_paths_from_file_empty_file(self):
        """Test reading paths from empty file"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            # Create empty file
            tmp_file_path = tmp_file.name

        try:
            result = read_paths_from_file(tmp_file_path)

            # Should return empty list
            assert result == []

        finally:
            # Clean up
            Path(tmp_file_path).unlink()

    @patch("main.logger")
    def test_read_paths_from_file_with_comments_and_empty_lines(self, mock_logger):
        """Test reading paths file with comments and empty lines"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("# This is a comment\n")
            tmp_file.write("\n")  # Empty line
            tmp_file.write("test1.mkv\n")
            tmp_file.write("# Another comment\n")
            tmp_file.write("   \n")  # Whitespace only
            tmp_file.write("test2.mp4\n")
            tmp_file_path = tmp_file.name

        try:
            result = read_paths_from_file(tmp_file_path)

            # Should return empty list since paths don't exist
            assert result == []

            # Should log warnings for non-existent paths
            mock_logger.warning.assert_called()

        finally:
            # Clean up
            Path(tmp_file_path).unlink()

    @patch("main.logger")
    def test_read_paths_from_file_dos_line_endings(self, mock_logger):
        """Test reading paths file with DOS line endings"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tmp_file:
            # Write content with DOS line endings (\r\n)
            tmp_file.write(b"test1.mkv\r\n")
            tmp_file.write(b"test2.mp4\r\n")
            tmp_file_path = tmp_file.name

        try:
            result = read_paths_from_file(tmp_file_path)

            # Should return empty list since paths don't exist
            assert result == []

            # Should log warnings for non-existent paths
            mock_logger.warning.assert_called()

        finally:
            # Clean up
            Path(tmp_file_path).unlink()

    @patch("main.logger")
    def test_read_paths_from_file_nonexistent_paths(self, mock_logger):
        """Test reading paths file where listed paths don't exist"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("/nonexistent/path1.mkv\n")
            tmp_file.write("/another/nonexistent/path2.mp4\n")
            tmp_file_path = tmp_file.name

        try:
            result = read_paths_from_file(tmp_file_path)

            # Should return empty list since paths don't exist
            assert result == []

            # Should log warnings for non-existent paths
            mock_logger.warning.assert_called()

        finally:
            # Clean up
            Path(tmp_file_path).unlink()

    @patch("main.logger")
    def test_read_paths_from_file_with_logging(self, mock_logger):
        """Test that file reading errors are properly logged"""
        # Create a file and then remove read permissions
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("test.mkv\n")
            tmp_file_path = tmp_file.name

        try:
            # Remove read permissions
            os.chmod(tmp_file_path, 0o000)

            # Should log permission error
            with pytest.raises(SystemExit):
                read_paths_from_file(tmp_file_path)

            # Verify error was logged
            mock_logger.error.assert_called()
            error_calls = [
                call
                for call in mock_logger.error.call_args_list
                if "Permission denied" in str(call)
            ]
            assert len(error_calls) > 0

        finally:
            # Restore permissions and clean up
            os.chmod(tmp_file_path, 0o644)
            Path(tmp_file_path).unlink()
