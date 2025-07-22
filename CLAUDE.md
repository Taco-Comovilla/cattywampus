# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Python 3.9+** with virtual environments (.venv)
- **PyInstaller** for standalone executable packaging
- **External tools**: MKVToolNix (mkvpropedit, mkvmerge), AtomicParsley
- **Testing**: pytest with coverage and custom markers
- **Linting**: ruff, black, mypy with VS Code integration
- **Templates**: String template system for cross-platform builds
- **Config**: TOML-based configuration system

## Project Structure

```
src/                    # Core Python modules
├── main.py            # Entry point and primary logic
├── mcoptions.py       # CLI argument parsing and config
├── mcconfig.py        # Configuration management
├── mclogger.py        # Logging system
└── version.py         # Centralized metadata

templates/             # Template files for generation
├── docs/              # Documentation templates
├── windows/           # Windows build file templates  
└── macos/            # macOS integration templates

build/                 # Generated build files (tracked exceptions)
dist/                  # Built executables by platform
tests/                 # Comprehensive test suite
.vscode/              # VS Code development settings
```

**Generated Files** (DO NOT EDIT):
- `README.adoc`, `CONTRIBUTING.adoc` - Generated from templates
- `build/windows/setup.iss`, `build/windows/file_version_info.txt`

## Commands

### Development Setup
```bash
# See global CLAUDE.md for standard Python venv setup
pip install -r requirements.txt
```

### Building
```bash
./build-app                    # Build for current platform
./build-app --release          # Build with compressed distribution
./build-app --generate-docs    # Regenerate docs from templates

# Build creates platform-specific executables in:
# - dist/linux/cattywampus
# - dist/macos/cattywampus  
# - dist/windows/cattywampus.exe
```

### Installation & Uninstallation
```bash
./install-integrations         # Install file manager integrations (Linux/macOS)
./install-integrations --dry-run  # Preview installation
./uninstall-integrations       # Remove all integrations
./uninstall-integrations --dry-run  # Preview removal
```

### Testing
```bash
./run-tests quick             # Core tests (recommended)
./run-tests coverage          # With coverage report
./run-tests all               # Full suite
./run-tests --help            # All options
```

### Code Quality
```bash
# See global CLAUDE.md for standard code quality commands
# All standard tools (black, ruff, mypy) are configured in pyproject.toml
```

## Project-Specific Conventions

- **Testing**: pytest with custom markers (`integration`, `slow`) and coverage
- **External tools**: MKVToolNix and AtomicParsley integration
- **Cross-platform**: Handles Linux, macOS, and Windows differences
- **Template system**: String templates with ${VARIABLE} substitution

## Project Workflow

### Template System (Project-Specific)
- **Regenerate** docs after template changes: `./build-app --generate-docs`
- Templates located in `templates/` directory with ${VARIABLE} syntax

### Project Testing
- **Run tests** before committing: `./run-tests quick`
- Use `./run-tests coverage` for coverage reports

### Current Branch Status
- **Current work**: `rename-to-cattywampus` branch for major refactoring

## Core Files & Utilities

### Primary Components
- **main.py**: Entry point, file processing, external tool integration
- **mcoptions.py**: CLI parsing, configuration precedence, validation
- **mcconfig.py**: Cross-platform config paths, TOML handling
- **mclogger.py**: File/console logging with level control
- **version.py**: Centralized metadata for templates and build

### Key Functions
- `process_mkv_file()`: MKV metadata removal with mkvpropedit
- `process_mp4_file()`: MP4 metadata removal with AtomicParsley  
- `get_mkv_metadata()`: JSON parsing of mkvmerge output
- `parse_options()`: CLI + config + defaults precedence handling

### File Manager Integrations
- **nautilus_extension.py**: GTK-based Nautilus context menu
- **install-integrations**: Unified Linux/macOS installer with template processing
- **uninstall-integrations**: Complete removal with dry-run support

### Build System
- **build-app**: PyInstaller builds, template processing, release packaging
- **templates/**: String template files with ${VARIABLE} substitution
- Generated executables: `dist/{platform}/cattywampus[.exe]`

## "Do Not Touch" List

### Generated Files (Auto-Updated)
- `README.adoc` - Generated from `templates/docs/README.adoc.template`
- `CONTRIBUTING.adoc` - Generated from `templates/docs/CONTRIBUTING.adoc.template`
- `build/windows/setup.iss` - Generated from template for InnoSetup
- `build/windows/file_version_info.txt` - Generated for PyInstaller

### Build Artifacts
- `dist/` directory contents - PyInstaller output
- `build/` directory (except tracked Windows files)
- `htmlcov/` - Coverage reports
- `__pycache__/`, `.pytest_cache/` - Python/test caches

### External Dependencies
- MKVToolNix binaries (`mkvpropedit`, `mkvmerge`) - User-installed
- AtomicParsley binary - User-installed
- VS Code extensions - Recommended in `.vscode/extensions.json`

### Configuration Files
- `.vscode/settings.json` - Team development settings
- `mypy.ini`, `pyproject.toml` - Tool configurations
- `requirements.txt` - Python dependencies

## Project-Specific Notes

- **Config changes**: Update tests in `tests/` that assume old default values
- **External dependencies**: Requires MKVToolNix and AtomicParsley binaries
- **File processing**: Handles .mkv, .mp4, and .m4v files with metadata removal
- **Cross-platform builds**: PyInstaller creates standalone executables