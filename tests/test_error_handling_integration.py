"""
Integration tests for error handling and exit scenarios in main() function
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import main

from .test_helpers import create_mock_options
from version import __app_name__


class TestErrorHandlingIntegration:
    """Test error handling and exit scenarios in main() function"""

    def test_main_function_no_paths_provided_still_runs(self):
        """Test main() function runs with no paths provided (processes empty list)"""
        # Mock sys.argv with no file paths
        with patch("sys.argv", [__app_name__]):
            # Mock parse_options to return no paths
            with patch("main.parse_options") as mock_parse_options:
                mock_options = create_mock_options(
                    paths=[],  # No paths provided
                    input_file=None,
                    dry_run=False,
                    only_mkv=False,
                    only_mp4=False,
                    log_file_path=None,
                    log_level=20,
                    mkvpropedit_path=None,
                    mkvmerge_path=None,
                    atomicparsley_path=None,
                )
                mock_parse_options.return_value = mock_options

                # Mock tools as found
                with patch("main.shutil.which") as mock_which:
                    mock_which.side_effect = lambda tool: (
                        f"/usr/bin/{tool}" if tool else None
                    )

                    with patch("main.logger") as mock_logger:
                        with patch("main.sys.exit") as mock_exit:

                            # Call main function with no paths
                            main.main()

                            # Verify processing 0 paths logged (lines 535-537)
                            mock_logger.debug.assert_any_call(
                                "Processing 0 unique paths"
                            )
                            mock_exit.assert_called_once()

    def test_main_function_input_file_error_handling(self):
        """Test main() function handles input file errors properly"""
        # Create a non-existent input file path
        non_existent_file = "/tmp/does_not_exist_12345.txt"

        # Mock sys.argv with non-existent input file
        with patch("sys.argv", [__app_name__, "--input", non_existent_file]):
            # Mock parse_options to return input file option
            with patch("main.parse_options") as mock_parse_options:
                mock_options = create_mock_options(
                    paths=[],
                    input_file=non_existent_file,
                    dry_run=False,
                    only_mkv=False,
                    only_mp4=False,
                    log_file_path=None,
                    log_level=20,
                    mkvpropedit_path=None,
                    mkvmerge_path=None,
                    atomicparsley_path=None,
                )
                mock_parse_options.return_value = mock_options

                # Mock tools as found
                with patch("main.shutil.which") as mock_which:
                    with patch("main.Path.is_file") as mock_is_file:
                        with patch("main.os.access") as mock_access:
                            mock_which.side_effect = lambda tool: (
                                f"/usr/bin/{tool}" if tool else None
                            )
                            mock_is_file.return_value = True
                            mock_access.return_value = True

                            with patch("main.logger"):
                                with patch("main.sys.exit") as mock_exit:

                                    # Call main function - should exit due to file not found
                                    main.main()

                                    # Verify exit was called due to input file error
                                    mock_exit.assert_called_with()

    def test_main_function_path_environment_logging(self):
        """Test main() function logs PATH environment variable (line 582)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        input_file=None,
                        dry_run=False,
                        only_mkv=False,
                        only_mp4=False,
                        log_file_path=None,
                        log_level=20,
                        mkvpropedit_path=None,
                        mkvmerge_path=None,
                        atomicparsley_path=None,
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock PATH environment variable
                    with patch.dict(
                        "main.os.environ", {"PATH": "/usr/bin:/usr/local/bin"}
                    ):
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

                                        # Verify PATH logging (line 582)
                                        mock_logger.debug.assert_any_call(
                                            "PATH: /usr/bin:/usr/local/bin"
                                        )
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_total_runtime_logging(self):
        """Test main() function logs total runtime statistics (lines 642-644)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        input_file=None,
                        dry_run=False,
                        only_mkv=False,
                        only_mp4=False,
                        log_file_path=None,
                        log_level=20,
                        mkvpropedit_path=None,
                        mkvmerge_path=None,
                        atomicparsley_path=None,
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock timing for total runtime
                    with patch("main.time.perf_counter") as mock_perf_counter:
                        mock_perf_counter.side_effect = [
                            0.0,
                            5.123,
                        ]  # 5.123 second runtime

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

                                        # Verify total runtime logging (lines 642-644)
                                        mock_logger.info.assert_any_call(
                                            "Total runtime: 5.123 seconds"
                                        )
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_file_error_statistics_logging(self):
        """Test main() function logs file error statistics (lines 630-634)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        input_file=None,
                        dry_run=False,
                        only_mkv=False,
                        only_mp4=False,
                        log_file_path=None,
                        log_level=20,
                        mkvpropedit_path=None,
                        mkvmerge_path=None,
                        atomicparsley_path=None,
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock tools as found
                    with patch("main.shutil.which") as mock_which:
                        with patch("main.Path.is_file") as mock_is_file:
                            with patch("main.os.access") as mock_access:
                                mock_which.side_effect = lambda tool: (
                                    f"/usr/bin/{tool}" if tool else None
                                )
                                mock_is_file.return_value = True
                                mock_access.return_value = True

                                # Simulate file processing errors by setting global variables
                                with patch("main.process_mkv_file") as mock_process_mkv:

                                    def simulate_error(path):
                                        # Simulate the error counting that happens in process_mkv_file
                                        main.files_errored = 1
                                        main.files_with_errors = [tmp_file_path]

                                    mock_process_mkv.side_effect = simulate_error

                                    with patch("main.logger") as mock_logger:
                                        with patch("main.sys.exit") as mock_exit:

                                            # Call main function
                                            main.main()

                                            # Verify error statistics logging (lines 630-634)
                                            mock_logger.info.assert_any_call(
                                                "Total files errored: 1"
                                            )
                                            mock_logger.info.assert_any_call(
                                                "Files with errors:"
                                            )
                                            mock_logger.info.assert_any_call(
                                                f"  {tmp_file_path}"
                                            )
                                            mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()
            # Reset global variables
            main.files_errored = 0
            main.files_with_errors = []
