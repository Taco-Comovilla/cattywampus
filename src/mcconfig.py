__all__ = ["mcconfig"]

import os
import platform
import sys

from version import __app_name__

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]
import tomli_w  # pip install tomli-w


class Config:
    def __init__(self, filename, custom_config_path=None):
        self.config = {
            "logLevel": 20,
            "mkvmergePath": "",
            "mkvpropeditPath": "",
            "atomicParsleyPath": "",
            "setDefaultSubTrack": False,
            "forceDefaultFirstSubTrack": False,
            "clearAudio": False,
            "useSystemLocale": True,
            "language": "",
            "onlyMkv": False,
            "onlyMp4": False,
            "stdout": False,
            "stdoutOnly": False,
        }

        if custom_config_path:
            # Use custom config file path directly
            self.config_file_path = custom_config_path
            # For custom config, use same directory for log file
            self.config_path = os.path.dirname(custom_config_path)
            self.log_file_path = os.path.join(self.config_path, f"{__app_name__}.log")
        else:
            # Use default config directory
            self.config_path = self._get_config_path()
            self.config_file_path = os.path.join(self.config_path, filename)
            self.log_file_path = os.path.join(self.config_path, f"{__app_name__}.log")
            self._ensure_config_exists(self.config_path, self.config_file_path)

        # Load the config file if it exists
        if os.path.isfile(self.config_file_path):
            try:
                with open(self.config_file_path, "rb") as config_file:
                    loaded_config = tomllib.load(config_file)
                    # Merge loaded config with defaults (loaded values override defaults)
                    self.config.update(loaded_config)
            except tomllib.TOMLDecodeError as e:
                config_type = "custom" if custom_config_path else "default"
                print(
                    f"Error: Invalid TOML syntax in {config_type} configuration file:",
                    file=sys.stderr,
                )
                print(f"  File: {self.config_file_path}", file=sys.stderr)
                print(f"  Error: {e}", file=sys.stderr)
                print(
                    "\nPlease fix the syntax errors in your configuration file.",
                    file=sys.stderr,
                )
                print(
                    "You can use an online TOML validator to check your file format.",
                    file=sys.stderr,
                )
                sys.exit(1)
            except PermissionError:
                config_type = "custom" if custom_config_path else "default"
                print(
                    f"Error: Permission denied reading {config_type} configuration file:",
                    file=sys.stderr,
                )
                print(f"  File: {self.config_file_path}", file=sys.stderr)
                print("Please check file permissions.", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                config_type = "custom" if custom_config_path else "default"
                print(
                    f"Error: Failed to read {config_type} configuration file:",
                    file=sys.stderr,
                )
                print(f"  File: {self.config_file_path}", file=sys.stderr)
                print(f"  Error: {e}", file=sys.stderr)
                sys.exit(1)
        elif custom_config_path:
            raise FileNotFoundError(
                f"Custom config file not found: {custom_config_path}"
            )

    def _get_config_path(self):
        system = platform.system()

        if system == "Windows":
            base_dir = os.getenv("LOCALAPPDATA")
            if not base_dir:
                raise OSError("LOCALAPPDATA is not set")
            return os.path.join(base_dir, __app_name__)

        if system == "Linux":
            base_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
            return os.path.join(base_dir, __app_name__)

        if system == "Darwin":  # macOS
            base_dir = os.path.expanduser("~/Library/Application Support")
            return os.path.join(base_dir, __app_name__)

        raise NotImplementedError(f"Unsupported platform: {system}")

    def _generate_default_config_file(self, config_file_path):
        # Copy example config file instead of generating from scratch
        import shutil
        from pathlib import Path
        
        # Find the example config file relative to this module
        current_dir = Path(__file__).parent
        example_config_path = current_dir / "config.example.toml"
        
        if example_config_path.exists():
            # Copy the example config file
            shutil.copy2(example_config_path, config_file_path)
        else:
            # Fallback to old behavior if example file not found
            with open(config_file_path, "wb") as f:
                f.write(tomli_w.dumps(self.config).encode("utf-8"))

    def _ensure_config_exists(self, config_dir, config_file_path):
        os.makedirs(config_dir, exist_ok=True)
        if not os.path.isfile(config_file_path):
            self._generate_default_config_file(config_file_path)

    def get(self, key, default=None):
        return self.config.get(key, default)


# Default global config instance - will be updated if custom config is provided
mcconfig = None


def initialize_config(custom_config_path=None):
    """Initialize the global config instance with optional custom config path."""
    global mcconfig
    mcconfig = Config("config.toml", custom_config_path)
    return mcconfig


# Initialize with default config for backward compatibility
mcconfig = initialize_config()
