"""
Options and configuration parsing module for the application.

This module handles command-line argument parsing, configuration file loading,
and merging of options from both sources with proper validation.
"""

__all__ = ["Options", "parse_options"]

import argparse
import locale
import os
import platform
import sys
from dataclasses import dataclass
from typing import List, Optional

from langcodes import Language

from mcconfig import initialize_config, mcconfig
from mclogger import logger
from version import __app_name__, __version__


def get_system_locale():
    """
    Detect the system's default locale and return it as a BCP 47 language tag.
    Returns None if detection fails.
    """
    try:
        # Try to get the system locale
        system_locale = None

        if platform.system() == "Windows":
            # On Windows, try to get the user's default locale
            try:
                import ctypes

                windll = ctypes.windll.kernel32
                # Get user default locale ID
                lcid = windll.GetUserDefaultLCID()
                # Convert to language tag format
                buffer_size = 85  # LOCALE_NAME_MAX_LENGTH
                buffer = ctypes.create_unicode_buffer(buffer_size)
                windll.LCIDToLocaleName(lcid, buffer, buffer_size, 0)
                system_locale = buffer.value
                # Convert Windows locale format to BCP 47 if needed
                if system_locale and "-" in system_locale:
                    # Windows uses format like "en-US", which is already BCP 47
                    system_locale = system_locale.split("-")[
                        0
                    ]  # Just take language part
            except (OSError, AttributeError, ctypes.ArgumentError):
                # Fallback to Python's locale if Windows locale detection fails
                system_locale, _ = locale.getdefaultlocale()
        else:
            # On Unix-like systems (Linux, macOS)
            # Try environment variables first
            for env_var in ["LC_ALL", "LC_MESSAGES", "LANG"]:
                env_locale = os.environ.get(env_var)
                if env_locale and env_locale != "C" and env_locale != "POSIX":
                    system_locale = env_locale
                    break

            # Fallback to Python's locale detection
            if not system_locale:
                system_locale, _ = locale.getdefaultlocale()

        if system_locale:
            # Clean up the locale string to extract just the language code
            # Handle formats like "en_US.UTF-8", "en_US", "en-US", etc.
            system_locale = system_locale.split(".")[0]  # Remove encoding
            system_locale = system_locale.split("_")[0]  # Remove country
            system_locale = system_locale.split("-")[
                0
            ]  # Remove country (alternative format)

            # Validate that it's a reasonable language code
            if len(system_locale) >= 2 and system_locale.isalpha():
                return system_locale.lower()

    except Exception as e:
        logger.debug(f"Failed to detect system locale: {e}")

    return None


@dataclass
class Options:
    """Container for all parsed options and configuration values."""

    # Command line arguments
    paths: List[str]
    input_file: Optional[str]
    dry_run: bool
    only_mkv: bool
    only_mp4: bool

    # Language configuration
    language: str
    lang_object: Language
    lang3: str
    use_system_locale: bool
    detected_locale: Optional[str]

    # Tool paths
    mkvmerge_path: str
    mkvpropedit_path: str
    atomicparsley_path: str

    # Other config
    log_level: int
    log_file_path: str
    stdout: bool
    stdout_only: bool
    set_default_sub_track: bool
    force_default_first_sub_track: bool
    clear_audio_track_names: bool

    # Source tracking - maps option name to source
    sources: dict[str, str]


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Clean metadata from MKV and MP4 files", prog=__app_name__
    )

    parser.add_argument("paths", nargs="*", help="Files or folders to process")

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        help="Read file paths from a text file (one path per line)",
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying files",
    )

    parser.add_argument(
        "--only-mkv",
        action="store_true",
        help="Only process MKV files (ignore MP4/M4V files)",
    )

    parser.add_argument(
        "--only-mp4",
        action="store_true",
        help="Only process MP4/M4V files (ignore MKV files)",
    )

    # Config override arguments
    parser.add_argument(
        "-L",
        "--language",
        type=str,
        help="Override language setting (BCP 47 language code, e.g. 'en', 'es')",
    )

    parser.add_argument(
        "-g",
        "--loglevel",
        type=int,
        choices=[10, 20, 30, 40, 50],
        help="Override log level (10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL)",
    )

    parser.add_argument(
        "-M",
        "--mkvmerge-path",
        type=str,
        help="Override mkvmergePath - path to mkvmerge binary",
    )

    parser.add_argument(
        "-P",
        "--mkvpropedit-path",
        type=str,
        help="Override mkvpropeditPath - path to mkvpropedit binary",
    )

    parser.add_argument(
        "-A",
        "--atomicparsley-path",
        type=str,
        help="Override atomicParsleyPath - path to AtomicParsley binary",
    )

    parser.add_argument(
        "-s",
        "--set-default",
        action="store_true",
        help="Override setDefaultSubTrack - enable default subtitle track setting",
    )

    parser.add_argument(
        "-f",
        "--default-first",
        action="store_true",
        help="Override forceDefaultFirstSubTrack - force first subtitle track as default",
    )

    parser.add_argument(
        "-a",
        "--clear-audio",
        action="store_true",
        help="Override clearAudio - clear audio track names in MKV files",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Use custom configuration file path (TOML format)",
    )

    parser.add_argument(
        "-l",
        "--logfile",
        type=str,
        help="Override log file path - specify custom log file location for testing",
    )

    parser.add_argument(
        "-S",
        "--stdout",
        action="store_true",
        help="Send program output to console (stdout) as well as log file.",
    )

    parser.add_argument(
        "-T",
        "--stdout-only",
        action="store_true",
        help="Send program output to console (stdout) only, suppressing log file output.",
    )

    return parser


