"""
Tests for folder processing error scenarios
"""

import os
import tempfile
from unittest.mock import patch

import main
from main import process_folder


class TestFolderProcessing:
    """Test folder processing error handling"""

    @patch("main.logger")
    def test_process_folder_not_a_directory(self, mock_logger):
        """Test folder processing when path is not a directory (lines 250-252)"""
        # Create a regular file (not a directory)
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b"not a directory")
            file_path = tmp_file.name

        try:
            # Mock global variables
            main.folders_errored = 0

            # Call process_folder with a file path instead of directory
            process_folder(file_path)

            # Should log error and increment counter (lines 250-252)
            mock_logger.error.assert_any_call(f"Path is not a directory: {file_path}")
            assert main.folders_errored == 1

        finally:
            # Clean up
            os.unlink(file_path)
            main.folders_errored = 0

    @patch("main.logger")
    def test_process_folder_does_not_exist(self, mock_logger):
        """Test folder processing when folder does not exist"""
        nonexistent_path = "/tmp/definitely_does_not_exist_folder_12345"

        # Mock global variables
        main.folders_errored = 0

        # Call process_folder with non-existent path
        process_folder(nonexistent_path)

        # Should log error and increment counter
        mock_logger.error.assert_any_call(f"Folder does not exist: {nonexistent_path}")
        assert main.folders_errored == 1

        # Reset
        main.folders_errored = 0

    @patch("main.logger")
    @patch("os.walk")
    def test_process_folder_general_exception(self, mock_walk, mock_logger):
        """Test folder processing with general exception (lines 268-270)"""
        # Create a real directory for testing
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock os.walk to raise an exception
            mock_walk.side_effect = PermissionError(
                "Permission denied accessing directory"
            )

            # Mock global variables
            main.folders_errored = 0

            # Call process_folder - should catch exception
            process_folder(tmp_dir)

            # Should log error and increment counter (lines 268-270)
            mock_logger.error.assert_any_call(
                f"Error processing folder {tmp_dir}: Permission denied accessing directory"
            )
            assert main.folders_errored == 1

            # Reset
            main.folders_errored = 0

    @patch("main.logger")
    @patch("main.process_mkv_file")
    def test_process_folder_success_path(self, mock_process_mkv_file, mock_logger):
        """Test successful folder processing to hit line 266"""
        # Create a directory with a test file
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = os.path.join(tmp_dir, "test.mkv")
            with open(test_file, "w") as f:
                f.write("fake content")

            # Mock process_mkv_file to avoid actual processing
            mock_process_mkv_file.return_value = None

            # Mock global variables
            main.folders_processed = 0

            # Mock options to avoid only_mp4 filter
            with patch("main.options") as mock_options:
                mock_options.only_mp4 = False

                # Call process_folder
                process_folder(tmp_dir)

            # Should increment folders_processed counter (line 266)
            assert main.folders_processed == 1

            # Should have called process_mkv_file for the test file
            mock_process_mkv_file.assert_called()

            # Reset
            main.folders_processed = 0

    @patch("main.logger")
    @patch("os.walk")
    def test_process_folder_os_error_exception(self, mock_walk, mock_logger):
        """Test folder processing with OSError exception"""
        # Create a real directory for testing
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Mock os.walk to raise an OSError
            mock_walk.side_effect = OSError("I/O error accessing directory")

            # Mock global variables
            main.folders_errored = 0

            # Call process_folder - should catch exception
            process_folder(tmp_dir)

            # Should log error and increment counter (lines 268-270)
            mock_logger.error.assert_any_call(
                f"Error processing folder {tmp_dir}: I/O error accessing directory"
            )
            assert main.folders_errored == 1

            # Reset
            main.folders_errored = 0
