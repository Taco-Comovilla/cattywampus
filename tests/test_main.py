"""
Unit tests for main.py functions
"""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import (
    format_error_string,
    get_mkv_metadata,
    get_mkv_subtitle_args,
    get_mp4_metadata,
    get_tool_version,
    has_audio_tracks,
    initialize_tools,
    log_mkv_metadata,
    read_paths_from_file,
)


@pytest.fixture(autouse=True)
def setup_tools():
    """Automatically initialize tools for all tests in this module"""
    initialize_tools()


class TestHasAudioTracks:
    """Test the has_audio_tracks function"""

    def test_has_audio_tracks_with_audio(self, sample_mkv_metadata):
        """Test detection of audio tracks when they exist"""
        assert has_audio_tracks(sample_mkv_metadata) is True

    def test_has_audio_tracks_without_audio(self, sample_mkv_metadata_no_audio):
        """Test detection when no audio tracks exist"""
        assert has_audio_tracks(sample_mkv_metadata_no_audio) is False

    def test_has_audio_tracks_empty_metadata(self):
        """Test handling of empty metadata"""
        assert has_audio_tracks({}) is False

    def test_has_audio_tracks_no_tracks_key(self):
        """Test handling of metadata without tracks key"""
        metadata = {"container": {"properties": {}}}
        assert has_audio_tracks(metadata) is False

    def test_has_audio_tracks_empty_tracks_list(self):
        """Test handling of empty tracks list"""
        metadata = {"tracks": []}
        assert has_audio_tracks(metadata) is False

    def test_has_audio_tracks_only_video_tracks(self):
        """Test with only video tracks"""
        metadata = {"tracks": [{"type": "video"}, {"type": "subtitles"}]}
        assert has_audio_tracks(metadata) is False

    def test_has_audio_tracks_multiple_audio_tracks(self):
        """Test with multiple audio tracks"""
        metadata = {
            "tracks": [
                {"type": "video"},
                {"type": "audio"},
                {"type": "audio"},
                {"type": "subtitles"},
            ]
        }
        assert has_audio_tracks(metadata) is True


class TestLogMkvMetadata:
    """Test the log_mkv_metadata function"""

    @patch("main.logger")
    def test_log_mkv_metadata_complete(self, mock_logger, sample_mkv_metadata):
        """Test logging complete MKV metadata"""
        log_mkv_metadata(sample_mkv_metadata)

        # Verify debug calls were made
        mock_logger.debug.assert_called()
        calls = mock_logger.debug.call_args_list

        # Check that title was logged
        assert any(
            "Segment info title: Test Movie Title" in str(call) for call in calls
        )

        # Check that tracks were logged
        assert any(
            "Video track 1 name: Video Track Name" in str(call) for call in calls
        )
        assert any(
            "Audio track 1 name: Audio Track Name" in str(call) for call in calls
        )
        assert any(
            "Subtitle track 1 name: English Subtitles" in str(call) for call in calls
        )

    @patch("main.logger")
    def test_log_mkv_metadata_empty(self, mock_logger):
        """Test logging empty metadata"""
        log_mkv_metadata({})

        mock_logger.debug.assert_called()
        calls = mock_logger.debug.call_args_list

        # Should still log header and empty title
        assert any("Original MKV metadata:" in str(call) for call in calls)
        assert any("Segment info title: " in str(call) for call in calls)


class TestGetMkvMetadata:
    """Test the get_mkv_metadata function"""

    @patch("main.subprocess.run")
    @patch("main.mkvmerge", "mkvmerge")
    def test_get_mkv_metadata_success(self, mock_run):
        """Test successful metadata extraction"""
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            {"container": {"properties": {"title": "Test"}}}
        )
        mock_run.return_value = mock_result

        result = get_mkv_metadata("test.mkv")

        assert result == {"container": {"properties": {"title": "Test"}}}
        mock_run.assert_called_once()

    @patch("main.subprocess.run")
    @patch("main.mkvmerge", "mkvmerge")
    @patch("main.logger")
    def test_get_mkv_metadata_subprocess_error(self, mock_logger, mock_run):
        """Test handling of subprocess errors"""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "mkvmerge", output="Error output"
        )

        result = get_mkv_metadata("test.mkv")

        assert result == {}
        mock_logger.error.assert_called_once()

    @patch("main.subprocess.run")
    @patch("main.mkvmerge", "mkvmerge")
    def test_get_mkv_metadata_invalid_json(self, mock_run):
        """Test handling of invalid JSON output"""
        mock_result = MagicMock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        with pytest.raises(json.JSONDecodeError):
            get_mkv_metadata("test.mkv")


