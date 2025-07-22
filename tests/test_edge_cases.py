"""
Edge case tests using the created test files
"""

import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from main import (
    get_mkv_metadata,
    get_mp4_metadata,
    has_audio_tracks,
    initialize_tools,
    process_mkv_file,
    process_mp4_file,
)


@pytest.fixture(autouse=True)
def setup_tools():
    """Automatically initialize tools for all tests in this module"""
    initialize_tools()


class TestEdgeCasesWithRealFiles:
    """Test edge cases using actual test files"""

    def test_video_only_mkv(self, test_files_dir):
        """Test processing video-only MKV file"""
        video_only_file = test_files_dir / "video_only.mkv"

        if not video_only_file.exists():
            pytest.skip("video_only.mkv test file not found")

        # Test metadata extraction
        metadata = get_mkv_metadata(str(video_only_file))

        # Should have video track but no audio track
        assert metadata is not None
        assert has_audio_tracks(metadata) is False

        # Should have at least one video track
        video_tracks = [
            t for t in metadata.get("tracks", []) if t.get("type") == "video"
        ]
        assert len(video_tracks) > 0

    def test_audio_only_mkv(self, test_files_dir):
        """Test processing audio-only MKV file"""
        audio_only_file = test_files_dir / "audio_only.mkv"

        if not audio_only_file.exists():
            pytest.skip("audio_only.mkv test file not found")

        # Test metadata extraction
        metadata = get_mkv_metadata(str(audio_only_file))

        # Should have audio track but no video track
        assert metadata is not None
        assert has_audio_tracks(metadata) is True

        # Should have no video tracks
        video_tracks = [
            t for t in metadata.get("tracks", []) if t.get("type") == "video"
        ]
        assert len(video_tracks) == 0

    def test_multi_subtitle_mkv(self, test_files_dir):
        """Test processing MKV file with multiple subtitle tracks"""
        multi_sub_file = test_files_dir / "multi_subtitles.mkv"

        if not multi_sub_file.exists():
            pytest.skip("multi_subtitles.mkv test file not found")

        # Test metadata extraction
        metadata = get_mkv_metadata(str(multi_sub_file))

        # Should have multiple subtitle tracks
        subtitle_tracks = [
            t for t in metadata.get("tracks", []) if t.get("type") == "subtitles"
        ]
        assert len(subtitle_tracks) >= 2

        # Should have different languages
        languages = [
            t.get("properties", {}).get("language_ietf", "") for t in subtitle_tracks
        ]
        assert len(set(languages)) > 1  # Multiple unique languages

    def test_weird_metadata_mp4(self, test_files_dir):
        """Test processing MP4 file with weird metadata characters"""
        weird_file = test_files_dir / "weird_metadata.mp4"

        if not weird_file.exists():
            pytest.skip("weird_metadata.mp4 test file not found")

        # Test metadata extraction
        metadata = get_mp4_metadata(str(weird_file))

        # Should extract metadata with special characters
        assert metadata is not None
        assert metadata.get("title") is not None
        assert metadata.get("description") is not None

        # Should handle special characters properly
        title = metadata.get("title", "")
        description = metadata.get("description", "")

        # Should contain some of the weird characters we added
        assert len(title) > 0
        assert len(description) > 0

    def test_no_metadata_mp4(self, test_files_dir):
        """Test processing MP4 file with no metadata"""
        no_meta_file = test_files_dir / "no_metadata.mp4"

        if not no_meta_file.exists():
            pytest.skip("no_metadata.mp4 test file not found")

        # Test metadata extraction
        metadata = get_mp4_metadata(str(no_meta_file))

        # Should return structure but with None values
        assert metadata is not None
        assert metadata.get("title") is None
        assert metadata.get("description") is None

    def test_tiny_mkv_file(self, test_files_dir):
        """Test processing very small MKV file"""
        tiny_file = test_files_dir / "tiny.mkv"

        if not tiny_file.exists():
            pytest.skip("tiny.mkv test file not found")

        # Test metadata extraction
        metadata = get_mkv_metadata(str(tiny_file))

        # Should still work with tiny files
        assert metadata is not None
        assert "tracks" in metadata

    def test_empty_mkv_file(self, test_files_dir):
        """Test processing empty MKV file"""
        empty_file = test_files_dir / "empty.mkv"

        if not empty_file.exists():
            pytest.skip("empty.mkv test file not found")

        # Test metadata extraction - should fail gracefully
        metadata = get_mkv_metadata(str(empty_file))

        # Should return valid JSON but with recognized=false
        assert metadata is not None
        assert metadata.get("container", {}).get("recognized") is False

    def test_fake_video_file(self, test_files_dir):
        """Test processing fake video file (text file with video extension)"""
        fake_file = test_files_dir / "fake_video.mkv"

        if not fake_file.exists():
            pytest.skip("fake_video.mkv test file not found")

        # Test metadata extraction - should fail gracefully
        metadata = get_mkv_metadata(str(fake_file))

        # Should return valid JSON but with recognized=false
        assert metadata is not None
        assert metadata.get("container", {}).get("recognized") is False

    def test_corrupted_mkv_file(self, test_files_dir):
        """Test processing corrupted MKV file"""
        corrupted_file = test_files_dir / "corrupted.mkv"

        if not corrupted_file.exists():
            pytest.skip("corrupted.mkv test file not found")

        # Test metadata extraction - should return metadata (mkvmerge can read partially corrupted files)
        metadata = get_mkv_metadata(str(corrupted_file))

        # Should return valid metadata dict
        assert metadata is not None
        assert isinstance(metadata, dict)

    def test_not_a_video_file(self, test_files_dir):
        """Test processing binary file with video extension"""
        not_video_file = test_files_dir / "not_a_video.mp4"

        if not not_video_file.exists():
            pytest.skip("not_a_video.mp4 test file not found")

        # Test metadata extraction - should fail gracefully
        metadata = get_mp4_metadata(str(not_video_file))

        # Should return empty dict on error
        assert metadata == {}

    @patch("main.logger")
    def test_permissions_test_file(self, mock_logger, test_files_dir):
        """Test processing file with no read permissions"""
        perm_file = test_files_dir / "permissions_test.mp4"

        if not perm_file.exists():
            pytest.skip("permissions_test.mp4 test file not found")

        # Test metadata extraction - should fail gracefully
        metadata = get_mp4_metadata(str(perm_file))

        # Should return dict with None values on error
        assert metadata == {"title": None, "description": None}

        # Test passed if we got the expected metadata format