def _setup_language_config() -> tuple[str, Language, str, bool, Optional[str]]:
    """
    Setup language configuration based on system locale detection and config.

    Returns:
        tuple: (language, lang_object, lang3, use_system_locale, detected_locale)
    """
    use_system_locale = mcconfig.get("useSystemLocale", True) if mcconfig else True
    detected_locale = None

    if use_system_locale:
        detected_locale = get_system_locale()
        if detected_locale:
            language = detected_locale
        else:
            # System locale detection failed, fall back to config language
            language = mcconfig.get("language", "") if mcconfig else ""
            # If config language is also empty, use "en" as final fallback
            if not language or language.strip() == "":
                language = "en"
    else:
        language = mcconfig.get("language", "") if mcconfig else ""
        # If config language is empty when not using system locale, use "en"
        if not language or language.strip() == "":
            language = "en"

    try:
        lang_object = Language.get(language)
        # mkvmerge outputs 3-letter language codes in its json
        # but the config file might have a 2-letter lang code
        # so we convert "en" -> "eng" for example
        lang3 = lang_object.to_alpha3()
    except Exception as e:
        logger.warning(
            f"Invalid language tag '{language}': {e}. Falling back to English."
        )
        language = "en"
        lang_object = Language.get(language)
        lang3 = lang_object.to_alpha3()

    return language, lang_object, lang3, use_system_locale, detected_locale


def _validate_options(args: argparse.Namespace, only_mkv: bool, only_mp4: bool) -> None:
    """Validate parsed options and exit with error if invalid."""

    # Validate arguments - must have either paths or input file
    if not args.paths and not args.input:
        parser = _create_argument_parser()
        parser.error(
            "Must provide either file/folder paths or use --input to specify input file"
        )

    # Validate that both file type options aren't enabled simultaneously
    if only_mkv and only_mp4:
        logger.critical(
            "Cannot enable both --only-mkv and --only-mp4 options simultaneously"
        )
        sys.exit(1)