class TestGetMp4Metadata:
    """Test the get_mp4_metadata function"""

    @patch("main.subprocess.run")
    def test_get_mp4_metadata_success(self, mock_run):
        """Test successful MP4 metadata extraction"""
        mock_result = MagicMock()
        mock_result.stdout = """Atom "©nam" contains: Test Title
Atom "desc" contains: Test Description
Other line"""
        mock_run.return_value = mock_result

        result = get_mp4_metadata("test.mp4")

        assert result == {"title": "Test Title", "description": "Test Description"}

    @patch("main.subprocess.run")
    def test_get_mp4_metadata_no_metadata(self, mock_run):
        """Test MP4 with no title/description metadata"""
        mock_result = MagicMock()
        mock_result.stdout = "No relevant metadata found"
        mock_run.return_value = mock_result

        result = get_mp4_metadata("test.mp4")

        assert result == {"title": None, "description": None}

    @patch("main.subprocess.run")
    @patch("main.logger")
    def test_get_mp4_metadata_subprocess_error(self, mock_logger, mock_run):
        """Test handling of subprocess errors"""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "AtomicParsley", output="Error output"
        )

        result = get_mp4_metadata("test.mp4")

        assert result == {}
        mock_logger.error.assert_called_once()


class TestGetMkvSubtitleArgs:
    """Test the get_mkv_subtitle_args function"""

    @patch("main.options")
    @patch("main.logger")
    def test_get_mkv_subtitle_args_language_found(self, mock_logger, mock_options):
        """Test subtitle args when target language is found"""
        mock_options.language = "en"
        mock_options.lang3 = "eng"
        mock_options.force_default_first_sub_track = False

        metadata = {
            "tracks": [
                {"type": "video"},
                {
                    "type": "subtitles",
                    "properties": {"language_ietf": "en", "language": "eng"},
                },
                {
                    "type": "subtitles",
                    "properties": {"language_ietf": "es", "language": "spa"},
                },
            ]
        }

        result = get_mkv_subtitle_args(metadata)

        expected = [
            "-e",
            "track:s1",
            "-s",
            "flag-enabled=1",
            "-e",
            "track:s1",
            "-s",
            "flag-default=1",
            "-e",
            "track:s2",
            "-s",
            "flag-default=0",
        ]
        assert result == expected

    @patch("main.options")
    @patch("main.logger")
    def test_get_mkv_subtitle_args_no_subtitles(self, mock_logger, mock_options):
        """Test subtitle args when no subtitle tracks exist"""
        mock_options.language = "en"
        mock_options.lang3 = "eng"
        mock_options.force_default_first_sub_track = False

        metadata = {"tracks": [{"type": "video"}, {"type": "audio"}]}

        result = get_mkv_subtitle_args(metadata)

        assert result == []
        mock_logger.debug.assert_called_with("No subtitle tracks found.")

    @patch("main.options")
    @patch("main.logger")
    def test_get_mkv_subtitle_args_force_first_default(self, mock_logger, mock_options):
        """Test forcing first subtitle track as default"""
        mock_options.language = "en"
        mock_options.lang3 = "eng"
        mock_options.force_default_first_sub_track = True

        metadata = {
            "tracks": [
                {"type": "video"},
                {
                    "type": "subtitles",
                    "properties": {"language_ietf": "fr", "language": "fre"},
                },
            ]
        }

        result = get_mkv_subtitle_args(metadata)

        expected = [
            "-e",
            "track:s1",
            "-s",
            "flag-enabled=1",
            "-e",
            "track:s1",
            "-s",
            "flag-default=1",
        ]
        assert result == expected


class TestGetToolVersion:
    """Test the get_tool_version function"""

    @patch("main.subprocess.run")
    def test_get_tool_version_success(self, mock_run):
        """Test successful tool version extraction"""
        mock_result = MagicMock()
        mock_result.stdout = "mkvmerge v90.0 ('Hanging On') 64-bit\nmore info"
        mock_run.return_value = mock_result

        result = get_tool_version("mkvmerge")

        assert result == "mkvmerge v90.0 ('Hanging On') 64-bit"

    @patch("main.subprocess.run")
    def test_get_tool_version_stderr_fallback(self, mock_run):
        """Test fallback to stderr when stdout is empty"""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "Version info from stderr"
        mock_run.return_value = mock_result

        result = get_tool_version("tool")

        assert result == "Version info from stderr"

    @patch("main.subprocess.run")
    def test_get_tool_version_subprocess_error(self, mock_run):
        """Test handling of subprocess errors"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "tool")

        result = get_tool_version("tool")

        assert result is None

    @patch("main.subprocess.run")
    def test_get_tool_version_timeout(self, mock_run):
        """Test handling of timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("tool", 5)

        result = get_tool_version("tool")

        assert result is None

    def test_get_tool_version_no_tool_path(self):
        """Test handling of empty tool path"""
        result = get_tool_version("")
        assert result is None

        result = get_tool_version(None)
        assert result is None


