# Debian Packaging for cattywampus

This document describes the Debian packaging support added to cattywampus for issue #30.

## Overview

The cattywampus project now supports building standard Debian packages (.deb files) that can be installed using `apt` or `dpkg` on Debian/Ubuntu systems. This provides a more standard installation method that will eventually replace the custom build/install/uninstall scripts.

## Building a Debian Package

### Prerequisites

Install the required Debian packaging tools:

```bash
sudo apt-get install devscripts debhelper dh-python
```

### Build the Package

Use the extended build script with the `--deb` option:

```bash
./build-app --deb
```

This will:
1. Generate Debian packaging files from templates
2. Build the package using `debuild`
3. Create a `.deb` file in the parent directory

## Installation

Once the package is built, install it with:

```bash
sudo dpkg -i ../cattywampus_1.1.0-1_all.deb
```

Or install dependencies automatically:

```bash
sudo apt-get install -f ../cattywampus_1.1.0-1_all.deb
```

## Package Features

### Automatic Dependency Management

The package declares dependencies on:
- `mkvtoolnix` (for MKV file processing)
- `atomicparsley` (for MP4/M4V file processing)
- Required Python libraries

These will be installed automatically when installing the package.

### User Environment Setup

The package includes a post-installation script that:
- Creates the user's application directory (`~/.local/share/cattywampus/`)
- Copies the configuration template if no config exists
- Creates an empty log file
- Sets proper permissions

This happens automatically for all users with home directories when the package is installed.

### Standard Installation Layout

The package installs files in standard Debian locations:
- **Binary**: `/usr/bin/cattywampus` (available in PATH)
- **Config template**: `/usr/share/cattywampus/config.example.toml`
- **Documentation**: `/usr/share/doc/cattywampus/`

## Package Management

### Upgrade

Upgrading to a newer version:

```bash
sudo dpkg -i ../cattywampus_1.2.0-1_all.deb
```

### Removal

Remove the package while preserving user configuration:

```bash
sudo apt-get remove cattywampus
```

User configuration files in `~/.local/share/cattywampus/` are preserved during removal.

### Complete Removal

To remove everything including user data:

```bash
sudo apt-get purge cattywampus
# Then manually remove user directories if desired
```

## Technical Details

### Package Structure

The Debian packaging uses:
- `debian/control`: Package metadata and dependencies
- `debian/rules`: Build rules using `dh_python3`
- `debian/postinst`: Post-installation user setup
- `debian/changelog`: Version history
- `setup.py`: Standard Python packaging for the application

### Template System Integration

The packaging integrates with the existing template system:
- `templates/debian/control.template`: Generates package metadata
- `templates/debian/changelog.template`: Generates version history

Templates use the same variable substitution system as other project templates.

### Building Without PyInstaller

Unlike the existing build system that uses PyInstaller to create standalone binaries, the Debian package uses standard Python installation methods. This provides better integration with the system's Python environment and dependency management.

## Future Plans

- **PPA Publishing**: After testing, investigate publishing to a Ubuntu PPA (Personal Package Archive) for easier installation
- **Multiple Architectures**: Currently builds `all` architecture packages; could be extended for architecture-specific builds if needed
- **Integration Packages**: Could create separate packages for file manager integrations

## Development Notes

The Debian packaging is designed to eventually replace the current custom build/install/uninstall workflow with standard Debian package management practices. This provides:

- Better dependency management
- Standard installation/removal procedures  
- Integration with system package managers
- Automatic updates through apt repositories (when published to PPA)

## Testing

The packaging has been tested for:
- ✅ Template processing and file generation
- ✅ Basic package structure validation
- ✅ Script syntax checking
- ⏳ Full package build (requires `debuild`)
- ⏳ Installation testing (requires built package)

To test on a Debian/Ubuntu system with `debuild` installed, run `./build-app --deb` and install the resulting package.