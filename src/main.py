import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from mclogger import logger
from mcoptions import parse_options


def find_tool_in_common_locations(tool_name):
    """
    Search for a tool in common macOS and Linux installation locations.
    This helps when tools are installed via Homebrew or other package managers
    but aren't in the PATH available to Quick Actions or other restricted contexts.
    """
    # If it's already a full path and exists, return it
    tool_path_obj = Path(tool_name)
    if (
        tool_path_obj.is_absolute()
        and tool_path_obj.is_file()
        and os.access(tool_name, os.X_OK)
    ):
        return tool_name

    # First try the standard PATH lookup
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path

    # Common installation locations on macOS and Linux
    common_paths = [
        "/opt/homebrew/bin",  # Apple Silicon Homebrew
        "/usr/local/bin",  # Intel Homebrew and other installations
        "/usr/bin",  # System installations
        "/opt/local/bin",  # MacPorts
    ]

    for path in common_paths:
        full_path_obj = Path(path) / tool_name
        full_path = str(full_path_obj)
        if full_path_obj.is_file() and os.access(full_path, os.X_OK):
            return full_path

    return None


# Global variables for tool paths and processing counters
mkvpropedit = False
mkvmerge = False
atomicparsley = False


def initialize_tools(
    mkvpropedit_path=None, mkvmerge_path=None, atomicparsley_path=None
):
    """
    Initialize global tool paths. This function is primarily for testing
    to allow setting up tools without going through the full main() setup.
    """
    global mkvpropedit, mkvmerge, atomicparsley

    # Use provided paths or try to find tools in PATH/common locations
    mkvpropedit = mkvpropedit_path or find_tool_in_common_locations("mkvpropedit")
    mkvmerge = mkvmerge_path or find_tool_in_common_locations("mkvmerge")
    atomicparsley = atomicparsley_path or find_tool_in_common_locations("AtomicParsley")


files_processed = 0
files_errored = 0
folders_processed = 0
folders_errored = 0
files_with_errors = []

# File type specific tracking
mkv_files_processed = 0
mp4_files_processed = 0
mkv_processing_time = 0.0
mp4_processing_time = 0.0

# Global options object - will be set in main()
options = None


def format_error_string(error_str):
    return error_str.replace("\n", "").replace("\r", "")


def has_audio_tracks(metadata):
    """Check if the MKV file has any audio tracks."""
    tracks = metadata.get("tracks", [])
    return any(track.get("type", "") == "audio" for track in tracks)


def log_mkv_metadata(metadata):
    video_index = 1
    audio_index = 1
    subtitle_index = 1

    logger.debug("Original MKV metadata:")

    seginfo_title = metadata.get("container", {}).get("properties", {}).get("title", "")
    logger.debug(f"  Segment info title: {seginfo_title}")

    for track in metadata.get("tracks", []):
        track_name = track.get("properties", {}).get("track_name", "")
        track_lang = ""
        track_ietf = ""
        if track.get("type", "") == "video":
            logger.debug(f"  Video track {video_index} name: {track_name}")
            video_index = video_index + 1
        elif track.get("type", "") == "audio":
            logger.debug(f"  Audio track {audio_index} name: {track_name}")
            audio_index = audio_index + 1
        elif track.get("type", "") == "subtitles":
            track_ietf = track.get("properties", {}).get("language_ietf", "")
            track_lang = track.get("properties", {}).get("language", "")
            logger.debug(f"  Subtitle track {subtitle_index} name: {track_name}")
            logger.debug(
                f"  Subtitle track {subtitle_index} language_ietf: {track_ietf}"
            )
            logger.debug(f"  Subtitle track {subtitle_index} language: {track_lang}")
            subtitle_index = subtitle_index + 1


