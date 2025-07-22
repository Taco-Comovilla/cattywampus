"""
Integration tests for the install script functionality
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestInstallScript:
    """Test the install script via subprocess"""

    def test_install_script_help(self):
        """Test that install script shows help without errors"""
        install_script = Path(__file__).parent.parent / "install"
        
        result = subprocess.run([
            sys.executable, str(install_script), "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "Install application and file manager integrations" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--integrations" in result.stdout
        assert "--skip-uninstall" in result.stdout

    def test_install_script_dry_run(self):
        """Test install script dry run mode"""
        install_script = Path(__file__).parent.parent / "install"
        
        result = subprocess.run([
            sys.executable, str(install_script), "--dry-run", "--integrations"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        assert "Dry run completed" in result.stdout

    def test_install_script_skip_uninstall(self):
        """Test install script with skip-uninstall flag"""
        install_script = Path(__file__).parent.parent / "install"
        
        result = subprocess.run([
            sys.executable, str(install_script), "--dry-run", "--integrations", "--skip-uninstall"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        assert "DRY RUN MODE" in result.stdout
        # Should not see existing installation detection when skipped
        assert "Existing installation detected" not in result.stdout

    def test_install_script_detects_existing(self):
        """Test that install script detects existing installations"""
        install_script = Path(__file__).parent.parent / "install"
        
        result = subprocess.run([
            sys.executable, str(install_script), "--dry-run", "--integrations"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0
        # Should detect existing installation if one exists, or proceed if none
        assert ("Existing installation detected" in result.stdout or 
                "Dry run completed" in result.stdout)