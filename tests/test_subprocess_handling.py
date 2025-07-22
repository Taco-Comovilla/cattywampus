"""
Tests for subprocess handling and tool version edge cases
"""

import subprocess
from unittest.mock import MagicMock, patch

from main import get_tool_version


class TestSubprocessHandling:
    """Test subprocess handling and edge cases"""

    @patch("main.subprocess.run")
    def test_get_tool_version_empty_output_fallback(self, mock_subprocess):
        """Test get_tool_version when stdout is empty, falls back to stderr (line 292)"""
        # Mock subprocess to return empty stdout but content in stderr
        mock_result = MagicMock()
        mock_result.stdout = ""  # Empty stdout
        mock_result.stderr = "Tool version 1.2.3\nAdditional info"
        mock_subprocess.return_value = mock_result

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return first line of stderr when stdout is empty (line 292)
        assert result == "Tool version 1.2.3"

    @patch("main.subprocess.run")
    def test_get_tool_version_no_output_returns_none(self, mock_subprocess):
        """Test get_tool_version returns None when no output (line 292)"""
        # Mock subprocess to return empty stdout and stderr
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return None when no output (line 292)
        assert result is None

    @patch("main.subprocess.run")
    def test_get_tool_version_timeout_exception(self, mock_subprocess):
        """Test get_tool_version handles TimeoutExpired exception"""
        # Mock subprocess to raise TimeoutExpired
        mock_subprocess.side_effect = subprocess.TimeoutExpired("tool", 5)

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return None on timeout (exception handling)
        assert result is None

    @patch("main.subprocess.run")
    def test_get_tool_version_called_process_error(self, mock_subprocess):
        """Test get_tool_version handles CalledProcessError exception"""
        # Mock subprocess to raise CalledProcessError
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, "tool")

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return None on process error (exception handling)
        assert result is None

    @patch("main.subprocess.run")
    def test_get_tool_version_file_not_found_error(self, mock_subprocess):
        """Test get_tool_version handles FileNotFoundError exception"""
        # Mock subprocess to raise FileNotFoundError
        mock_subprocess.side_effect = FileNotFoundError("Tool not found")

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return None on file not found (exception handling)
        assert result is None

    @patch("main.subprocess.run")
    def test_get_tool_version_multiline_output_first_line(self, mock_subprocess):
        """Test get_tool_version returns first line of multiline output"""
        # Mock subprocess to return multiline output
        mock_result = MagicMock()
        mock_result.stdout = "Tool version 1.2.3\nLicense: GPL\nCopyright info"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return only first line (line 291)
        assert result == "Tool version 1.2.3"

    @patch("main.subprocess.run")
    def test_get_tool_version_stderr_fallback_multiline(self, mock_subprocess):
        """Test get_tool_version stderr fallback with multiline output"""
        # Mock subprocess with empty stdout but multiline stderr
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = (
            "Error: Tool version 2.1.0\nWarning: deprecated\nUsage info"
        )
        mock_subprocess.return_value = mock_result

        # Call get_tool_version
        result = get_tool_version("/usr/bin/tool")

        # Should return first line of stderr (lines 287, 291)
        assert result == "Error: Tool version 2.1.0"

    def test_get_tool_version_no_tool_path(self):
        """Test get_tool_version returns None when no tool path provided"""
        # Call with None tool path
        result = get_tool_version(None)

        # Should return None immediately
        assert result is None

        # Call with empty string
        result = get_tool_version("")

        # Should return None immediately
        assert result is None