class TestReadPathsFromFile:
    """Test the read_paths_from_file function"""

    def test_read_paths_from_file_success(self, temp_dir):
        """Test successful reading of paths from file"""
        test_file = str(Path(temp_dir) / "paths.txt")
        test_paths = ["path1.mkv", "path2.mp4", "# This is a comment", "", "path3.mkv"]

        with open(test_file, "w") as f:
            f.write("\n".join(test_paths))

        # Create dummy files so they exist
        for path in ["path1.mkv", "path2.mp4", "path3.mkv"]:
            with open(path, "w") as f:
                f.write("")

        try:
            result = read_paths_from_file(test_file)

            expected = [
                os.path.abspath("path1.mkv"),
                os.path.abspath("path2.mp4"),
                os.path.abspath("path3.mkv"),
            ]
            assert result == expected
        finally:
            # Clean up
            for path in ["path1.mkv", "path2.mp4", "path3.mkv"]:
                if Path(path).exists():
                    Path(path).unlink()

    def test_read_paths_from_file_nonexistent_file(self):
        """Test handling of non-existent input file"""
        with pytest.raises(SystemExit):
            read_paths_from_file("nonexistent.txt")

    def test_read_paths_from_file_nonexistent_paths(self, temp_dir):
        """Test handling of non-existent paths in file"""
        test_file = str(Path(temp_dir) / "paths.txt")

        with open(test_file, "w") as f:
            f.write("nonexistent1.mkv\nnonexistent2.mp4\n")

        with patch("main.logger") as mock_logger:
            result = read_paths_from_file(test_file)

            assert result == []
            # Should log warnings about non-existent paths
            assert mock_logger.warning.call_count == 2

    def test_read_paths_from_file_dos_line_endings(self, temp_dir):
        """Test handling of DOS line endings"""
        test_file = str(Path(temp_dir) / "paths.txt")

        with open(test_file, "wb") as f:
            f.write(b"path1.mkv\r\npath2.mp4\r\n")

        # Create dummy files
        with open("path1.mkv", "w") as f:
            f.write("")
        with open("path2.mp4", "w") as f:
            f.write("")

        try:
            result = read_paths_from_file(test_file)

            expected = [os.path.abspath("path1.mkv"), os.path.abspath("path2.mp4")]
            assert result == expected
        finally:
            # Clean up
            for path in ["path1.mkv", "path2.mp4"]:
                if Path(path).exists():
                    Path(path).unlink()


class TestFormatErrorString:
    """Test the format_error_string function"""

    def test_format_error_string_with_newlines(self):
        """Test removal of newline characters"""
        error_str = "Error message\nwith multiple\nlines"
        result = format_error_string(error_str)
        assert result == "Error messagewith multiplelines"

    def test_format_error_string_with_carriage_returns(self):
        """Test removal of carriage return characters"""
        error_str = "Error message\rwith carriage\rreturns"
        result = format_error_string(error_str)
        assert result == "Error messagewith carriagereturns"

    def test_format_error_string_with_mixed_line_endings(self):
        """Test removal of mixed line endings"""
        error_str = "Error message\r\nwith mixed\n\rline endings"
        result = format_error_string(error_str)
        assert result == "Error messagewith mixedline endings"

    def test_format_error_string_empty_string(self):
        """Test handling of empty string"""
        result = format_error_string("")
        assert result == ""

    def test_format_error_string_no_line_endings(self):
        """Test string without line endings remains unchanged"""
        error_str = "Error message without line endings"
        result = format_error_string(error_str)
        assert result == error_str

    def test_format_error_string_only_line_endings(self):
        """Test string with only line endings"""
        error_str = "\n\r\n\r"
        result = format_error_string(error_str)
        assert result == ""

    def test_format_error_string_preserves_spaces(self):
        """Test that spaces are preserved while removing line endings"""
        error_str = "Error message   with\nspaces   and\rtabs"
        result = format_error_string(error_str)
        assert result == "Error message   withspaces   andtabs"
