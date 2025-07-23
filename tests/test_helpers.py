"""
Helper functions for tests to mock tool availability
"""

from unittest.mock import MagicMock, Mock


def setup_mock_tools():
    """
    Set up mock tool paths for testing.
    Returns dict with mock tool paths that can be used in tests.
    """
    return {
        "mkvmerge_path": "/usr/bin/mkvmerge",
        "mkvpropedit_path": "/usr/bin/mkvpropedit",
        "atomicparsley_path": "/usr/bin/AtomicParsley",
    }


def setup_mock_logger():
    """Set up a mock logger for testing"""
    mock_logger = Mock()
    mock_logger.debug = Mock()
    mock_logger.info = Mock()
    mock_logger.error = Mock()
    mock_logger.warning = Mock()
    mock_logger.critical = Mock()
    return mock_logger


def setup_mock_options():
    """Set up mock options object for testing"""
    mock_options = Mock()
    mock_options.language = "en"
    mock_options.lang3 = "eng"
    mock_options.force_default_first_subtitle = False
    mock_options.set_default_sub_track = False
    mock_options.set_default_audio_track = False
    mock_options.dry_run = False
    return mock_options


def setup_complete_mock_options(**overrides):
    """Set up a complete mock options object with all attributes for main.options patches"""
    defaults = {
        'language': 'en',
        'lang3': 'eng', 
        'force_default_first_subtitle': False,
        'set_default_sub_track': False,
        'set_default_audio_track': False,
        'clear_audio_track_names': False,
        'dry_run': False,
        'only_mkv': False,
        'only_mp4': False,
        'sources': {
            'set_default_sub_track': 'default',
            'set_default_audio_track': 'default',
            'force_default_first_subtitle': 'default',
        }
    }
    
    # Apply overrides
    defaults.update(overrides)
    
    mock_options = Mock()
    for key, value in defaults.items():
        setattr(mock_options, key, value)
    
    return mock_options


def create_mock_options(**overrides):
    """Create a complete mock options object with all required attributes"""
    mock_lang_object = MagicMock()
    mock_lang_object.display_name.return_value = "English"

    # Default options
    default_options = {
        "paths": [],
        "input_file": None,
        "dry_run": False,
        "only_mkv": False,
        "only_mp4": False,
        "log_file_path": None,
        "log_level": 20,
        "stdout": False,
        "stdout_only": False,
        "set_default_sub_track": False,
        "force_default_first_subtitle": False,
        "set_default_audio_track": False,
        "clear_audio_track_names": False,
        "use_system_locale": False,
        "language": "en",
        "lang3": "eng",
        "lang_object": mock_lang_object,
        "mkvpropedit_path": None,
        "mkvmerge_path": None,
        "atomicparsley_path": None,
    }

    # Default sources for all options
    default_sources = {
        "language": "default",
        "mkvmerge_path": "default",
        "mkvpropedit_path": "default",
        "atomicparsley_path": "default",
        "only_mkv": "default",
        "only_mp4": "default",
        "set_default_sub_track": "default",
        "force_default_first_subtitle": "default",
        "set_default_audio_track": "default",
        "clear_audio_track_names": "default",
        "use_system_locale": "default",
        "dry_run": "default",
        "log_level": "default",
        "stdout": "default",
        "stdout_only": "default",
    }

    # Apply overrides
    default_options.update(overrides)
    if "sources" in overrides:
        default_sources.update(overrides["sources"])

    # Create mock object
    mock_options = MagicMock()
    for key, value in default_options.items():
        setattr(mock_options, key, value)

    mock_options.sources = default_sources

    return mock_options