class TestErrorHandling:
    """Test error handling in various scenarios"""

    @patch("main.subprocess.run")
    @patch("main.logger")
    def test_mkvmerge_timeout(self, mock_logger, mock_run):
        """Test handling of mkvmerge timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("mkvmerge", 30)

        result = get_mkv_metadata("test.mkv")

        # Should return empty dict and log error
        assert result == {}
        mock_logger.error.assert_called()

    @patch("main.subprocess.run")
    @patch("main.logger")
    def test_atomicparsley_timeout(self, mock_logger, mock_run):
        """Test handling of AtomicParsley timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("AtomicParsley", 30)

        result = get_mp4_metadata("test.mp4")

        # Should return empty dict and log error
        assert result == {}
        mock_logger.error.assert_called()

    @patch("main.subprocess.run")
    @patch("main.logger")
    def test_mkvmerge_file_not_found(self, mock_logger, mock_run):
        """Test handling of mkvmerge file not found"""
        mock_run.side_effect = FileNotFoundError("mkvmerge not found")

        result = get_mkv_metadata("test.mkv")

        # Should return empty dict and log error
        assert result == {}
        mock_logger.error.assert_called()

    @patch("main.subprocess.run")
    @patch("main.logger")
    def test_atomicparsley_file_not_found(self, mock_logger, mock_run):
        """Test handling of AtomicParsley file not found"""
        mock_run.side_effect = FileNotFoundError("AtomicParsley not found")

        result = get_mp4_metadata("test.mp4")

        # Should return empty dict and log error
        assert result == {}
        mock_logger.error.assert_called()

    @patch("main.options")
    @patch("main.mkvpropedit", "/usr/bin/mkvpropedit")
    @patch("main.mkvmerge", "/usr/bin/mkvmerge")
    @patch("main.subprocess.run")
    @patch("main.get_mkv_metadata")
    @patch("main.logger")
    def test_process_mkv_subprocess_error(
        self, mock_logger, mock_get_metadata, mock_run, mock_options
    ):
        """Test handling of subprocess error during MKV processing"""
        # Setup
        mock_options.dry_run = False
        mock_options.set_default_sub_track = False
        mock_options.force_default_first_sub_track = False

        mock_get_metadata.return_value = {"tracks": [{"type": "video"}]}
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "mkvpropedit", output="Error message"
        )

        # Create temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as temp_file:
            temp_file.write(b"fake mkv content")
            temp_path = temp_file.name

        try:
            # Test
            process_mkv_file(temp_path)

            # Should log error and increment error counter
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "Error processing file" in error_call

        finally:
            os.unlink(temp_path)

    @patch("main.options")
    @patch("main.atomicparsley", "/usr/bin/AtomicParsley")
    @patch("main.subprocess.run")
    @patch("main.get_mp4_metadata")
    @patch("main.logger")
    def test_process_mp4_subprocess_error(
        self, mock_logger, mock_get_metadata, mock_run, mock_options
    ):
        """Test handling of subprocess error during MP4 processing"""
        # Setup
        mock_options.dry_run = False

        mock_get_metadata.return_value = {"title": "Test", "description": "Test"}
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "AtomicParsley", output="Error message"
        )

        # Create temp file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"fake mp4 content")
            temp_path = temp_file.name

        try:
            # Test
            process_mp4_file(temp_path)

            # Should log error and increment error counter
            mock_logger.error.assert_called()
            error_call = mock_logger.error.call_args[0][0]
            assert "Error processing file" in error_call

        finally:
            os.unlink(temp_path)