def parse_options() -> Options:
    """
    Parse command line arguments and merge with configuration file values.

    Returns:
        Options: Parsed and validated options object with source tracking
    """
    # Parse command line arguments
    parser = _create_argument_parser()
    args = parser.parse_args()

    # Initialize config with custom path if provided
    global mcconfig
    if args.config:
        mcconfig = initialize_config(args.config)

    # Initialize source tracking
    sources = {}

    # Track command line argument sources
    sources["paths"] = "cli" if args.paths else "default"
    sources["input_file"] = "cli" if args.input else "default"
    sources["dry_run"] = "cli" if args.dry_run else "default"

    # Setup language configuration with CLI override support
    if args.language:
        # CLI language override
        language = args.language
        try:
            lang_object = Language.get(language)
            lang3 = lang_object.to_alpha3()
        except Exception as e:
            logger.warning(
                f"Invalid language tag from CLI '{language}': {e}. Falling back to English."
            )
            language = "en"
            lang_object = Language.get(language)
            lang3 = lang_object.to_alpha3()
        use_system_locale = False
        detected_locale = None
        sources["language"] = "cli"
        sources["use_system_locale"] = "cli override"
    else:
        # Use existing logic for system locale vs config
        language, lang_object, lang3, use_system_locale, detected_locale = (
            _setup_language_config()
        )

        # Track language source
        if use_system_locale:
            if detected_locale:
                sources["language"] = "detected system locale"
            else:
                sources["language"] = "config fallback"
        else:
            sources["language"] = "config"

        sources["use_system_locale"] = "config"

    # Determine file type filtering from CLI args and config with source tracking
    if args.only_mkv:
        only_mkv = True
        sources["only_mkv"] = "cli"
    elif mcconfig and mcconfig.get("onlyMkv", False):
        only_mkv = True
        sources["only_mkv"] = "config"
    else:
        only_mkv = False
        sources["only_mkv"] = "default"

    if args.only_mp4:
        only_mp4 = True
        sources["only_mp4"] = "cli"
    elif mcconfig and mcconfig.get("onlyMp4", False):
        only_mp4 = True
        sources["only_mp4"] = "config"
    else:
        only_mp4 = False
        sources["only_mp4"] = "default"

    # Handle CLI overrides for other config options

    # Tool paths
    if args.mkvmerge_path:
        mkvmerge_path = args.mkvmerge_path
        sources["mkvmerge_path"] = "cli"
    elif mcconfig and mcconfig.get("mkvmergePath", ""):
        mkvmerge_path = mcconfig.get("mkvmergePath", "")
        sources["mkvmerge_path"] = "config"
    else:
        mkvmerge_path = ""
        sources["mkvmerge_path"] = "default"

    if args.mkvpropedit_path:
        mkvpropedit_path = args.mkvpropedit_path
        sources["mkvpropedit_path"] = "cli"
    elif mcconfig and mcconfig.get("mkvpropeditPath", ""):
        mkvpropedit_path = mcconfig.get("mkvpropeditPath", "")
        sources["mkvpropedit_path"] = "config"
    else:
        mkvpropedit_path = ""
        sources["mkvpropedit_path"] = "default"

    # AtomicParsley path
    if args.atomicparsley_path:
        atomicparsley_path = args.atomicparsley_path
        sources["atomicparsley_path"] = "cli"
    elif mcconfig and mcconfig.get("atomicParsleyPath", ""):
        atomicparsley_path = mcconfig.get("atomicParsleyPath", "")
        sources["atomicparsley_path"] = "config"
    else:
        atomicparsley_path = ""
        sources["atomicparsley_path"] = "default"

    # Stdout logging
    if args.stdout:
        stdout = True
        sources["stdout"] = "cli"
    elif mcconfig and mcconfig.get("stdout") is not None:
        stdout = mcconfig.get("stdout", False)
        sources["stdout"] = "config"
    else:
        stdout = False
        sources["stdout"] = "default"

    # Stdout-only logging
    if args.stdout_only:
        stdout_only = True
        sources["stdout_only"] = "cli"
    elif mcconfig and mcconfig.get("stdoutOnly") is not None:
        stdout_only = mcconfig.get("stdoutOnly", False)
        sources["stdout_only"] = "config"
    else:
        stdout_only = False
        sources["stdout_only"] = "default"

    # Log level
    if args.loglevel is not None:
        log_level = args.loglevel
        sources["log_level"] = "cli"
    elif mcconfig and mcconfig.get("logLevel") is not None:
        log_level = mcconfig.get("logLevel", logger.INFO)
        sources["log_level"] = "config"
    else:
        log_level = logger.INFO
        sources["log_level"] = "default"

    # Log file path
    if args.logfile:
        log_file_path = args.logfile
        sources["log_file_path"] = "cli"
    else:
        log_file_path = mcconfig.log_file_path if mcconfig else ""
        sources["log_file_path"] = "config"

    # Set default subtitle track
    if args.set_default:
        set_default_sub_track = True
        sources["set_default_sub_track"] = "cli"
    elif mcconfig and mcconfig.get("setDefaultSubTrack") is not None:
        set_default_sub_track = mcconfig.get("setDefaultSubTrack", False)
        sources["set_default_sub_track"] = "config"
    else:
        set_default_sub_track = False
        sources["set_default_sub_track"] = "default"

    # Force default first subtitle track
    if args.default_first:
        force_default_first_sub_track = True
        sources["force_default_first_sub_track"] = "cli"
    elif mcconfig and mcconfig.get("forceDefaultFirstSubTrack") is not None:
        force_default_first_sub_track = mcconfig.get("forceDefaultFirstSubTrack", False)
        sources["force_default_first_sub_track"] = "config"
    else:
        force_default_first_sub_track = False
        sources["force_default_first_sub_track"] = "default"

    # Clear audio track names
    if args.clear_audio:
        clear_audio_track_names = True
        sources["clear_audio_track_names"] = "cli"
    elif mcconfig and mcconfig.get("clearAudio") is not None:
        clear_audio_track_names = mcconfig.get("clearAudio", False)
        sources["clear_audio_track_names"] = "config"
    else:
        clear_audio_track_names = False
        sources["clear_audio_track_names"] = "default"

    # Validate options
    _validate_options(args, only_mkv, only_mp4)

    # Create and return options object
    return Options(
        # Command line arguments
        paths=args.paths or [],
        input_file=args.input,
        dry_run=args.dry_run,
        only_mkv=only_mkv,
        only_mp4=only_mp4,
        # Language configuration
        language=language,
        lang_object=lang_object,
        lang3=lang3,
        use_system_locale=use_system_locale,
        detected_locale=detected_locale,
        # Tool paths
        mkvmerge_path=mkvmerge_path,
        mkvpropedit_path=mkvpropedit_path,
        atomicparsley_path=atomicparsley_path,
        # Other config
        log_level=log_level,
        log_file_path=log_file_path,
        stdout=stdout,
        stdout_only=stdout_only,
        set_default_sub_track=set_default_sub_track,
        force_default_first_sub_track=force_default_first_sub_track,
        clear_audio_track_names=clear_audio_track_names,
        # Source tracking
        sources=sources,
    )