def process_mkv_file(file_path, track_id=1, mkvpropedit_path=None, mkvmerge_path=None):
    global files_processed, files_errored, files_with_errors
    global mkv_files_processed, mkv_processing_time

    # Use provided paths or fall back to global variables
    mkvpropedit_tool = mkvpropedit_path or mkvpropedit
    mkvmerge_tool = mkvmerge_path or mkvmerge

    if not mkvpropedit_tool:
        logger.info("mkvpropedit not found in PATH. Skipping.")
        return
    if not mkvmerge_tool:
        logger.info("mkvmerge not found in PATH. Skipping.")
        return

    # Start timing for MKV processing
    mkv_start_time = time.perf_counter()

    logger.info(f"Processing MKV file: {file_path}")
    file_size = round(Path(file_path).stat().st_size / 1024)  # size in KB
    logger.debug(f"File size: {file_size} KB")

    metadata = get_mkv_metadata(file_path, mkvmerge_tool)
    log_mkv_metadata(metadata)

    try:
        command = [
            mkvpropedit_tool,
            "-q",
            file_path,
            "-d",
            "title",
            "-e",
            f"track:v{track_id}",
            "-d",
            "name",
            "-e",
            f"track:v{track_id}",
            "-s",
            "language=und",
        ]

        # Only add audio track options if audio tracks exist and clearing is enabled
        if has_audio_tracks(metadata) and options.clear_audio_track_names:
            command.extend(["-e", f"track:a{track_id}", "-d", "name"])
            logger.debug("Clearing audio track names")
        elif has_audio_tracks(metadata):
            logger.debug(
                "Audio tracks found but clearing disabled, preserving audio track names"
            )
        else:
            logger.debug("No audio tracks found, skipping audio track options")
        if options.set_default_sub_track or options.force_default_first_sub_track:
            command = command + get_mkv_subtitle_args(metadata)
        logger.debug(f"mkvpropedit command: {' '.join(command)}")

        if options.dry_run:
            logger.info("DRY RUN: Would execute mkvpropedit command")
            files_processed = files_processed + 1
            mkv_files_processed = mkv_files_processed + 1
            # Track processing time even for dry run
            mkv_duration = time.perf_counter() - mkv_start_time
            mkv_processing_time = mkv_processing_time + mkv_duration
            logger.info("Processing finished (dry run).")
        else:
            start_time = time.perf_counter()
            subprocess.run(command, check=True, capture_output=True, encoding="cp437")
            duration = time.perf_counter() - start_time
            logger.debug(f"Command took: {duration:.3f} seconds")

            files_processed = files_processed + 1
            mkv_files_processed = mkv_files_processed + 1
            # Track total processing time for this MKV file
            mkv_duration = time.perf_counter() - mkv_start_time
            mkv_processing_time = mkv_processing_time + mkv_duration
            logger.info("Processing finished.")

    except subprocess.CalledProcessError as e:
        files_errored = files_errored + 1
        files_with_errors.append(file_path)
        mkv_files_processed = mkv_files_processed + 1
        # Track processing time even for failed files
        mkv_duration = time.perf_counter() - mkv_start_time
        mkv_processing_time = mkv_processing_time + mkv_duration
        logger.error(f"Error processing file: {format_error_string(e.output)}")


