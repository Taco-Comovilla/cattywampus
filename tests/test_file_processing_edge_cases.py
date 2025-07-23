"""
Tests for file processing edge cases and conditional paths
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import main
from main import get_mkv_subtitle_args, process_mkv_file, process_mp4_file


class TestFileProcessingEdgeCases:
    """Test file processing edge cases and conditional logic"""

    @patch("main.options")
    @patch("main.logger")
    def test_mkv_subtitle_processing_conditional_path(self, mock_logger, mock_options):
        """Test MKV subtitle processing conditional (line 121)"""
        # Setup options to enable subtitle processing
        mock_options.dry_run = False
        mock_options.set_default_sub_track = (
            True  # This enables the conditional on line 120
        )
        mock_options.force_default_first_subtitle = False

        # Reset global counters
        main.files_processed = 0
        main.mkv_files_processed = 0
        main.mkv_processing_time = 0.0

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock get_mkv_metadata to return metadata with audio and subtitles
            with patch("main.get_mkv_metadata") as mock_get_metadata:
                with patch("main.get_mkv_subtitle_args") as mock_subtitle_args:
                    mock_get_metadata.return_value = {
                        "tracks": [
                            {"type": "video"},
                            {"type": "audio"},
                            {"type": "subtitles", "properties": {"language": "eng"}},
                        ]
                    }
                    mock_subtitle_args.return_value = [
                        "-e",
                        "track:s1",
                        "-s",
                        "flag-default=1",
                    ]

                    # Mock subprocess to avoid actual execution
                    with patch("main.subprocess.run") as mock_subprocess:
                        mock_subprocess.return_value = MagicMock()

                        # Call the function with subtitle processing enabled
                        process_mkv_file(
                            tmp_file_path,
                            mkvpropedit_path="/usr/bin/mkvpropedit",
                            mkvmerge_path="/usr/bin/mkvmerge",
                        )

                        # Should call get_mkv_subtitle_args (lines 120-121)
                        mock_subtitle_args.assert_called_once_with(
                            mock_get_metadata.return_value
                        )

                        # Verify the subtitle arguments were added to the command
                        call_args = mock_subprocess.call_args[0][
                            0
                        ]  # First positional arg (the command list)
                        assert "-e" in call_args
                        assert "track:s1" in call_args

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
            main.files_processed = 0
            main.mkv_files_processed = 0
            main.mkv_processing_time = 0.0

    @patch("main.options")
    @patch("main.logger")
    def test_mp4_dry_run_execution_path(self, mock_logger, mock_options):
        """Test MP4 dry run execution path (lines 206-212)"""
        # Setup options for dry run
        mock_options.dry_run = True

        # Reset global counters
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

                # Mock timing
                with patch("main.time.perf_counter") as mock_perf_counter:
                    mock_perf_counter.side_effect = [
                        1000.0,
                        1002.5,
                    ]  # 2.5 second difference

                    # Call the function in dry run mode
                    process_mp4_file(
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
                    assert main.mp4_processing_time == 2.5

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
            main.files_processed = 0
            main.mp4_files_processed = 0
            main.mp4_processing_time = 0.0

    def test_subtitle_args_no_tracks_found(self):
        """Test get_mkv_subtitle_args with no subtitle tracks (lines 401-403)"""
        # Mock options for subtitle processing
        with patch("main.options") as mock_options:
            mock_options.language = "eng"
            mock_options.lang3 = "eng"
            mock_options.force_default_first_subtitle = False

            # Test with metadata containing no subtitle tracks
            metadata = {"tracks": [{"type": "video"}, {"type": "audio"}]}

            with patch("main.logger") as mock_logger:
                result = get_mkv_subtitle_args(metadata)

                # Should return empty list and log no subtitles (lines 406-408)
                assert result == []
                mock_logger.debug.assert_called_with("No subtitle tracks found.")

    def test_subtitle_args_language_fallback(self):
        """Test subtitle args with language fallback logic (lines 401-403)"""
        # Mock options for subtitle processing
        with patch("main.options") as mock_options:
            mock_options.language = "eng"
            mock_options.lang3 = "eng"
            mock_options.set_default_sub_track = True
            mock_options.force_default_first_subtitle = False

            # Test with subtitle track that doesn't match preferred language
            metadata = {
                "tracks": [
                    {"type": "video"},
                    {
                        "type": "subtitles",
                        "properties": {"language": "fre"},
                    },  # French, not English
                ]
            }

            with patch("main.logger") as mock_logger:
                result = get_mkv_subtitle_args(metadata)

                # Should process the track and default it (current behavior when no match found)
                assert len(result) > 0
                assert "-s" in result
                assert (
                    "flag-default=1" in result
                )  # Currently defaults first track when no matching language found
                mock_logger.debug.assert_any_call(
                    "Enabling and defaulting subtitle track s1 (language:eng)"
                )

    @patch("main.options")
    @patch("main.logger")
    def test_mkv_processing_no_audio_tracks(self, mock_logger, mock_options):
        """Test MKV processing with no audio tracks (skips audio track commands)"""
        mock_options.dry_run = False
        mock_options.set_default_sub_track = False
        mock_options.force_default_first_subtitle = False

        # Reset global counters
        main.files_processed = 0
        main.mkv_files_processed = 0
        main.mkv_processing_time = 0.0

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock get_mkv_metadata to return metadata with NO audio tracks
            with patch("main.get_mkv_metadata") as mock_get_metadata:
                mock_get_metadata.return_value = {
                    "tracks": [{"type": "video"}]  # Only video, no audio
                }

                # Mock subprocess to capture the command
                with patch("main.subprocess.run") as mock_subprocess:
                    mock_subprocess.return_value = MagicMock()

                    # Call the function
                    process_mkv_file(
                        tmp_file_path,
                        mkvpropedit_path="/usr/bin/mkvpropedit",
                        mkvmerge_path="/usr/bin/mkvmerge",
                    )

                    # Should log that no audio tracks were found
                    mock_logger.debug.assert_any_call(
                        "No audio tracks found, skipping audio track options"
                    )

                    # Verify command does NOT contain audio track options
                    call_args = mock_subprocess.call_args[0][0]
                    audio_track_args = ["-e", "track:a1", "-d", "name"]
                    for arg in audio_track_args:
                        if arg in call_args:
                            # Find the index and check if it's part of audio track processing
                            idx = call_args.index(arg)
                            if (
                                idx + 1 < len(call_args)
                                and call_args[idx + 1] == "track:a1"
                            ):
                                pytest.fail(
                                    f"Audio track arguments found when no audio tracks exist: {call_args}"
                                )

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
            main.files_processed = 0
            main.mkv_files_processed = 0
            main.mkv_processing_time = 0.0
