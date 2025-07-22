"""
Pytest configuration and shared fixtures
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add src directory to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_files_dir():
    """Path to the test files directory"""
    return Path(__file__).parent.parent / "test-data"


@pytest.fixture
def sample_mkv_metadata():
    """Sample MKV metadata structure"""
    return {
        "container": {"properties": {"title": "Test Movie Title"}},
        "tracks": [
            {"type": "video", "properties": {"track_name": "Video Track Name"}},
            {"type": "audio", "properties": {"track_name": "Audio Track Name"}},
            {
                "type": "subtitles",
                "properties": {
                    "track_name": "English Subtitles",
                    "language": "eng",
                    "language_ietf": "en",
                },
            },
        ],
    }


@pytest.fixture
def sample_mkv_metadata_no_audio():
    """Sample MKV metadata structure without audio tracks"""
    return {
        "container": {"properties": {"title": "Video Only Movie"}},
        "tracks": [
            {"type": "video", "properties": {"track_name": "Video Track Name"}},
            {
                "type": "subtitles",
                "properties": {
                    "track_name": "English Subtitles",
                    "language": "eng",
                    "language_ietf": "en",
                },
            },
        ],
    }


@pytest.fixture
def sample_mp4_metadata():
    """Sample MP4 metadata structure"""
    return {"title": "Test MP4 Title", "description": "Test MP4 Description"}


@pytest.fixture
def mock_config():
    """Mock configuration object"""

    class MockConfig:
        def __init__(self):
            self.config = {
                "logLevel": 20,
                "mkvmergePath": "",
                "mkvpropeditPath": "",
                "atomicParsleyPath": "",
                "setDefaultSubTrack": False,
                "forceDefaultFirstSubTrack": False,
                "useSystemLocale": True,
                "language": "en",
                "onlyMkv": False,
                "onlyMp4": False,
            }
            self.log_file_path = "/tmp/test.log"

        def get(self, key, default=None):
            return self.config.get(key, default)

    return MockConfig()
