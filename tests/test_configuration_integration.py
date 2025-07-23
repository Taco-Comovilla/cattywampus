"""
Integration tests for configuration loading and option handling in main() function
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import main
from version import __app_name__

from .test_helpers import create_mock_options


class TestConfigurationIntegration:
    """Test configuration loading and option handling scenarios in main() function"""

    def test_main_function_logger_setup_with_options(self):
        """Test logger setup with file path and log level from options (lines 462-465)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options to return custom logger options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[tmp_file_path],
                        input_file=None,
                        dry_run=False,
                        only_mkv=False,
                        only_mp4=False,
                        log_file_path="/custom/log/path.log",
                        log_level=10,  # DEBUG level
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

                                with patch("main.process_mkv_file") as mock_process_mkv:
                                    # Mock logger setup to verify correct parameters
                                    with patch("main.logger.setup") as mock_logger_setup:
                                        with patch("main.sys.exit") as mock_exit:
                                            mock_process_mkv.return_value = None

                                            # Call main function
                                            main.main()

                                            # Verify logger setup called with correct parameters (lines 462-465)
                                            mock_logger_setup.assert_called_once_with(
                                                log_file_path="/custom/log/path.log",
                                                log_level=10,
                                                stdout_enabled=False,
                                                stdout_only=False,
                                            )
                                        mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_configuration_options_logging(self):
        """Test configuration options logging with sources (lines 539-559)"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock sys.argv to simulate CLI execution
            with patch("sys.argv", [__app_name__, tmp_file_path]):
                # Mock parse_options to return detailed options with sources
                with patch("main.parse_options") as mock_parse_options:
                    mock_lang_object = MagicMock()
                    mock_lang_object.display_name.return_value = "English"

                    mock_options = MagicMock()
                    mock_options.paths = [tmp_file_path]
                    mock_options.input_file = None
                    mock_options.dry_run = True
                    mock_options.only_mkv = True
                    mock_options.only_mp4 = False
                    mock_options.log_file_path = None
                    mock_options.log_level = 20
                    mock_options.set_default_sub_track = True
                    mock_options.set_default_audio_track = False
                    mock_options.use_system_locale = False
                    mock_options.language = "en"
                    mock_options.lang3 = "eng"
                    mock_options.lang_object = mock_lang_object
                    mock_options.mkvpropedit_path = "/custom/mkvpropedit"
                    mock_options.mkvmerge_path = None
                    mock_options.atomicparsley_path = None
                    # Mock sources for all options
                    mock_options.sources = {
                        "language": "config file",
                        "mkvmerge_path": "default",
                        "mkvpropedit_path": "command line",
                        "atomicparsley_path": "default",
                        "only_mkv": "command line",
                        "only_mp4": "default",
                        "set_default_sub_track": "config file",
                        "force_default_first_sub_track": "default",
                        "set_default_audio_track": "default",
                        "use_system_locale": "default",
                        "dry_run": "command line",
                        "log_level": "config file",
                    }
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

                                    # Verify configuration options logging (lines 539-559)
                                    mock_logger.debug.assert_any_call("Options:")
                                    mock_logger.debug.assert_any_call(
                                        "  language: English (en/eng) - config file"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "  mkvpropeditPath: /custom/mkvpropedit - command line"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "  mkvmergePath: not set - default"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "  onlyMkv: True - command line"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "  onlyMp4: False - default"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "  setDefaultSubtitle: True - config file"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "  dryRun: True - command line"
                                    )
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_file_type_statistics_logging(self):
        """Test file type specific statistics logging (lines 636-640)"""
        # Create temporary test files of different types
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as mkv_file:
            mkv_file.write(b"fake mkv content")
            mkv_file_path = mkv_file.name

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as mp4_file:
            mp4_file.write(b"fake mp4 content")
            mp4_file_path = mp4_file.name

        try:
            # Mock sys.argv to simulate processing both file types
            with patch("sys.argv", [__app_name__, mkv_file_path, mp4_file_path]):
                # Mock parse_options
                with patch("main.parse_options") as mock_parse_options:
                    mock_options = create_mock_options(
                        paths=[mkv_file_path, mp4_file_path],
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

                                # Mock processing functions to simulate file type statistics
                                with patch("main.process_mkv_file") as mock_process_mkv:
                                    with patch("main.process_mp4_file") as mock_process_mp4:

                                        def simulate_mkv_processing(path):
                                            main.mkv_files_processed = 1
                                            main.mkv_processing_time = 2.5

                                        def simulate_mp4_processing(path):
                                            main.mp4_files_processed = 1
                                            main.mp4_processing_time = 1.8

                                        mock_process_mkv.side_effect = simulate_mkv_processing
                                        mock_process_mp4.side_effect = simulate_mp4_processing

                                        with patch("main.logger") as mock_logger:
                                            with patch("main.sys.exit") as mock_exit:

                                                # Call main function
                                                main.main()

                                                # Verify file type statistics logging (lines 636-640)
                                                mock_logger.info.assert_any_call(
                                                    "MKV files processed: 1, total MKV processing time: 2.500 seconds"
                                                )
                                                mock_logger.info.assert_any_call(
                                                    "MP4 files processed: 1, total MP4 processing time: 1.800 seconds"
                                                )
                                                mock_exit.assert_called_once()
        finally:
            # Clean up
            for path in [mkv_file_path, mp4_file_path]:
                if Path(path).exists():
                    Path(path).unlink()
            # Reset global variables
            main.mkv_files_processed = 0
            main.mp4_files_processed = 0
            main.mkv_processing_time = 0.0
            main.mp4_processing_time = 0.0