class TestFileSystemEdgeCases:
    """Test file system related edge cases"""

    def test_nonexistent_file_mkv(self):
        """Test processing non-existent MKV file"""
        result = get_mkv_metadata("nonexistent.mkv")

        # Should return empty dict
        assert result == {}

    def test_nonexistent_file_mp4(self):
        """Test processing non-existent MP4 file"""
        result = get_mp4_metadata("nonexistent.mp4")

        # Should return empty dict
        assert result == {}

    def test_directory_instead_of_file(self, temp_dir):
        """Test processing directory instead of file"""
        result = get_mkv_metadata(temp_dir)

        # Should return empty dict
        assert result == {}

    def test_long_file_path(self, temp_dir):
        """Test processing file with very long path"""
        # Create nested directory structure
        long_path = temp_dir
        for i in range(10):
            long_path = os.path.join(long_path, f"very_long_directory_name_{i}")

        os.makedirs(long_path)
        test_file = os.path.join(long_path, "test_file_with_very_long_name.mkv")

        # Create fake file
        with open(test_file, "w") as f:
            f.write("fake content")

        # Should handle long paths gracefully
        result = get_mkv_metadata(test_file)

        # Should return valid JSON but with recognized=false (since it's not a real video file)
        assert result is not None
        assert result.get("container", {}).get("recognized") is False

    def test_unicode_file_path(self, temp_dir):
        """Test processing file with unicode characters in path"""
        unicode_file = os.path.join(temp_dir, "测试文件_éñtürñätīõñål.mkv")

        # Create fake file
        with open(unicode_file, "w") as f:
            f.write("fake content")

        # Should handle unicode paths gracefully
        result = get_mkv_metadata(unicode_file)

        # Should return valid JSON but with recognized=false (since it's not a real video file)
        assert result is not None
        assert result.get("container", {}).get("recognized") is False


class TestMemoryAndPerformance:
    """Test memory and performance related edge cases"""

    @patch("main.json.loads")
    @patch("main.subprocess.run")
    def test_large_json_metadata(self, mock_run, mock_json_loads):
        """Test handling of very large JSON metadata"""
        # Create mock result with large stdout
        mock_result = MagicMock()
        mock_result.stdout = "x" * 10000000  # 10MB of data
        mock_run.return_value = mock_result

        # Mock json.loads to return large structure
        large_metadata = {
            "tracks": [{"type": "video", "properties": {"data": "x" * 1000000}}] * 100
        }
        mock_json_loads.return_value = large_metadata

        result = get_mkv_metadata("test.mkv")

        # Should handle large metadata gracefully
        assert result == large_metadata

    @patch("main.subprocess.run")
    def test_malformed_json_metadata(self, mock_run):
        """Test handling of malformed JSON metadata"""
        # Create mock result with malformed JSON
        mock_result = MagicMock()
        mock_result.stdout = '{"tracks": [{"type": "video", "incomplete": }'
        mock_run.return_value = mock_result

        # Should raise JSONDecodeError
        with pytest.raises(Exception):  # json.JSONDecodeError
            get_mkv_metadata("test.mkv")

    @patch("main.subprocess.run")
    def test_empty_json_metadata(self, mock_run):
        """Test handling of empty JSON metadata"""
        # Create mock result with empty JSON
        mock_result = MagicMock()
        mock_result.stdout = "{}"
        mock_run.return_value = mock_result

        result = get_mkv_metadata("test.mkv")

        # Should return empty dict
        assert result == {}
