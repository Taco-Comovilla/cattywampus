"""
CLI integration tests to cover main() function execution paths
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import main

from .test_helpers import create_mock_options
from version import __app_name__


class TestCLIIntegration:
    """Test CLI integration scenarios that exercise main() function"""

    def test_main_function_basic_execution(self):
        """Test basic main() function execution with minimal args"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(paths=[tmp_file_path])
                    mock_parse_options.return_value = mock_options

                    # Mock tools to avoid actual processing
                    with patch("main.shutil.which") as mock_which:
                        # Mock tools as found
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        # Mock the processing functions to avoid actual file modification
                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Call main function - this should exercise lines 457-649
                                    main.main()

                                    # Verify basic execution path was followed
                                    mock_logger.info.assert_any_call(
                                        "*" * 20 + " BEGINNING RUN " + "*" * 20
                                    )
                                    mock_logger.info.assert_any_call(
                                        "*" * 20 + " ENDING RUN " + "*" * 23
                                    )
                                    mock_process_mkv.assert_called_once()
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_dry_run_mode(self):
        """Test main() function in dry run mode"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_file:
            tmp_file.write(b"fake mp4 content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution with dry run
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path], dry_run=True
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock tools as found
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        # Mock the processing functions
                        with patch("main.process_mp4_file") as mock_process_mp4:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mp4.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify dry run logging (lines 510-511)
                                    mock_logger.info.assert_any_call(
                                        "*" * 23 + " DRY RUN " + "*" * 23
                                    )
                                    mock_process_mp4.assert_called_once()
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_no_tools_found_exit(self):
        """Test main() function exits when no tools are found (lines 584-586)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(paths=[tmp_file_path])
                    mock_parse_options.return_value = mock_options

                    # Mock all tools as not found
                    with patch("main.shutil.which", return_value=None):
                        with patch("main.logger") as mock_logger:
                            with patch("main.sys.exit") as mock_exit:

                                # Call main function - should exit early
                                main.main()

                                # Verify critical error and exit (lines 584-586)
                                mock_logger.critical.assert_any_call(
                                    "neither mkvtoolnix nor AtomicParsley found in PATH. Exiting."
                                )
                                mock_exit.assert_called()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_input_file_processing(self):
        """Test main() function with input file (lines 475-477)"""
        # Create temporary test files
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as test_file:
            test_file.write(b"fake mkv content")
            test_file_path = test_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False
        ) as input_file:
            input_file.write(f"{test_file_path}\n")
            input_file_path = input_file.name

        try:
            # Mock sys.argv to simulate CLI execution with input file
            with patch("sys.argv", [__app_name__, "--input-file", input_file_path]):
                # Mock tools as found
                with patch("main.shutil.which") as mock_which:
                    mock_which.side_effect = lambda tool: (
                        f"/usr/bin/{tool}" if tool else None
                    )

                    # Mock the processing functions
                    with patch("main.process_mkv_file") as mock_process_mkv:
                        with patch("main.logger") as mock_logger:
                            with patch("main.sys.exit") as mock_exit:
                                mock_process_mkv.return_value = None

                                # Call main function
                                main.main()

                                # Verify input file was processed (lines 475-477)
                                mock_logger.debug.assert_any_call(
                                    f"Added 1 path from input file: {input_file_path}"
                                )
                                mock_process_mkv.assert_called_once()
                                mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(test_file_path).exists():
                Path(test_file_path).unlink()
            if Path(input_file_path).exists():
                Path(input_file_path).unlink()

    def test_main_function_folder_processing(self):
        """Test main() function with folder processing (lines 623-624)"""
        # Create a temporary directory with a test file
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_file = str(Path(tmp_dir) / "test.mkv")
            with open(test_file, "w") as f:
                f.write("fake content")

            # Mock sys.argv to simulate CLI execution with folder
            with patch("sys.argv", [__app_name__, tmp_dir]):
                # Mock tools as found
                with patch("main.shutil.which") as mock_which:
                    mock_which.side_effect = lambda tool: (
                        f"/usr/bin/{tool}" if tool else None
                    )

                    # Mock the processing functions
                    with patch("main.process_folder") as mock_process_folder:
                        with patch("main.logger") as mock_logger:
                            with patch("main.sys.exit") as mock_exit:
                                mock_process_folder.return_value = None

                                # Call main function
                                main.main()

                                # Verify folder processing (lines 623-624)
                                mock_process_folder.assert_called_once_with(tmp_dir)
                                mock_exit.assert_called_once()

    def test_main_function_tool_version_detection(self):
        """Test main() function tool version detection (lines 593-615)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock tools as found
                with patch("main.shutil.which") as mock_which:
                    mock_which.side_effect = lambda tool: (
                        f"/usr/bin/{tool}" if tool else None
                    )

                    # Mock tool version detection
                    with patch("main.get_tool_version") as mock_get_version:
                        mock_get_version.return_value = "Tool version 1.2.3"

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify tool version logging (lines 593-615)
                                    mock_logger.info.assert_any_call(
                                        "mkvpropedit version: Tool version 1.2.3"
                                    )
                                    mock_logger.info.assert_any_call(
                                        "mkvmerge version: Tool version 1.2.3"
                                    )
                                    mock_logger.info.assert_any_call(
                                        "AtomicParsley version: Tool version 1.2.3"
                                    )
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()
