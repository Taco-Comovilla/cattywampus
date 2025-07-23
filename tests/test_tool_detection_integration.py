"""
Integration tests for tool detection and initialization in main() function
"""

import os
import tempfile
from unittest.mock import patch

import main

from .test_helpers import create_mock_options


class TestToolDetectionIntegration:
    """Test tool detection and initialization scenarios in main() function"""

    def test_main_function_tool_path_initialization_from_options(self):
        """Test tool path initialization from options (lines 562-575)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options to return custom tool paths
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        input_file=None,
                        dry_run=False,
                        only_mkv=False,
                        only_mp4=False,
                        log_file_path=None,
                        log_level=20,
                        # Set custom tool paths
                        mkvpropedit_path="/custom/path/mkvpropedit",
                        mkvmerge_path="/custom/path/mkvmerge",
                        atomicparsley_path="/custom/path/AtomicParsley",
                        sources={
                            "mkvpropedit_path": "config",
                            "mkvmerge_path": "config",
                            "atomicparsley_path": "config",
                        },
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock shutil.which to verify custom paths are used
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda path: (
                            path if path.startswith("/custom/path/") else None
                        )

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify custom paths were used (lines 562-575)
                                    mock_which.assert_any_call(
                                        "/custom/path/mkvpropedit"
                                    )
                                    mock_which.assert_any_call("/custom/path/mkvmerge")
                                    mock_which.assert_any_call(
                                        "/custom/path/AtomicParsley"
                                    )
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_tool_path_fallback_to_system(self):
        """Test tool path fallback to system binaries on Windows/Unix (lines 565-575)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options to return no custom tool paths
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        input_file=None,
                        dry_run=False,
                        only_mkv=False,
                        only_mp4=False,
                        log_file_path=None,
                        log_level=20,
                        # No custom tool paths
                        mkvpropedit_path=None,
                        mkvmerge_path=None,
                        atomicparsley_path=None,
                        sources={
                            "mkvpropedit_path": "default",
                            "mkvmerge_path": "default",
                            "atomicparsley_path": "default",
                        },
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock platform detection
                    with patch("main.platform.system") as mock_platform:
                        mock_platform.return_value = "Linux"

                        # Mock shutil.which to return system paths
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

                                        # Verify system tool names were used (lines 565-575)
                                        mock_which.assert_any_call("mkvpropedit")
                                        mock_which.assert_any_call("mkvmerge")
                                        mock_which.assert_any_call("AtomicParsley")
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_tool_discovery_logging(self):
        """Test tool discovery logging with sources (lines 588-615)"""
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
                        sources={
                            "mkvpropedit_path": "default",
                            "mkvmerge_path": "default",
                            "atomicparsley_path": "default",
                        },
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock tools found in PATH
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

                                        # Verify tool discovery logging (lines 589-615)
                                        mock_logger.debug.assert_any_call(
                                            "Tool discovery:"
                                        )
                                        mock_logger.debug.assert_any_call(
                                            "  mkvpropedit: /usr/bin/mkvpropedit - PATH"
                                        )
                                        mock_logger.debug.assert_any_call(
                                            "  mkvmerge: /usr/bin/mkvmerge - PATH"
                                        )
                                        mock_logger.debug.assert_any_call(
                                            "  AtomicParsley: /usr/bin/AtomicParsley - PATH"
                                        )
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_windows_tool_naming(self):
        """Test Windows-specific tool naming (.exe extension) (lines 565-575)"""
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

                    # Mock Windows platform
                    with patch("main.platform.system") as mock_platform:
                        mock_platform.return_value = "Windows"

                        # Mock shutil.which to return Windows tool paths
                        with patch("main.shutil.which") as mock_which:
                            mock_which.side_effect = lambda tool: (
                                f"C:\\Tools\\{tool}" if tool.endswith(".exe") else None
                            )

                            with patch("main.process_mkv_file") as mock_process_mkv:
                                with patch("main.logger") as mock_logger:
                                    with patch("main.sys.exit") as mock_exit:
                                        mock_process_mkv.return_value = None

                                        # Call main function
                                        main.main()

                                        # Verify Windows tool names were used (lines 565-575)
                                        mock_which.assert_any_call("mkvpropedit.exe")
                                        mock_which.assert_any_call("mkvmerge.exe")
                                        mock_which.assert_any_call("AtomicParsley.exe")
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()
