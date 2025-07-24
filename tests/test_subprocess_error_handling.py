"""
Tests for subprocess error handling and tool missing scenarios
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import main
from main import get_mkv_metadata, get_mp4_metadata, process_mkv_file, process_mp4_file
from .test_helpers import setup_complete_mock_options


class TestSubprocessErrorHandling:
    """Test subprocess error handling and tool missing scenarios"""

    @patch("main.options")
    @patch("main.logger")
    @patch("main.mkvpropedit", None)  # Mock global variable as None
    def test_process_mkv_file_mkvpropedit_missing(self, mock_logger, mock_options):
        """Test MKV processing when mkvpropedit is missing (lines 93-94)"""
        mock_options.configure_mock(**setup_complete_mock_options(dry_run=False).__dict__)

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Call with no mkvpropedit tool (both parameter and global None)
            result = process_mkv_file(
                tmp_file_path, mkvpropedit_path=None, mkvmerge_path="/usr/bin/mkvmerge"
            )

            # Should log missing tool and return None (lines 90-91)
            mock_logger.info.assert_called_with(
                "mkvpropedit not found in PATH. Skipping."
            )
            assert result is None

        finally:
            Path(tmp_file_path).unlink()

    @patch("main.options")
    @patch("main.logger")
    @patch("main.mkvmerge", None)  # Mock global variable as None
    def test_process_mkv_file_mkvmerge_missing(self, mock_logger, mock_options):
        """Test MKV processing when mkvmerge is missing (lines 93-94)"""
        mock_options.configure_mock(**setup_complete_mock_options(dry_run=False).__dict__)

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Call with no mkvmerge tool (both parameter and global None)
            result = process_mkv_file(
                tmp_file_path,
                mkvpropedit_path="/usr/bin/mkvpropedit",
                mkvmerge_path=None,
            )

            # Should log missing tool and return None (lines 92-94)
            mock_logger.info.assert_called_with("mkvmerge not found in PATH. Skipping.")
            assert result is None

        finally:
            Path(tmp_file_path).unlink()

    @patch("main.mkvmerge", None)  # Mock global variable as None
    def test_get_mkv_metadata_missing_tool_runtime_error(self):
        """Test get_mkv_metadata raises RuntimeError when tool is missing (line 301)"""
        # Should raise RuntimeError when mkvmerge tool is not available (line 301)
        with pytest.raises(RuntimeError, match="mkvmerge tool not available"):
            get_mkv_metadata("test.mkv", mkvmerge_path=None)

    @patch("main.atomicparsley", None)  # Mock global variable as None
    def test_get_mp4_metadata_missing_tool_runtime_error(self):
        """Test get_mp4_metadata raises RuntimeError when tool is missing (line 332)"""
        # Should raise RuntimeError when AtomicParsley tool is not available (line 332)
        with pytest.raises(RuntimeError, match="AtomicParsley tool not available"):
            get_mp4_metadata("test.mp4", atomicparsley_path=None)

    @patch("main.options")
    @patch("main.logger")
    @patch("main.atomicparsley", None)  # Mock global variable as None
    def test_process_mp4_file_atomicparsley_missing(self, mock_logger, mock_options):
        """Test MP4 processing when AtomicParsley is missing"""
        mock_options.configure_mock(**setup_complete_mock_options(dry_run=False).__dict__)

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 content")
            tmp_file_path = tmp_file.name

        try:
            # Call with no AtomicParsley tool (both parameter and global None)
            result = process_mp4_file(tmp_file_path, atomicparsley_path=None)

            # Should log missing tool and return None
            mock_logger.info.assert_called_with(
                "AtomicParsley not found in PATH. Skipping."
            )
            assert result is None

        finally:
            Path(tmp_file_path).unlink()

    @patch("main.options")
    @patch("main.logger")
    def test_process_folder_nonexistent_folder(self, mock_logger, mock_options):
        """Test folder processing with non-existent folder (lines 250-252)"""
        mock_options.configure_mock(**setup_complete_mock_options(only_mkv=False, only_mp4=False).__dict__)

        # Reset global error counters
        main.folders_errored = 0

        try:
            # Call with non-existent folder path
            from main import process_folder

            process_folder("/nonexistent/folder/path")

            # Should log error and increment counter (lines 245-247)
            mock_logger.error.assert_called_with(
                "Folder does not exist: /nonexistent/folder/path"
            )
            assert main.folders_errored == 1

        finally:
            # Reset global variables
            main.folders_errored = 0

    @patch("main.options")
    @patch("main.logger")
    def test_process_folder_not_directory(self, mock_logger, mock_options):
        """Test folder processing with file instead of directory (lines 250-252)"""
        mock_options.configure_mock(**setup_complete_mock_options(only_mkv=False, only_mp4=False).__dict__)

        # Reset global error counters
        main.folders_errored = 0

        # Create a temporary file (not directory)
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file_path = tmp_file.name

        try:
            # Call with file path instead of folder
            from main import process_folder

            process_folder(tmp_file_path)

            # Should log error and increment counter (lines 249-252)
            mock_logger.error.assert_called_with(
                f"Path is not a directory: {tmp_file_path}"
            )
            assert main.folders_errored == 1

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
            main.folders_errored = 0

    @patch("main.options")
    @patch("main.logger")
    def test_process_folder_general_exception(self, mock_logger, mock_options):
        """Test folder processing with general exception (lines 268-270)"""
        mock_options.configure_mock(**setup_complete_mock_options(only_mkv=False, only_mp4=False).__dict__)

        # Reset global error counters
        main.folders_errored = 0

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock os.walk to raise an exception
            with patch("main.os.walk") as mock_walk:
                mock_walk.side_effect = PermissionError("Access denied")

                try:
                    from main import process_folder

                    process_folder(tmp_dir)

                    # Should log error and increment counter (lines 268-270)
                    mock_logger.error.assert_called_with(
                        f"Error processing folder {tmp_dir}: Access denied"
                    )
                    assert main.folders_errored == 1

                finally:
                    main.folders_errored = 0