def process_mp4_file(file_path, atomicparsley_path=None):
    global files_processed, files_errored, files_with_errors
    global mp4_files_processed, mp4_processing_time

    # Use provided path or fall back to global variable
    atomicparsley_tool = atomicparsley_path or atomicparsley

    if not atomicparsley_tool:
        logger.info("AtomicParsley not found in PATH. Skipping.")
        return

    # Start timing for MP4 processing
    mp4_start_time = time.perf_counter()

    logger.info(f"Processing MP4 file: {file_path}")
    file_size = round(Path(file_path).stat().st_size / 1024)  # size in KB
    logger.debug(f"File size: {file_size} KB")

    metadata = get_mp4_metadata(file_path, atomicparsley_tool)

    if not metadata:
        logger.info("No metadata found in file.")
        # Still count as processed even if no metadata
        mp4_files_processed = mp4_files_processed + 1
        mp4_duration = time.perf_counter() - mp4_start_time
        mp4_processing_time = mp4_processing_time + mp4_duration
        return

    logger.debug("Original MP4 metadata:")
    logger.debug(f"  Title: {metadata.get('title') or ''}")
    logger.debug(f"  Description: {metadata.get('description') or ''}")

    try:
        command = [
            atomicparsley_tool,
            file_path,
            "--title",
            "",
            "--description",
            "",
            "--preventOptimizing",
            "--overWrite",
        ]

        # Format command for logging, replacing empty strings with quoted empty strings
        formatted_command = " ".join('""' if arg == "" else arg for arg in command)
        logger.debug(f"AtomicParsley command: {formatted_command}")

        if options.dry_run:
            logger.info("DRY RUN: Would execute AtomicParsley command")
            files_processed = files_processed + 1
            mp4_files_processed = mp4_files_processed + 1
            # Track processing time even for dry run
            mp4_duration = time.perf_counter() - mp4_start_time
            mp4_processing_time = mp4_processing_time + mp4_duration
            logger.info("Processing finished (dry run).")
        else:
            start_time = time.perf_counter()
            subprocess.run(command, check=True, capture_output=True, encoding="cp437")
            duration = time.perf_counter() - start_time
            logger.debug(f"Command took: {duration:.3f} seconds")
            files_processed = files_processed + 1
            mp4_files_processed = mp4_files_processed + 1
            # Track total processing time for this MP4 file
            mp4_duration = time.perf_counter() - mp4_start_time
            mp4_processing_time = mp4_processing_time + mp4_duration
            logger.info("Processing finished.")

    except subprocess.CalledProcessError as e:
        files_errored = files_errored + 1
        files_with_errors.append(file_path)
        mp4_files_processed = mp4_files_processed + 1
        # Track processing time even for failed files
        mp4_duration = time.perf_counter() - mp4_start_time
        mp4_processing_time = mp4_processing_time + mp4_duration
        logger.error(f"Error processing file: {format_error_string(e.output)}")


def process_folder(folder_path):
    global folders_processed, folders_errored
    file_path = ""

    # Check if folder exists first
    if not Path(folder_path).exists():
        folders_errored = folders_errored + 1
        logger.error(f"Folder does not exist: {folder_path}")
        return

    if not Path(folder_path).is_dir():
        folders_errored = folders_errored + 1
        logger.error(f"Path is not a directory: {folder_path}")
        return

    try:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith(".mkv"):
                    if not options.only_mp4:  # Process MKV unless only MP4 is enabled
                        file_path = str(Path(root) / file)
                        process_mkv_file(file_path)
                elif file.endswith((".mp4", ".m4v", ".mp4v")):
                    if not options.only_mkv:  # Process MP4 unless only MKV is enabled
                        file_path = str(Path(root) / file)
                        process_mp4_file(file_path)

        folders_processed = folders_processed + 1

    except Exception as e:
        folders_errored = folders_errored + 1
        logger.error(f"Error processing folder {folder_path}: {e}")


def get_tool_version(tool_path, version_arg="--version"):
    if not tool_path:
        return None

    try:
        result = subprocess.run(
            [tool_path, version_arg],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Extract version from output
        output = result.stdout.strip()
        if not output:
            output = result.stderr.strip()

        # Return first line which usually contains version info
        if output:
            return output.split("\n")[0]
        return None

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ):
        return None


def get_mkv_metadata(file_path, mkvmerge_path=None):
    # Use provided path or fall back to global variable
    tool_path = mkvmerge_path or mkvmerge
    if not tool_path:
        raise RuntimeError("mkvmerge tool not available")

    command = [tool_path, "-J", file_path]
    logger.debug(f"mkvmerge command: {' '.join(command)}")

    try:
        start_time = time.perf_counter()
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding="cp437",  # https://stackoverflow.com/a/73546303
        )
        duration = time.perf_counter() - start_time
        logger.debug(f"Metadata collection took: {duration:.3f} seconds")
        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        # mkvmerge -J outputs JSON on error
        logger.error(
            f"Error reading metadata from {file_path}: {format_error_string(e.output)}"
        )
        return {}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # Handle timeouts and missing tool
        logger.error(f"Error reading metadata from {file_path}: {e}")
        return {}


