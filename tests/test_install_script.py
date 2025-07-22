"""
Integration tests for the install script functionality
"""

import subprocess
import sys
from pathlib import Path


class TestInstallScript:
    """Test the install script via subprocess"""

    def test_install_script_help(self):
        """Test that install script shows help without errors"""
        install_script = Path(__file__).parent.parent / "install"

        result = subprocess.run(
            [sys.executable, str(install_script), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Install application and file manager integrations" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--integrations" in result.stdout
        assert "--skip-uninstall" in result.stdout
        assert "--force" in result.stdout or "-f" in result.stdout

    def test_install_script_dry_run(self):
        """Test install script dry run mode"""
        install_script = Path(__file__).parent.parent / "install"

        result = subprocess.run(
            [sys.executable, str(install_script), "--dry-run", "--integrations"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Dry run completed" in result.stdout

    def test_install_script_skip_uninstall(self):
        """Test install script with skip-uninstall flag"""
        install_script = Path(__file__).parent.parent / "install"

        result = subprocess.run(
            [
                sys.executable,
                str(install_script),
                "--dry-run",
                "--integrations",
                "--skip-uninstall",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        # Should not see existing installation detection when skipped
        assert "Existing installation detected" not in result.stdout

    def test_install_script_detects_existing(self):
        """Test that install script detects existing installations using uninstall script"""
        install_script = Path(__file__).parent.parent / "install"

        result = subprocess.run(
            [sys.executable, str(install_script), "--dry-run", "--integrations"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should detect existing installation if one exists, or proceed if none
        assert (
            "Existing installation detected" in result.stdout
            or "Dry run completed" in result.stdout
        )

        # If existing installation detected, should show details from uninstall script
        if "Existing installation detected" in result.stdout:
            assert (
                "Binary:" in result.stdout
                or "Integration:" in result.stdout
                or "Quick Action:" in result.stdout
            )

    def test_install_script_force_flag(self):
        """Test install script with --force flag"""
        install_script = Path(__file__).parent.parent / "install"

        result = subprocess.run(
            [
                sys.executable,
                str(install_script),
                "--dry-run",
                "--integrations",
                "--force",
            ],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        # Force flag should work in dry run mode

    def test_install_script_contains_config_warning_function(self):
        """Test that the install script contains the config preservation warning function"""
        install_script = Path(__file__).parent.parent / "install"

        # Read the install script content
        content = install_script.read_text()

        # Verify the function exists in the script
        assert "def check_and_warn_about_preserved_config" in content
        assert "Your personal configuration and settings were preserved" in content
        assert "Configuration folder:" in content
        assert "Configuration file:" in content
        assert "The new installation will use your existing settings" in content

    def test_install_script_calls_config_warning_after_uninstall(self):
        """Test that install script calls config warning function after successful uninstall"""
        install_script = Path(__file__).parent.parent / "install"

        # Read the install script content
        content = install_script.read_text()

        # Verify the function is called after successful uninstall
        assert "check_and_warn_about_preserved_config(app_name)" in content

        # Verify it's called in both success and warning code paths
        success_pattern = "Previous version uninstalled successfully"
        warning_pattern = "Uninstall completed with warnings"

        # Find both patterns and ensure the config warning call comes after each
        success_index = content.find(success_pattern)
        warning_index = content.find(warning_pattern)

        assert success_index != -1, "Success message not found"
        assert warning_index != -1, "Warning message not found"

        # Check that config warning function is called after success message
        success_section = content[success_index : success_index + 500]
        assert "check_and_warn_about_preserved_config" in success_section

        # Check that config warning function is called after warning message
        warning_section = content[warning_index : warning_index + 500]
        assert "check_and_warn_about_preserved_config" in warning_section

    def test_install_script_contains_checksum_functionality(self):
        """Test that install script contains checksum comparison functionality"""
        install_script = Path(__file__).parent.parent / "install"

        # Read the install script content
        content = install_script.read_text()

        # Verify checksum function exists
        assert "def calculate_file_checksum" in content
        assert "hashlib.sha256()" in content

        # Verify checksum comparison logic exists in both platforms
        assert "source_checksum = calculate_file_checksum" in content
        assert "target_checksum = calculate_file_checksum" in content
        assert "Checksums match. Skipping" in content
        assert "Checksums differ. Overwriting" in content
        assert "already up to date" in content
        assert "different version" in content

        # Should have the function in both Linux and macOS binary install functions
        assert content.count("source_checksum = calculate_file_checksum") >= 2

    def test_uninstall_script_contains_config_prompts(self):
        """Test that uninstall script contains proper config removal prompts"""
        uninstall_script = Path(__file__).parent.parent / "uninstall"

        # Read the uninstall script content
        content = uninstall_script.read_text()

        # Verify config removal prompting exists
        assert "def prompt_remove_app_folder" in content
        assert "personal configuration and logs" in content
        assert (
            "customized settings, preferences, and log history will be lost" in content
        )
        assert (
            "Choose 'N' (default) to keep your settings for future reinstallation"
            in content
        )
        assert "Remove application folder and all data? [y/N]" in content
        assert "The following personal files will be removed:" in content
        assert "Personal configuration:" in content

    def test_uninstall_script_preserve_config_option(self):
        """Test that uninstall script has --preserve-config option"""
        uninstall_script = Path(__file__).parent.parent / "uninstall"

        # Test that help includes the option
        result = subprocess.run(
            [sys.executable, str(uninstall_script), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--preserve-config" in result.stdout
        assert "Preserve user configuration and logs" in result.stdout

    def test_uninstall_script_preserve_config_dry_run(self):
        """Test uninstall script with --preserve-config in dry-run mode"""
        uninstall_script = Path(__file__).parent.parent / "uninstall"

        result = subprocess.run(
            [sys.executable, str(uninstall_script), "--dry-run", "--preserve-config"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Would preserve user configuration and logs" in result.stdout
        assert "preserve-config specified" in result.stdout
        # Should not show config removal prompts
        assert "The following personal files will be removed:" not in result.stdout

    def test_uninstall_script_preserve_config_conflicts(self):
        """Test that --preserve-config works with other flags"""
        uninstall_script = Path(__file__).parent.parent / "uninstall"

        # Test --preserve-config alone
        result = subprocess.run(
            [sys.executable, str(uninstall_script), "--dry-run", "--preserve-config"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Would preserve user configuration" in result.stdout

        # Test that --integrations still skips config (should not conflict)
        result = subprocess.run(
            [sys.executable, str(uninstall_script), "--dry-run", "--integrations"],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # With --integrations, should not mention config preservation at all
        assert "preserve" not in result.stdout.lower()
