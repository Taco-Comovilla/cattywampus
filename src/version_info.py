"""
Version information utilities for the application.
This module provides version information for the application.
"""

from version import __app_name__, __version__


def get_version_info():
    """Return detailed version information."""
    return {
        "version": __version__,
        "name": __app_name__,
        "description": "Clean metadata from MKV and MP4 files",
        "author": "Taco Comovilla https://github.com/Taco-Comovilla",
        "license": "MIT License",
    }


def print_version_info():
    """Print version information to stdout."""
    info = get_version_info()
    print(f"{info['name']} {info['version']}")
    print(f"Description: {info['description']}")
    print(f"Author: {info['author']}")
    print(f"License: {info['license']}")


if __name__ == "__main__":
    print_version_info()
