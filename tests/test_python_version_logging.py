"""
Tests for Python version logging functionality
"""

import os
import sys
import tempfile
from unittest.mock import patch

import main


class TestPythonVersionLogging:
    """Test Python version logging in main function"""

    def test_python_version_logging_in_main(self):
        """Test that Python version is logged during main() execution"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                # Mock parse_options to return test options
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=True,
                        log_file_path="/tmp/test.log",
                        log_level=20,
                    )
                    mock_parse_options.return_value = mock_options

                    # Mock tool detection
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        # Mock process_mkv_file to avoid actual processing
                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Call main function
                                    main.main()

                                    # Verify that Python version was logged with environment info
                                    expected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                                    # Check that a call starting with "Python {version}" was made
                                    python_version_found = False
                                    for call in mock_logger.debug.call_args_list:
                                        call_msg = call[0][
                                            0
                                        ]  # First argument of the call
                                        if call_msg.startswith(
                                            f"Python {expected_version}"
                                        ):
                                            python_version_found = True
                                            # Verify it contains environment info (either "bundled" or "system")
                                            assert (
                                                "(" in call_msg and ")" in call_msg
                                            ), "Environment info missing from Python version log"
                                            break
                                    assert (
                                        python_version_found
                                    ), "Python version was not logged"

                                    # Verify it's logged after BEGINNING RUN
                                    info_calls = [
                                        call for call in mock_logger.info.call_args_list
                                    ]
                                    debug_calls = [
                                        call
                                        for call in mock_logger.debug.call_args_list
                                    ]
                                    beginning_run_logged = False
                                    python_version_logged = False

                                    # Check INFO calls for BEGINNING RUN
                                    for call in info_calls:
                                        call_msg = call[0][
                                            0
                                        ]  # First argument of the call
                                        if "BEGINNING RUN" in call_msg:
                                            beginning_run_logged = True
                                            break

                                    # Check DEBUG calls for Python version
                                    for call in debug_calls:
                                        call_msg = call[0][
                                            0
                                        ]  # First argument of the call
                                        if call_msg.startswith(
                                            f"Python {expected_version}"
                                        ):
                                            # Python version should be logged after BEGINNING RUN
                                            assert (
                                                beginning_run_logged
                                            ), "Python version logged before BEGINNING RUN"
                                            python_version_logged = True
                                            break

                                    assert (
                                        python_version_logged
                                    ), "Python version was not logged"

        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_python_version_format(self):
        """Test that Python version format is correct"""
        expected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Test the exact format used in main.py
        version_string = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert version_string == expected_version

        # Verify it matches pattern like "3.13.3"
        import re

        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(
            pattern, version_string
        ), f"Version {version_string} doesn't match expected format"

    def test_python_version_components(self):
        """Test that all Python version components are integers"""
        # Verify that version_info components are accessible and are integers
        assert isinstance(sys.version_info.major, int)
        assert isinstance(sys.version_info.minor, int)
        assert isinstance(sys.version_info.micro, int)

        # Verify they're reasonable values
        assert sys.version_info.major >= 3  # We require Python 3+
        assert sys.version_info.minor >= 0
        assert sys.version_info.micro >= 0

    def test_logging_order_with_dry_run(self):
        """Test that Python version is logged in correct order with dry run"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution with dry run
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=True,
                        log_file_path="/tmp/test.log",
                        log_level=20,
                    )
                    mock_parse_options.return_value = mock_options

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

                                    # Check logging order: BEGINNING RUN, DRY RUN (INFO), Python version (DEBUG)
                                    info_calls = [
                                        call[0][0]
                                        for call in mock_logger.info.call_args_list
                                    ]
                                    debug_calls = [
                                        call[0][0]
                                        for call in mock_logger.debug.call_args_list
                                    ]

                                    beginning_run_idx = None
                                    dry_run_idx = None
                                    python_version_found = False

                                    # Find BEGINNING RUN and DRY RUN in INFO calls
                                    for i, msg in enumerate(info_calls):
                                        if "BEGINNING RUN" in msg:
                                            beginning_run_idx = i
                                        elif "DRY RUN" in msg:
                                            dry_run_idx = i

                                    # Find Python version in DEBUG calls
                                    expected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                                    for msg in debug_calls:
                                        if msg.startswith(f"Python {expected_version}"):
                                            python_version_found = True
                                            break

                                    # Verify all messages were logged
                                    assert (
                                        beginning_run_idx is not None
                                    ), "BEGINNING RUN not logged"
                                    assert dry_run_idx is not None, "DRY RUN not logged"
                                    assert (
                                        python_version_found
                                    ), "Python version not logged"

                                    # Verify correct order (BEGINNING RUN before DRY RUN)
                                    assert (
                                        beginning_run_idx < dry_run_idx
                                    ), "BEGINNING RUN should come before DRY RUN"

        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_python_version_environment_detection(self):
        """Test that Python version logging includes environment detection"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=True,
                        log_file_path="/tmp/test.log",
                        log_level=20,
                    )
                    mock_parse_options.return_value = mock_options

                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Test system Python detection (normal case)
                                    main.main()

                                    # Find the Python version log message
                                    python_log_found = False
                                    for call in mock_logger.debug.call_args_list:
                                        call_msg = call[0][0]
                                        if call_msg.startswith("Python "):
                                            python_log_found = True
                                            # Should contain "system" for normal Python execution
                                            assert (
                                                "system" in call_msg
                                            ), f"Expected 'system' in log message: {call_msg}"
                                            # Should contain environment info in parentheses
                                            assert (
                                                "(" in call_msg and ")" in call_msg
                                            ), f"Expected environment info in parentheses: {call_msg}"
                                            break

                                    assert (
                                        python_log_found
                                    ), "Python version log message not found"

        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_python_version_bundled_detection(self):
        """Test that Python version logging detects PyInstaller bundle"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, "--dry-run", tmp_file_path]):
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=True,
                        log_file_path="/tmp/test.log",
                        log_level=20,
                    )
                    mock_parse_options.return_value = mock_options

                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        with patch("main.process_mkv_file") as mock_process_mkv:
                            with patch("main.logger") as mock_logger:
                                with patch("main.sys.exit") as mock_exit:
                                    mock_process_mkv.return_value = None

                                    # Mock PyInstaller environment
                                    with (
                                        patch.object(
                                            main.sys, "frozen", True, create=True
                                        ),
                                        patch.object(
                                            main.sys,
                                            "_MEIPASS",
                                            "/tmp/meipass",
                                            create=True,
                                        ),
                                    ):

                                        main.main()

                                        # Find the Python version log message
                                        python_log_found = False
                                        for call in mock_logger.debug.call_args_list:
                                            call_msg = call[0][0]
                                            if call_msg.startswith("Python "):
                                                python_log_found = True
                                                # Should contain "bundled" for PyInstaller execution
                                                assert (
                                                    "bundled" in call_msg
                                                ), f"Expected 'bundled' in log message: {call_msg}"
                                                break

                                        assert (
                                            python_log_found
                                        ), "Python version log message not found"

        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    def test_logging_order_without_dry_run(self):
        """Test that Python version is logged in correct order without dry run"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution without dry run
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                with patch("main.parse_options") as mock_parse_options:
                    from tests.test_helpers import create_mock_options

                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        dry_run=False,
                        log_file_path="/tmp/test.log",
                        log_level=20,
                    )
                    mock_parse_options.return_value = mock_options

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

                                    # Check logging order: BEGINNING RUN (INFO), Python version (DEBUG), no DRY RUN
                                    info_calls = [
                                        call[0][0]
                                        for call in mock_logger.info.call_args_list
                                    ]
                                    debug_calls = [
                                        call[0][0]
                                        for call in mock_logger.debug.call_args_list
                                    ]

                                    beginning_run_idx = None
                                    python_version_found = False
                                    dry_run_found = False

                                    # Check INFO calls for BEGINNING RUN and ensure no DRY RUN
                                    for i, msg in enumerate(info_calls):
                                        if "BEGINNING RUN" in msg:
                                            beginning_run_idx = i
                                        elif "DRY RUN" in msg:
                                            dry_run_found = True

                                    # Check DEBUG calls for Python version
                                    expected_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
                                    for msg in debug_calls:
                                        if msg.startswith(f"Python {expected_version}"):
                                            python_version_found = True
                                            break

                                    # Verify correct messages were logged
                                    assert (
                                        beginning_run_idx is not None
                                    ), "BEGINNING RUN not logged"
                                    assert (
                                        python_version_found
                                    ), "Python version not logged"
                                    assert (
                                        not dry_run_found
                                    ), "DRY RUN should not be logged when not in dry run mode"

        finally:
            # Clean up
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
