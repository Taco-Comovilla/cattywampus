"""
Tests for tool initialization and edge cases
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from main import (
    get_mkv_metadata,
    get_mp4_metadata,
    get_tool_version,
    process_mkv_file,
)


class TestToolInitialization:
    """Test tool initialization edge cases and error handling"""

    def test_tool_path_validation_simple(self):
        """Test simple tool path validation scenarios"""
        # This test focuses on testing the reachable code paths
        # rather than complex integration scenarios

        # Test that we can call functions with None tool paths
        # and handle the validation appropriately
        result = get_tool_version(None)
        assert result is None

        result = get_tool_version("")
        assert result is None

    @patch("main.atomicparsley", None)
    def test_get_mp4_metadata_missing_tool_runtime_error(self):
        """Test get_mp4_metadata raises RuntimeError when tool is missing (line 332)"""
        # Should raise RuntimeError when AtomicParsley tool is not available
        # Both the parameter and global variable should be None
        with pytest.raises(RuntimeError, match="AtomicParsley tool not available"):
            get_mp4_metadata("test.mp4", atomicparsley_path=None)

    @patch("main.mkvmerge", None)
    def test_get_mkv_metadata_missing_tool_runtime_error(self):
        """Test get_mkv_metadata raises RuntimeError when tool is missing (line 301)"""
        # Should raise RuntimeError when mkvmerge tool is not available
        # Both the parameter and global variable should be None
        with pytest.raises(RuntimeError, match="mkvmerge tool not available"):
            get_mkv_metadata("test.mkv", mkvmerge_path=None)

    @patch("main.options")
    @patch("main.logger")
    def test_mkv_subtitle_processing_enabled(self, mock_logger, mock_options):
        """Test MKV subtitle processing path (line 121)"""
        # Setup options to enable subtitle processing
        mock_options.dry_run = False
        mock_options.set_default_sub_track = True
        mock_options.force_default_first_subtitle = False

        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock get_mkv_metadata to return metadata with subtitles
            with patch("main.get_mkv_metadata") as mock_get_metadata:
                with patch("main.get_mkv_subtitle_args") as mock_subtitle_args:
                    mock_get_metadata.return_value = {
                        "tracks": [
                            {"type": "video"},
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

                        # Should call get_mkv_subtitle_args (line 121)
                        mock_subtitle_args.assert_called_once_with(
                            mock_get_metadata.return_value
                        )

        finally:
            # Clean up
            Path(tmp_file_path).unlink()
