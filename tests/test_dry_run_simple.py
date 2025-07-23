"""
Tests for dry run functionality - simplified approach
"""

import os
import tempfile
from unittest.mock import patch

import main
from main import process_mp4_file


class TestDryRunSimple:
    """Test dry run mode with simplified mocking approach"""

    @patch("main.options")
    @patch("main.logger")
    @patch("main.time.perf_counter")
    def test_process_mp4_file_dry_run_execution_path(
        self, mock_perf_counter, mock_logger, mock_options
    ):
        """Test MP4 dry run execution path (lines 206-212)"""
        # Setup timing mocks
        mock_perf_counter.side_effect = [1000.0, 1005.0]  # 5 second difference

        # Setup options for dry run
        mock_options.dry_run = True

        # Mock global variables that get incremented
        main.files_processed = 0
        main.mp4_files_processed = 0
        main.mp4_processing_time = 0.0

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 content")
            tmp_file_path = tmp_file.name

        try:
            # Mock get_mp4_metadata to return valid metadata
            with patch("main.get_mp4_metadata") as mock_get_metadata:
                mock_get_metadata.return_value = {
                    "title": "Test Title",
                    "description": "Test Description",
                }

                # Call the function in dry run mode
                result = process_mp4_file(
                    tmp_file_path, atomicparsley_path="/usr/bin/AtomicParsley"
                )

                # Verify dry run logging (lines 206, 212)
                mock_logger.info.assert_any_call(
                    "DRY RUN: Would execute AtomicParsley command"
                )
                mock_logger.info.assert_any_call("Processing finished (dry run).")

                # Verify counters were incremented in dry run (lines 207-211)
                assert main.files_processed == 1
                assert main.mp4_files_processed == 1
                assert main.mp4_processing_time == 5.0  # 1005.0 - 1000.0

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
            # Reset global variables
            main.files_processed = 0
            main.mp4_files_processed = 0
            main.mp4_processing_time = 0.0

    @patch("main.options")
    @patch("main.logger")
    def test_mp4_dry_run_with_no_metadata(self, mock_logger, mock_options):
        """Test MP4 dry run when no metadata is found"""
        # Setup options for dry run
        mock_options.dry_run = True

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 content")
            tmp_file_path = tmp_file.name

        try:
            # Mock get_mp4_metadata to return no metadata
            with patch("main.get_mp4_metadata") as mock_get_metadata:
                mock_get_metadata.return_value = {}

                # Call the function - should skip processing
                result = process_mp4_file(
                    tmp_file_path, atomicparsley_path="/usr/bin/AtomicParsley"
                )

                # Should log no metadata and return None (skip dry run path)
                mock_logger.info.assert_any_call("No metadata found in file.")
                assert result is None

        finally:
            # Clean up
            Path(tmp_file_path).unlink()

    @patch("main.options")
    @patch("main.logger")
    def test_mp4_command_formatting_with_empty_strings(self, mock_logger, mock_options):
        """Test command formatting with empty strings for logging"""
        # Setup options for dry run to trigger command formatting
        mock_options.dry_run = True

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 content")
            tmp_file_path = tmp_file.name

        try:
            # Mock get_mp4_metadata to return metadata with empty values
            with patch("main.get_mp4_metadata") as mock_get_metadata:
                mock_get_metadata.return_value = {
                    "title": "",  # Empty string that should be formatted as ""
                    "description": "Test Description",
                }

                # Call the function
                result = process_mp4_file(
                    tmp_file_path, atomicparsley_path="/usr/bin/AtomicParsley"
                )

                # Should format empty strings as quoted in debug log
                # This tests the command formatting logic before dry run
                mock_logger.debug.assert_called()
                debug_calls = [
                    call
                    for call in mock_logger.debug.call_args_list
                    if "AtomicParsley command:" in str(call)
                ]
                assert len(debug_calls) > 0

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