def get_mp4_metadata(file_path, atomicparsley_path=None):
    # Use provided path or fall back to global variable
    tool_path = atomicparsley_path or atomicparsley
    if not tool_path:
        raise RuntimeError("AtomicParsley tool not available")

    command = [tool_path, file_path, "-t"]
    logger.debug(f"AtomicParsley command: {' '.join(command)}")

    try:
        start_time = time.perf_counter()
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, encoding="utf-8"
        )
        duration = time.perf_counter() - start_time
        logger.debug(f"Metadata collection took: {duration:.3f} seconds")

        title = None
        description = None

        for line in result.stdout.splitlines():
            if 'Atom "©nam"' in line:
                title_match = re.search(r'Atom "©nam" contains:\s*(.*)', line)
                if title_match:
                    title = title_match.group(1).strip()
            elif 'Atom "desc"' in line:
                desc_match = re.search(r'Atom "desc" contains:\s*(.*)', line)
                if desc_match:
                    description = desc_match.group(1).strip()

        return {"title": title, "description": description}

    except subprocess.CalledProcessError as e:
        logger.error(
            f"Error reading metadata from {file_path}: {format_error_string(e.output)}"
        )
        return {}
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        # Handle timeouts and missing tool
        logger.error(f"Error reading metadata from {file_path}: {e}")
        return {}


def get_mkv_subtitle_args(metadata):
    subtitle_args = []
    track_found = False
    found_at_index = 1
    current_index = 1
    tracks = metadata.get("tracks", [])
    sub_tracks = []

    subtitle_track_index = 1
    for track in tracks:
        if track.get("type", "") == "subtitles":
            sub_tracks.append(track)
            this_language = (
                track.get("properties", {}).get("language_ietf")
                or track.get("properties", {}).get("language")
                or "{unknown}"
            )
            if (
                this_language == options.lang3 or this_language == options.language
            ) and not track_found:
                track_found = True
                found_at_index = subtitle_track_index
                logger.debug(
                    f"Subtitle track in {options.language} found at index s{found_at_index}"
                )
            subtitle_track_index = subtitle_track_index + 1

    if len(sub_tracks) > 0:
        for track in sub_tracks:
            s_track = f"track:s{current_index}"
            if current_index == found_at_index or (
                not track_found
                and current_index == 1
                and options.force_default_first_sub_track
            ):
                logger.debug(
                    f"Enabling and defaulting subtitle track s{current_index} (language:{options.language})"
                )
                subtitle_args += ["-e", s_track, "-s", "flag-enabled=1"]
                subtitle_args += ["-e", s_track, "-s", "flag-default=1"]
            else:
                this_language = (
                    track.get("properties", {}).get("language_ietf")
                    or track.get("properties", {}).get("language")
                    or ""
                )
                logger.debug(
                    f"Un-defaulting subtitle track s{current_index} (language:{this_language})"
                )
                subtitle_args += ["-e", s_track, "-s", "flag-default=0"]
            current_index = current_index + 1
        return subtitle_args
    logger.debug("No subtitle tracks found.")
    return []


