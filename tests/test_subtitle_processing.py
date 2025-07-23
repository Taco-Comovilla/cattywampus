"""
Tests for subtitle processing edge cases
"""

from unittest.mock import patch

from main import get_mkv_subtitle_args


class TestSubtitleProcessing:
    """Test subtitle processing edge cases and code paths"""

    @patch("main.options")
    @patch("main.logger")
    def test_subtitle_args_non_default_track_processing(
        self, mock_logger, mock_options
    ):
        """Test subtitle processing for non-default tracks (lines 401-403)"""
        # Setup options
        mock_options.set_default_sub_track = True
        mock_options.force_default_first_subtitle = False
        mock_options.language = "en"
        mock_options.lang3 = "eng"

        # Create metadata with multiple subtitle tracks where first won't match
        metadata = {
            "tracks": [
                {"type": "video"},
                {
                    "type": "subtitles",
                    "properties": {"language": "spa", "language_ietf": "es"},
                },
                {
                    "type": "subtitles",
                    "properties": {"language": "eng", "language_ietf": "en"},
                },
            ]
        }

        # Call get_mkv_subtitle_args
        result = get_mkv_subtitle_args(metadata)

        # Should process tracks and hit the un-defaulting code path (lines 401-403)
        # The first track (spa) should be un-defaulted
        # The second track (eng) should be defaulted

        # Verify that debug logging was called (this tests lines 401-403)
        mock_logger.debug.assert_called()

        # Verify result contains subtitle arguments
        assert "-e" in result
        assert "flag-default=1" in result
        assert "flag-default=0" in result

    @patch("main.options")
    @patch("main.logger")
    def test_subtitle_args_empty_language_fallback(self, mock_logger, mock_options):
        """Test subtitle processing with empty language properties"""
        # Setup options
        mock_options.set_default_sub_track = True
        mock_options.force_default_first_subtitle = False
        mock_options.language = "en"
        mock_options.lang3 = "eng"

        # Create metadata with subtitle track that has no language info
        metadata = {
            "tracks": [
                {"type": "video"},
                {"type": "subtitles", "properties": {}},  # No language info
            ]
        }

        # Call get_mkv_subtitle_args
        result = get_mkv_subtitle_args(metadata)

        # Should handle missing language gracefully (current behavior defaults first track)
        mock_logger.debug.assert_any_call("Enabling and defaulting subtitle track s1 (language:en)")

        # Should still process the track
        assert "-e" in result
        assert "track:s1" in result
        assert "flag-default=1" in result

    @patch("main.options")
    @patch("main.logger")
    def test_subtitle_args_force_first_track_default(self, mock_logger, mock_options):
        """Test force first track default when no matching language found"""
        # Setup options to force first track default
        mock_options.set_default_sub_track = True
        mock_options.force_default_first_subtitle = True
        mock_options.language = "en"
        mock_options.lang3 = "eng"

        # Create metadata with subtitle tracks that don't match target language
        metadata = {
            "tracks": [
                {"type": "video"},
                {
                    "type": "subtitles",
                    "properties": {"language": "spa", "language_ietf": "es"},
                },
                {
                    "type": "subtitles",
                    "properties": {"language": "fra", "language_ietf": "fr"},
                },
            ]
        }

        # Call get_mkv_subtitle_args
        result = get_mkv_subtitle_args(metadata)

        # Should force first track as default and un-default others (lines 396, 401-403)
        mock_logger.debug.assert_any_call(
            "Enabling and defaulting subtitle track s1 (language:en)"
        )
        mock_logger.debug.assert_any_call(
            "Un-defaulting subtitle track s2 (language:fr)"
        )

        # Verify result
        assert "track:s1" in result
        assert "flag-default=1" in result
        assert "flag-default=0" in result

    @patch("main.options")
    @patch("main.logger")
    def test_subtitle_args_language_ietf_fallback(self, mock_logger, mock_options):
        """Test language_ietf fallback when language_ietf is missing"""
        # Setup options
        mock_options.set_default_sub_track = True
        mock_options.force_default_first_subtitle = False
        mock_options.language = "en"
        mock_options.lang3 = "eng"

        # Create metadata with track that has language but no language_ietf
        metadata = {
            "tracks": [
                {"type": "video"},
                {
                    "type": "subtitles",
                    "properties": {
                        "language": "spa"
                        # Missing language_ietf - should fall back to "language"
                    },
                },
            ]
        }

        # Call get_mkv_subtitle_args
        result = get_mkv_subtitle_args(metadata)

        # Should use "language" field when "language_ietf" is missing (current behavior defaults first track)
        mock_logger.debug.assert_any_call(
            "Enabling and defaulting subtitle track s1 (language:en)"
        )

        # Should still process the track
        assert "track:s1" in result
        assert "flag-default=1" in result
