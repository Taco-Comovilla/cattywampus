"""
Tests for audio track name clearing functionality
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from src.main import has_audio_tracks, process_mkv_file


class TestAudioTrackClearing:
    """Test audio track name clearing functionality"""

    def test_clear_audio_track_names_enabled(self):
        """Test that audio track names are cleared when option is enabled"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock the global options with clearing enabled
            with patch("src.main.options") as mock_options:
                mock_options.clear_audio_track_names = True
                mock_options.dry_run = True
                mock_options.set_default_sub_track = False
                mock_options.force_default_first_sub_track = False

                # Mock metadata with audio tracks
                with patch("src.main.get_mkv_metadata") as mock_get_metadata:
                    mock_get_metadata.return_value = {
                        "tracks": [
                            {"type": "video"},
                            {"type": "audio"},
                        ]
                    }

                    with patch("src.main.subprocess.run") as mock_subprocess:
                        with patch("src.main.logger") as mock_logger:
                            # Call the function
                            result = process_mkv_file(
                                tmp_file_path,
                                mkvpropedit_path="/usr/bin/mkvpropedit",
                                mkvmerge_path="/usr/bin/mkvmerge",
                            )

                            # Verify that clearing message was logged
                            mock_logger.debug.assert_any_call(
                                "Clearing audio track names"
                            )

        finally:
            # Clean up
            tmp_path = Path(tmp_file_path)
            if tmp_path.exists():
                tmp_path.unlink()

    def test_clear_audio_track_names_disabled(self):
        """Test that audio track names are preserved when option is disabled"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock the global options with clearing disabled
            with patch("src.main.options") as mock_options:
                mock_options.clear_audio_track_names = False
                mock_options.dry_run = True
                mock_options.set_default_sub_track = False
                mock_options.force_default_first_sub_track = False

                # Mock metadata with audio tracks
                with patch("src.main.get_mkv_metadata") as mock_get_metadata:
                    mock_get_metadata.return_value = {
                        "tracks": [
                            {"type": "video"},
                            {"type": "audio"},
                        ]
                    }

                    with patch("src.main.subprocess.run") as mock_subprocess:
                        with patch("src.main.logger") as mock_logger:
                            # Call the function
                            result = process_mkv_file(
                                tmp_file_path,
                                mkvpropedit_path="/usr/bin/mkvpropedit",
                                mkvmerge_path="/usr/bin/mkvmerge",
                            )

                            # Verify that preservation message was logged
                            mock_logger.debug.assert_any_call(
                                "Audio tracks found but clearing disabled, preserving audio track names"
                            )

        finally:
            # Clean up
            tmp_path = Path(tmp_file_path)
            if tmp_path.exists():
                tmp_path.unlink()

    def test_no_audio_tracks_found(self):
        """Test behavior when no audio tracks are present"""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".mkv", delete=False) as tmp_file:
            tmp_file.write(b"fake mkv content")
            tmp_file_path = tmp_file.name

        try:
            # Mock the global options
            with patch("src.main.options") as mock_options:
                mock_options.clear_audio_track_names = True
                mock_options.dry_run = True
                mock_options.set_default_sub_track = False
                mock_options.force_default_first_sub_track = False

                # Mock metadata with no audio tracks
                with patch("src.main.get_mkv_metadata") as mock_get_metadata:
                    mock_get_metadata.return_value = {
                        "tracks": [
                            {"type": "video"},
                            {"type": "subtitles"},
                        ]
                    }

                    with patch("src.main.subprocess.run") as mock_subprocess:
                        with patch("src.main.logger") as mock_logger:
                            # Call the function
                            result = process_mkv_file(
                                tmp_file_path,
                                mkvpropedit_path="/usr/bin/mkvpropedit",
                                mkvmerge_path="/usr/bin/mkvmerge",
                            )

                            # Verify that no audio tracks message was logged
                            mock_logger.debug.assert_any_call(
                                "No audio tracks found, skipping audio track options"
                            )

        finally:
            # Clean up
            tmp_path = Path(tmp_file_path)
            if tmp_path.exists():
                tmp_path.unlink()

    def test_has_audio_tracks_function(self):
        """Test the has_audio_tracks helper function"""
        # Test with audio tracks
        metadata_with_audio = {
            "tracks": [
                {"type": "video"},
                {"type": "audio"},
                {"type": "subtitles"},
            ]
        }
        assert has_audio_tracks(metadata_with_audio) is True

        # Test without audio tracks
        metadata_without_audio = {
            "tracks": [
                {"type": "video"},
                {"type": "subtitles"},
            ]
        }
        assert has_audio_tracks(metadata_without_audio) is False

        # Test with empty tracks
        metadata_empty = {"tracks": []}
        assert has_audio_tracks(metadata_empty) is False

        # Test with no tracks key
        metadata_no_tracks = {}
        assert has_audio_tracks(metadata_no_tracks) is False


class TestAudioTrackClearingCLI:
    """Test CLI parsing for audio track clearing option"""

    def test_cli_short_option(self):
        """Test -a short option"""
        import sys

        from src.mcoptions import parse_options

        original_argv = sys.argv
        try:
            sys.argv = [__app_name__, "-a", "test.mkv"]
            options = parse_options()
            assert options.clear_audio_track_names is True
            assert options.sources["clear_audio_track_names"] == "cli"
        finally:
            sys.argv = original_argv

    def test_cli_long_option(self):
        """Test --clear-audio long option"""
        import sys

        from src.mcoptions import parse_options

        original_argv = sys.argv
        try:
            sys.argv = [__app_name__, "--clear-audio", "test.mkv"]
            options = parse_options()
            assert options.clear_audio_track_names is True
            assert options.sources["clear_audio_track_names"] == "cli"
        finally:
            sys.argv = original_argv

    def test_cli_default_disabled(self):
        """Test that default is False"""
        import sys

        from src.mcoptions import parse_options

        original_argv = sys.argv
        try:
            sys.argv = [__app_name__, "test.mkv"]
            options = parse_options()
            assert options.clear_audio_track_names is False
            # Source can be either "default" or "config" depending on config availability
            assert options.sources["clear_audio_track_names"] in ["default", "config"]
        finally:
            sys.argv = original_argv

    def test_config_override(self):
        """Test config file override"""
        import sys
        import tempfile

        from src.mcoptions import parse_options

        # Create a temporary config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as tmp_config:
            tmp_config.write("clearAudio = true\n")
            tmp_config_path = tmp_config.name

        original_argv = sys.argv
        try:
            sys.argv = [__app_name__, "-c", tmp_config_path, "test.mkv"]
            options = parse_options()
            assert options.clear_audio_track_names is True
            assert options.sources["clear_audio_track_names"] == "config"
        finally:
            sys.argv = original_argv
            import os

            if os.path.exists(tmp_config_path):
                os.unlink(tmp_config_path)

    def test_cli_overrides_config(self):
        """Test that CLI option overrides config file"""
        import sys
        import tempfile

        from src.mcoptions import parse_options

        # Create a temporary config file with clearing disabled
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as tmp_config:
            tmp_config.write("clearAudio = false\n")
            tmp_config_path = tmp_config.name

        original_argv = sys.argv
        try:
            # CLI should override config
            sys.argv = [__app_name__, "-c", tmp_config_path, "-a", "test.mkv"]
            options = parse_options()
            assert options.clear_audio_track_names is True
            assert options.sources["clear_audio_track_names"] == "cli"
        finally:
            sys.argv = original_argv
            import os

            if os.path.exists(tmp_config_path):
                os.unlink(tmp_config_path)
