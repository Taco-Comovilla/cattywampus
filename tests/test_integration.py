"""
Integration tests for file processing workflows
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from main import process_folder, process_mkv_file, process_mp4_file


class TestProcessMkvFile:
    """Integration tests for MKV file processing"""

    @patch("main.options")
    @patch("main.mkvpropedit", "/usr/bin/mkvpropedit")
    @patch("main.mkvmerge", "/usr/bin/mkvmerge")
    @patch("main.subprocess.run")
    @patch("main.get_mkv_metadata")
    @patch("main.logger")
    def test_process_mkv_file_with_audio(
        self, mock_logger, mock_get_metadata, mock_run, mock_options
    ):
        """Test processing MKV file with audio tracks"""
        # Setup
        mock_options.dry_run = False
        mock_options.set_default_sub_track = False
        mock_options.force_default_first_sub_track = False

        mock_metadata = {
            "tracks": [{"type": "video"}, {"type": "audio"}, {"type": "subtitles"}]
        }
        mock_get_metadata.return_value = mock_metadata

        # Mock successful subprocess calls
        mock_run.return_value = MagicMock()

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as temp_file:
            temp_file.write(b"fake mkv content")
            temp_path = temp_file.name

        try:
            # Test
            process_mkv_file(temp_path)

            # Verify subprocess was called with audio track options
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]  # Get the command list

            # Should include audio track options
            assert "-e" in call_args
            assert "track:a1" in call_args
            assert "-d" in call_args
            assert "name" in call_args

            # Verify logging
            mock_logger.info.assert_called()

        finally:
            Path(temp_path).unlink()

    @patch("main.options")
    @patch("main.mkvpropedit", "/usr/bin/mkvpropedit")
    @patch("main.mkvmerge", "/usr/bin/mkvmerge")
    @patch("main.subprocess.run")
    @patch("main.get_mkv_metadata")
    @patch("main.logger")
    def test_process_mkv_file_without_audio(
        self, mock_logger, mock_get_metadata, mock_run, mock_options
    ):
        """Test processing MKV file without audio tracks"""
        # Setup
        mock_options.dry_run = False
        mock_options.set_default_sub_track = False
        mock_options.force_default_first_sub_track = False

        mock_metadata = {"tracks": [{"type": "video"}, {"type": "subtitles"}]}
        mock_get_metadata.return_value = mock_metadata

        # Mock successful subprocess calls
        mock_run.return_value = MagicMock()

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as temp_file:
            temp_file.write(b"fake mkv content")
            temp_path = temp_file.name

        try:
            # Test
            process_mkv_file(temp_path)

            # Verify subprocess was called without audio track options
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]  # Get the command list

            # Should not include audio track options
            audio_track_present = False
            for i, arg in enumerate(call_args):
                if arg == "track:a1":
                    audio_track_present = True
                    break

            assert not audio_track_present

            # Should log that no audio tracks were found
            mock_logger.debug.assert_called()
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("No audio tracks found" in call for call in debug_calls)

        finally:
            Path(temp_path).unlink()

    @patch("main.options")
    @patch("main.mkvpropedit", "/usr/bin/mkvpropedit")
    @patch("main.mkvmerge", "/usr/bin/mkvmerge")
    @patch("main.subprocess.run")
    @patch("main.get_mkv_metadata")
    @patch("main.logger")
    def test_process_mkv_file_dry_run(
        self, mock_logger, mock_get_metadata, mock_run, mock_options
    ):
        """Test processing MKV file in dry run mode"""
        # Setup
        mock_options.dry_run = True
        mock_options.set_default_sub_track = False
        mock_options.force_default_first_sub_track = False

        mock_metadata = {"tracks": [{"type": "video"}]}
        mock_get_metadata.return_value = mock_metadata

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as temp_file:
            temp_file.write(b"fake mkv content")
            temp_path = temp_file.name

        try:
            # Test
            process_mkv_file(temp_path)

            # Verify subprocess was NOT called in dry run mode
            mock_run.assert_not_called()

            # Verify dry run logging
            mock_logger.info.assert_called()
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("DRY RUN" in call for call in info_calls)

        finally:
            Path(temp_path).unlink()

    @patch("main.options")
    @patch("main.mkvpropedit", None)
    @patch("main.mkvmerge", "/usr/bin/mkvmerge")
    @patch("main.logger")
    def test_process_mkv_file_no_mkvpropedit(self, mock_logger, mock_options):
        """Test processing MKV file when mkvpropedit is not available"""
        mock_options.dry_run = False

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as temp_file:
            temp_file.write(b"fake mkv content")
            temp_path = temp_file.name

        try:
            # Test
            result = process_mkv_file(temp_path)

            # Should return None and log warning
            assert result is None
            mock_logger.info.assert_called_with(
                "mkvpropedit not found in PATH. Skipping."
            )

        finally:
            Path(temp_path).unlink()


class TestProcessMp4File:
    """Integration tests for MP4 file processing"""

    @patch("main.options")
    @patch("main.atomicparsley", "/usr/bin/AtomicParsley")
    @patch("main.subprocess.run")
    @patch("main.get_mp4_metadata")
    @patch("main.logger")
    def test_process_mp4_file_with_metadata(
        self, mock_logger, mock_get_metadata, mock_run, mock_options
    ):
        """Test processing MP4 file with metadata"""
        # Setup
        mock_options.dry_run = False

        mock_metadata = {"title": "Test Title", "description": "Test Description"}
        mock_get_metadata.return_value = mock_metadata

        # Mock successful subprocess calls
        mock_run.return_value = MagicMock()

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"fake mp4 content")
            temp_path = temp_file.name

        try:
            # Test
            process_mp4_file(temp_path)

            # Verify subprocess was called with correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]  # Get the command list

            # Should include title and description clearing
            assert "--title" in call_args
            assert "--description" in call_args
            assert "--overWrite" in call_args

            # Verify logging
            mock_logger.info.assert_called()

        finally:
            Path(temp_path).unlink()

    @patch("main.options")
    @patch("main.atomicparsley", "/usr/bin/AtomicParsley")
    @patch("main.get_mp4_metadata")
    @patch("main.logger")
    def test_process_mp4_file_no_metadata(
        self, mock_logger, mock_get_metadata, mock_options
    ):
        """Test processing MP4 file without metadata"""
        # Setup
        mock_options.dry_run = False

        mock_get_metadata.return_value = None

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"fake mp4 content")
            temp_path = temp_file.name

        try:
            # Test
            result = process_mp4_file(temp_path)

            # Should return None and log that no metadata was found
            assert result is None
            mock_logger.info.assert_called_with("No metadata found in file.")

        finally:
            Path(temp_path).unlink()

    @patch("main.options")
    @patch("main.atomicparsley", None)
    @patch("main.logger")
    def test_process_mp4_file_no_atomicparsley(self, mock_logger, mock_options):
        """Test processing MP4 file when AtomicParsley is not available"""
        mock_options.dry_run = False

        # Create temp file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"fake mp4 content")
            temp_path = temp_file.name

        try:
            # Test
            result = process_mp4_file(temp_path)

            # Should return None and log warning
            assert result is None
            mock_logger.info.assert_called_with(
                "AtomicParsley not found in PATH. Skipping."
            )

        finally:
            Path(temp_path).unlink()


class TestProcessFolder:
    """Integration tests for folder processing"""

    @patch("main.options")
    @patch("main.process_mkv_file")
    @patch("main.process_mp4_file")
    def test_process_folder_mixed_files(
        self, mock_process_mp4, mock_process_mkv, mock_options
    ):
        """Test processing folder with mixed file types"""
        # Setup
        mock_options.only_mkv = False
        mock_options.only_mp4 = False

        # Create temp directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            mkv_file = os.path.join(temp_dir, "test.mkv")
            mp4_file = os.path.join(temp_dir, "test.mp4")
            txt_file = os.path.join(temp_dir, "readme.txt")

            with open(mkv_file, "w") as f:
                f.write("fake mkv")
            with open(mp4_file, "w") as f:
                f.write("fake mp4")
            with open(txt_file, "w") as f:
                f.write("text file")

            # Test
            process_folder(temp_dir)

            # Verify both processors were called
            mock_process_mkv.assert_called_once_with(mkv_file)
            mock_process_mp4.assert_called_once_with(mp4_file)

    @patch("main.options")
    @patch("main.process_mkv_file")
    @patch("main.process_mp4_file")
    def test_process_folder_only_mkv(
        self, mock_process_mp4, mock_process_mkv, mock_options
    ):
        """Test processing folder with only MKV files enabled"""
        # Setup
        mock_options.only_mkv = True
        mock_options.only_mp4 = False

        # Create temp directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            mkv_file = os.path.join(temp_dir, "test.mkv")
            mp4_file = os.path.join(temp_dir, "test.mp4")

            with open(mkv_file, "w") as f:
                f.write("fake mkv")
            with open(mp4_file, "w") as f:
                f.write("fake mp4")

            # Test
            process_folder(temp_dir)

            # Verify only MKV processor was called
            mock_process_mkv.assert_called_once_with(mkv_file)
            mock_process_mp4.assert_not_called()

    @patch("main.options")
    @patch("main.process_mkv_file")
    @patch("main.process_mp4_file")
    def test_process_folder_only_mp4(
        self, mock_process_mp4, mock_process_mkv, mock_options
    ):
        """Test processing folder with only MP4 files enabled"""
        # Setup
        mock_options.only_mkv = False
        mock_options.only_mp4 = True

        # Create temp directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            mkv_file = os.path.join(temp_dir, "test.mkv")
            mp4_file = os.path.join(temp_dir, "test.mp4")
            m4v_file = os.path.join(temp_dir, "test.m4v")

            with open(mkv_file, "w") as f:
                f.write("fake mkv")
            with open(mp4_file, "w") as f:
                f.write("fake mp4")
            with open(m4v_file, "w") as f:
                f.write("fake m4v")

            # Test
            process_folder(temp_dir)

            # Verify only MP4 processors were called
            mock_process_mkv.assert_not_called()
            mock_process_mp4.assert_any_call(mp4_file)
            mock_process_mp4.assert_any_call(m4v_file)

    @patch("main.options")
    @patch("main.process_mkv_file")
    @patch("main.process_mp4_file")
    def test_process_folder_recursive(
        self, mock_process_mp4, mock_process_mkv, mock_options
    ):
        """Test recursive folder processing"""
        # Setup
        mock_options.only_mkv = False
        mock_options.only_mp4 = False

        # Create temp directory with nested structure
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create nested directory
            nested_dir = os.path.join(temp_dir, "nested")
            os.makedirs(nested_dir)

            # Create test files at different levels
            root_mkv = os.path.join(temp_dir, "root.mkv")
            nested_mp4 = os.path.join(nested_dir, "nested.mp4")

            with open(root_mkv, "w") as f:
                f.write("fake mkv")
            with open(nested_mp4, "w") as f:
                f.write("fake mp4")

            # Test
            process_folder(temp_dir)

            # Verify both files were processed
            mock_process_mkv.assert_called_once_with(root_mkv)
            mock_process_mp4.assert_called_once_with(nested_mp4)

    @patch("main.folders_errored", 0)
    @patch("main.logger")
    def test_process_folder_error_handling(self, mock_logger):
        """Test error handling in folder processing"""
        # Test with non-existent folder
        process_folder("/nonexistent/folder")

        # Should log error and increment error counter
        mock_logger.error.assert_called()

        # Import to check the global variable
        import main

        assert main.folders_errored == 1