def read_paths_from_file(input_file):
    """
    Read file paths from a text file, handling both DOS and Unix line endings.
    Returns a list of paths relative to the current working directory.
    """
    paths = []
    try:
        with Path(input_file).open(encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                # Strip whitespace and handle both DOS (\r\n) and Unix (\n) line endings
                path = line.strip()

                # Skip empty lines and comments (lines starting with #)
                if not path or path.startswith("#"):
                    continue

                # Resolve relative to current working directory
                resolved_path = str(Path(path).resolve())

                # Check if path exists
                if not Path(resolved_path).exists():
                    logger.warning(
                        f"Path from input file line {line_num} does not exist: {path}"
                    )
                    continue

                paths.append(resolved_path)

    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    except PermissionError:
        logger.error(f"Permission denied reading input file: {input_file}")
        sys.exit(1)
    except UnicodeDecodeError:
        logger.error(f"Input file contains invalid UTF-8 encoding: {input_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading input file {input_file}: {e}")
        sys.exit(1)

    return paths


def main():
    global mkvpropedit, mkvmerge, atomicparsley, options
    global files_processed, files_errored, folders_processed, folders_errored, files_with_errors
    global mkv_files_processed, mp4_files_processed, mkv_processing_time, mp4_processing_time

    # Record script start time for total runtime calculation
    script_start_time = time.perf_counter()

    # Parse options and configuration
    options = parse_options()

    logger.setup(
        log_file_path=options.log_file_path,
        log_level=options.log_level,
        stdout_enabled=options.stdout,
        stdout_only=options.stdout_only,
    )

    # Collect all paths to process
    all_paths = []

    # Add direct paths from command line
    if options.paths:
        all_paths.extend(options.paths)

    # Add paths from input file
    if options.input_file:
        input_paths = read_paths_from_file(options.input_file)
        all_paths.extend(input_paths)

    # Remove duplicates while preserving order
    original_count = len(all_paths)
    seen = set()
    unique_paths = []
    for path in all_paths:
        # Use absolute path for comparison to catch different ways of specifying same file
        abs_path = str(Path(path).resolve())
        if abs_path not in seen:
            seen.add(abs_path)
            unique_paths.append(path)
    all_paths = unique_paths
    deduplicated_count = len(all_paths)

    # Filter paths by file type if filtering is enabled
    filtered_count = 0
    if options.only_mkv or options.only_mp4:
        filtered_paths = []
        for path in all_paths:
            if Path(path).is_file():
                if (path.lower().endswith(".mkv") and not options.only_mp4) or (
                    (path.lower().endswith(".mp4") or path.lower().endswith(".m4v"))
                    and not options.only_mkv
                ):
                    filtered_paths.append(path)
            elif Path(path).is_dir():
                # Always include directories - filtering happens during folder processing
                filtered_paths.append(path)

        filtered_count = len(all_paths) - len(filtered_paths)
        all_paths = filtered_paths

    logger.info("*" * 20 + " BEGINNING RUN " + "*" * 20)
    if options.dry_run:
        logger.info("*" * 23 + " DRY RUN " + "*" * 23)

    # Log Python version with execution environment
    python_version = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )

    # Detect execution environment
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running from PyInstaller bundle
        env_info = "bundled"
    else:
        # Running from system Python
        env_info = "system"

    logger.debug(f"Python {python_version} ({env_info})")

    # Log path collection after run headers
    if options.paths:
        count = len(options.paths)
        plural = "paths" if count != 1 else "path"
        logger.debug(f"Added {count} {plural} from command line")
    if options.input_file:
        count = len(input_paths)
        plural = "paths" if count != 1 else "path"
        logger.debug(f"Added {count} {plural} from input file: {options.input_file}")

    # Log filtering results after path collection
    if filtered_count > 0:
        file_type = "MP4/M4V" if options.only_mkv else "MKV"
        plural = "files" if filtered_count != 1 else "file"
        logger.debug(f"Filtered out {filtered_count} {file_type} {plural}")

    # Log duplicate removal if any duplicates were found
    if original_count != deduplicated_count:
        removed_count = original_count - deduplicated_count
        plural = "paths" if removed_count != 1 else "path"
        logger.debug(f"Removed {removed_count} duplicate {plural}")

    count = len(all_paths)
    plural = "paths" if count != 1 else "path"
    logger.debug(f"Processing {count} unique {plural}")

    # Log configuration options with sources
    logger.debug("Options:")

    # Language configuration
    logger.debug(
        f"  language: {options.lang_object.display_name()} ({options.language}/{options.lang3}) - {options.sources['language']}"
    )

    # Tool paths
    logger.debug(
        f"  mkvmergePath: {options.mkvmerge_path or 'not set'} - {options.sources['mkvmerge_path']}"
    )
    logger.debug(
        f"  mkvpropeditPath: {options.mkvpropedit_path or 'not set'} - {options.sources['mkvpropedit_path']}"
    )
    logger.debug(
        f"  atomicParsleyPath: {options.atomicparsley_path or 'not set'} - {options.sources['atomicparsley_path']}"
    )

    # File filtering options
    logger.debug(f"  onlyMkv: {options.only_mkv} - {options.sources['only_mkv']}")
    logger.debug(f"  onlyMp4: {options.only_mp4} - {options.sources['only_mp4']}")

    # Other options
    logger.debug(
        f"  setDefaultSubTrack: {options.set_default_sub_track} - {options.sources['set_default_sub_track']}"
    )
    logger.debug(
        f"  useSystemLocale: {options.use_system_locale} - {options.sources['use_system_locale']}"
    )
    logger.debug(f"  dryRun: {options.dry_run} - {options.sources['dry_run']}")
    logger.debug(f"  logLevel: {options.log_level} - {options.sources['log_level']}")

    # Use direct binary paths or fallback to system PATH
    if options.mkvpropedit_path:
        mkvpropedit = options.mkvpropedit_path
    else:
        mkvpropedit = (
            "mkvpropedit.exe" if platform.system() == "Windows" else "mkvpropedit"
        )

    if options.mkvmerge_path:
        mkvmerge = options.mkvmerge_path
    else:
        mkvmerge = "mkvmerge.exe" if platform.system() == "Windows" else "mkvmerge"

    if options.atomicparsley_path:
        atomicparsley = options.atomicparsley_path
    else:
        atomicparsley = (
            "AtomicParsley.exe" if platform.system() == "Windows" else "AtomicParsley"
        )

    # Verify binaries exist (either as direct paths or in PATH/common locations)
    mkvpropedit = find_tool_in_common_locations(mkvpropedit)
    mkvmerge = find_tool_in_common_locations(mkvmerge)
    atomicparsley = find_tool_in_common_locations(atomicparsley)

    logger.debug(f"PATH: {os.environ.get('PATH')}")

    if not mkvpropedit and not mkvmerge and not atomicparsley:
        logger.critical("neither mkvtoolnix nor AtomicParsley found in PATH. Exiting.")
        sys.exit()

    # Log tool discovery with sources
    logger.debug("Tool discovery:")
    if mkvpropedit:
        tool_source = "direct path" if options.mkvpropedit_path else "PATH"
        logger.debug(f"  mkvpropedit: {mkvpropedit} - {tool_source}")
        version = get_tool_version(mkvpropedit)
        if version:
            logger.info(f"mkvpropedit version: {version}")
    else:
        logger.debug("  mkvpropedit: not found")

    if mkvmerge:
        tool_source = "direct path" if options.mkvmerge_path else "PATH"
        logger.debug(f"  mkvmerge: {mkvmerge} - {tool_source}")
        version = get_tool_version(mkvmerge)
        if version:
            logger.info(f"mkvmerge version: {version}")
    else:
        logger.debug("  mkvmerge: not found")

    if atomicparsley:
        tool_source = "direct path" if options.atomicparsley_path else "PATH"
        logger.debug(f"  AtomicParsley: {atomicparsley} - {tool_source}")
        version = get_tool_version(atomicparsley)
        if version:
            logger.info(f"{version}")
    else:
        logger.debug("  AtomicParsley: not found")

    for path in all_paths:
        if Path(path).is_file():
            if path.lower().endswith(".mkv"):
                process_mkv_file(path)
            elif path.lower().endswith(".mp4") or path.lower().endswith(".m4v"):
                process_mp4_file(path)
        elif os.path.isdir(path):
            process_folder(path)

    logger.info(f"Total folders processed: {folders_processed}")
    if folders_errored:
        logger.info(f"Total folders errored: {folders_errored}")
    logger.info(f"Total files processed: {files_processed}")
    if files_errored:
        logger.info(f"Total files errored: {files_errored}")
        logger.info("Files with errors:")
        for error_file in files_with_errors:
            logger.info(f"  {error_file}")

    # Log file type specific statistics
    if mkv_files_processed > 0:
        logger.info(
            f"MKV files processed: {mkv_files_processed}, total MKV processing time: {mkv_processing_time:.3f} seconds"
        )
    if mp4_files_processed > 0:
        logger.info(
            f"MP4 files processed: {mp4_files_processed}, total MP4 processing time: {mp4_processing_time:.3f} seconds"
        )

    # Log total runtime
    total_runtime = time.perf_counter() - script_start_time
    logger.info(f"Total runtime: {total_runtime:.3f} seconds")

    logger.info("*" * 20 + " ENDING RUN " + "*" * 23)
    sys.exit()


if __name__ == "__main__":
    main()
