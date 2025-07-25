#!/usr/bin/env python3
"""Setup script for cattywampus Debian packaging."""

from setuptools import setup, find_packages
import sys
from pathlib import Path

# Add src to path for local imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from version import (
        __version__,
        __app_name__,
        __app_description__,
        __repo_base_url__,
        __organization__,
        __maintainer_email__,
        __license__,
    )
except ImportError as e:
    print(f"Error importing version information: {e}")
    sys.exit(1)

# Read long description from README
readme_path = Path(__file__).parent / "README.adoc"
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = __app_description__

# Runtime dependencies for Debian packaging
install_requires = [
    "tomli>=1.2.3; python_version < '3.11'",
    "tomli-w>=1.0.0",
    "pycountry>=20.7.3",
]

setup(
    name=__app_name__,
    version=__version__,
    description=__app_description__,
    long_description=long_description,
    long_description_content_type="text/plain",
    author=__organization__,
    author_email=__maintainer_email__, 
    url=__repo_base_url__,
    license="MIT",
    
    # Package structure
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    py_modules=["main", "mcconfig", "mclogger", "mcoptions", "version"],
    
    # Entry point
    entry_points={
        "console_scripts": [
            f"{__app_name__}=main:main",
        ],
    },
    
    # Dependencies
    install_requires=install_requires,
    python_requires=">=3.9",
    
    # Data files for Debian packaging
    data_files=[
        ("share/cattywampus", ["src/config.example.toml"]),
        ("share/doc/cattywampus", ["README.adoc", "LICENSE"]),
    ],
    
    # Package metadata
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console", 
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: System :: Archiving",
        "Topic :: Utilities",
    ],
    
    keywords="video metadata mkv mp4 cleaner privacy",
    project_urls={
        "Bug Reports": f"{__repo_base_url__}/issues",
        "Source": __repo_base_url__,
    },
)