"""
Tests for remaining main() function edge cases and conditional paths
"""

import os
import tempfile
from unittest.mock import patch

import main
from version import __app_name__

from .test_helpers import create_mock_options


class TestMainFunctionEdgeCases:
    """Test remaining main() function edge cases and conditional logic"""

    def test_main_function_input_file_path_processing(self):
        """Test main() function input file path processing (lines 476-477)"""
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
            with patch("sys.argv", [__app_name__, "-i", input_file_path]):
                # Mock parse_options to return input file option
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[], input_file=input_file_path  # No direct paths
                    )
                    mock_parse_options.return_value = mock_options

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

                                    # Verify input file path was added (lines 476-477)
                                    mock_logger.debug.assert_any_call(
                                        f"Added 1 path from input file: {input_file_path}"
                                    )
                                    mock_process_mkv.assert_called_once()
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(test_file_path):
                os.unlink(test_file_path)
            if os.path.exists(input_file_path):
                os.unlink(input_file_path)

    def test_main_function_file_type_filtering_mkv_only(self):
        """Test main() function file type filtering with --only-mkv (lines 495-507)"""
        # Create temporary test files of different types
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as mkv_file:
            mkv_file.write(b"fake mkv content")
            mkv_file_path = mkv_file.name

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as mp4_file:
            mp4_file.write(b"fake mp4 content")
            mp4_file_path = mp4_file.name

        try:
            # Mock sys.argv with both file types and --only-mkv
            with patch(
                "sys.argv", [__app_name__, "--only-mkv", mkv_file_path, mp4_file_path]
            ):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[mkv_file_path, mp4_file_path], only_mkv=True
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock tools as found
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.process_mp4_file") as mock_process_mp4:
                                with patch("main.logger") as mock_logger:
                                    with patch("main.sys.exit") as mock_exit:
                                        mock_process_mkv.return_value = None
                                        mock_process_mp4.return_value = None

                                        # Call main function
                                        main.main()

                                        # Verify filtering logged (lines 524-527)
                                        mock_logger.debug.assert_any_call(
                                            "Filtered out 1 MP4/M4V file"
                                        )
                                        mock_logger.debug.assert_any_call(
                                            "Processing 1 unique path"
                                        )

                                        # Should only process MKV file
                                        mock_process_mkv.assert_called_once()
                                        mock_process_mp4.assert_not_called()
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            for path in [mkv_file_path, mp4_file_path]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_main_function_path_deduplication_logging(self):
        """Test main() function path deduplication logging (lines 531-533)"""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

            # Create different ways to reference the same file
            abs_path = os.path.abspath(tmp_file_path)
            rel_path = os.path.relpath(tmp_file_path)

        try:
            # Mock sys.argv with duplicate paths
            duplicate_paths = [tmp_file_path, abs_path, rel_path, tmp_file_path]
            with patch("sys.argv", [__app_name__] + duplicate_paths):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(paths=duplicate_paths)
                    mock_parse_options.return_value = mock_options

                    # Mock tools as found
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify deduplication logging (lines 531-533)
                                    mock_logger.debug.assert_any_call(
                                        "Removed 3 duplicate paths"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "Processing 1 unique path"
                                    )

                                    # Should only process the file once
                                    assert mock_process_mkv.call_count == 1
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_main_function_tool_path_assignment_logic(self):
        """Test main() function tool path assignment logic (lines 563, 568, 573)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options with custom tool paths
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        mkvpropedit_path="/custom/mkvpropedit",
                        mkvmerge_path="/custom/mkvmerge",
                        atomicparsley_path="/custom/AtomicParsley",
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock shutil.which to verify tool path assignment
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda path: (
                            path if path.startswith("/custom/") else None
                        )

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify custom tool paths were used (lines 562-575)
                                    mock_which.assert_any_call("/custom/mkvpropedit")
                                    mock_which.assert_any_call("/custom/mkvmerge")
                                    mock_which.assert_any_call("/custom/AtomicParsley")
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_main_function_mixed_file_processing_dispatch(self):
        """Test main() function file processing dispatch (lines 623-624)"""
        # Create temporary files and directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as mkv_file:
                mkv_file.write(b"fake mkv content")
                mkv_file_path = mkv_file.name

            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as mp4_file:
                mp4_file.write(b"fake mp4 content")
                mp4_file_path = mp4_file.name

            try:
                # Mock sys.argv with mixed files and folder
                with patch(
                    "sys.argv", [__app_name__, mkv_file_path, tmp_dir, mp4_file_path]
                ):
                    # Mock parse_options
                    with patch("main.parse_options") as mock_parse_options:
                        mock_options = create_mock_options(
                            paths=[mkv_file_path, tmp_dir, mp4_file_path]
                        )
                        mock_parse_options.return_value = mock_options

                        # Mock tools as found
                        with patch("main.shutil.which") as mock_which:
                            mock_which.side_effect = lambda tool: (
                                f"/usr/bin/{tool}" if tool else None
                            )

                            with patch("main.process_mkv_file") as mock_process_mkv:
                                with patch("main.process_mp4_file") as mock_process_mp4:
                                    with patch(
                                        "main.process_folder"
                                    ) as mock_process_folder:
                                        with patch("main.logger") as mock_logger:
                                            with patch("main.sys.exit") as mock_exit:
                                                mock_process_mkv.return_value = None
                                                mock_process_mp4.return_value = None
                                                mock_process_folder.return_value = None

                                                # Call main function
                                                main.main()

                                                # Verify all processing types called (lines 617-624)
                                                mock_process_mkv.assert_called_once_with(
                                                    mkv_file_path
                                                )
                                                mock_process_mp4.assert_called_once_with(
                                                    mp4_file_path
                                                )
                                                mock_process_folder.assert_called_once_with(
                                                    tmp_dir
                                                )
                                                mock_exit.assert_called_once()
            finally:
                # Clean up
                for path in [mkv_file_path, mp4_file_path]:
                    if os.path.exists(path):
                        os.unlink(path)

    def test_main_function_folder_error_statistics_logging(self):
        """Test main() function folder error statistics logging (line 628)"""
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

                    # Mock tools as found
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        # Simulate folder processing errors by setting global variables
                        with patch("main.process_mkv_file") as mock_process_mkv:

                            def simulate_folder_errors(*args, **kwargs):
                                # Simulate folder error statistics
                                main.folders_errored = 2

                            mock_process_mkv.side_effect = simulate_folder_errors

                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:

                                    # Call main function
                                    main.main()

                                    # Verify folder error statistics logging (line 628)
                                    mock_logger.info.assert_any_call(
                                        "Total folders errored: 2"
                                    )
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            # Reset global variables
            main.folders_errored = 0
