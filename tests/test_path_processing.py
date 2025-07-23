"""
Tests for path processing, deduplication, and filtering in main() function
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import main
from version import __app_name__


class TestPathProcessing:
    """Test path processing scenarios in main() function"""

    def test_main_function_path_deduplication(self):
        """Test path deduplication logic (lines 479-490)"""
        # Create temporary test files
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

            # Create different ways to reference the same file
            abs_path = str(Path(tmp_file_path).resolve())
            rel_path = os.path.relpath(tmp_file_path)

        try:
            # Mock sys.argv with duplicate paths
            duplicate_paths = [tmp_file_path, abs_path, rel_path, tmp_file_path]
            with patch("sys.argv", [__app_name__, *duplicate_paths]):
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

                                # Verify deduplication logging (lines 530-533)
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
            if Path(tmp_file_path).exists():
                Path(tmp_file_path).unlink()

    def test_main_function_file_type_filtering_mkv_only(self):
        """Test file type filtering with --only-mkv (lines 494-507)"""
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

                                    # Verify filtering (lines 524-527)
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
                if Path(path).exists():
                    Path(path).unlink()

    def test_main_function_file_type_filtering_mp4_only(self):
        """Test file type filtering with --only-mp4 (lines 494-507)"""
        # Create temporary test files of different types
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as mkv_file:
            mkv_file.write(b"fake mkv content")
            mkv_file_path = mkv_file.name

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as mp4_file:
            mp4_file.write(b"fake mp4 content")
            mp4_file_path = mp4_file.name

        try:
            # Mock sys.argv with both file types and --only-mp4
            with patch(
                "sys.argv", [__app_name__, "--only-mp4", mkv_file_path, mp4_file_path]
            ):
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

                                    # Verify filtering (lines 524-527)
                                    mock_logger.debug.assert_any_call(
                                        "Filtered out 1 MKV file"
                                    )
                                    mock_logger.debug.assert_any_call(
                                        "Processing 1 unique path"
                                    )

                                    # Should only process MP4 file
                                    mock_process_mp4.assert_called_once()
                                    mock_process_mkv.assert_not_called()
                                    mock_exit.assert_called_once()
        finally:
            # Clean up
            for path in [mkv_file_path, mp4_file_path]:
                if Path(path).exists():
                    Path(path).unlink()

    def test_main_function_directory_filtering_preserved(self):
        """Test that directories are preserved during file type filtering (lines 502-504)"""
        # Create a temporary directory and file
        with tempfile.TemporaryDirectory() as tmp_dir:
            with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as mkv_file:
                mkv_file.write(b"fake mkv content")
                mkv_file_path = mkv_file.name

            try:
                # Mock sys.argv with directory and file, using --only-mp4 filter
                with patch(
                    "sys.argv", [__app_name__, "--only-mp4", tmp_dir, mkv_file_path]
                ):
                    # Mock tools as found
                    with patch("main.shutil.which") as mock_which:
                        mock_which.side_effect = lambda tool: (
                            f"/usr/bin/{tool}" if tool else None
                        )

                        with patch("main.process_folder") as mock_process_folder:
                            with patch("main.process_mkv_file") as mock_process_mkv:
                                with patch("main.logger") as mock_logger:
                                    with patch("main.sys.exit") as mock_exit:
                                        mock_process_folder.return_value = None
                                        mock_process_mkv.return_value = None

                                        # Call main function
                                        main.main()

                                        # Verify directory is preserved despite filtering
                                        mock_logger.debug.assert_any_call(
                                            "Filtered out 1 MKV file"
                                        )
                                        mock_logger.debug.assert_any_call(
                                            "Processing 1 unique path"
                                        )

                                        # Should process directory but not MKV file
                                        mock_process_folder.assert_called_once_with(
                                            tmp_dir
                                        )
                                        mock_process_mkv.assert_not_called()
                                        mock_exit.assert_called_once()
            finally:
                # Clean up
                if Path(mkv_file_path).exists():
                    Path(mkv_file_path).unlink()

    def test_main_function_mixed_file_and_folder_processing(self):
        """Test processing both files and folders (lines 617-624)"""
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
                                    with patch("main.logger"):
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
                    if Path(path).exists():
                        Path(path).unlink()

    def test_main_function_m4v_file_processing(self):
        """Test .m4v file processing (lines 621-622)"""
        # Create temporary .m4v file
        with tempfile.NamedTemporaryFile(suffix=".m4v", delete=False) as m4v_file:
            m4v_file.write(b"fake m4v content")
            m4v_file_path = m4v_file.name

        try:
            # Mock sys.argv with .m4v file
            with patch("sys.argv", [__app_name__, m4v_file_path]):
                # Mock tools as found
                with patch("main.shutil.which") as mock_which:
                    mock_which.side_effect = lambda tool: (
                        f"/usr/bin/{tool}" if tool else None
                    )

                    with patch("main.process_mp4_file") as mock_process_mp4:
                        with patch("main.logger"):
                            with patch("main.sys.exit") as mock_exit:
                                mock_process_mp4.return_value = None

                                # Call main function
                                main.main()

                                # Verify .m4v file processed as MP4 (lines 621-622)
                                mock_process_mp4.assert_called_once_with(m4v_file_path)
                                mock_exit.assert_called_once()
        finally:
            # Clean up
            if Path(m4v_file_path).exists():
                Path(m4v_file_path).unlink()
