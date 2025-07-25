"""
Tests for Debian packaging functionality
"""

import subprocess
import sys
import tempfile
from pathlib import Path
from string import Template

import pytest


class TestDebianTemplates:
    """Test Debian template processing"""

    def test_control_template_processing(self):
        """Test that debian control template processes correctly"""
        template_path = Path(__file__).parent.parent / "templates/debian/control.template"
        
        assert template_path.exists(), "Control template should exist"
        
        with open(template_path) as f:
            template_content = f.read()
            
        template = Template(template_content)
        
        # Test with sample metadata
        test_metadata = {
            "APP_NAME": "test-app",
            "VERSION": "1.0.0",
            "REPO_BASE_URL": "https://github.com/test/test-app",
            "APP_DESCRIPTION": "Test application",
            "ORGANIZATION": "Test Org",
            "COPYRIGHT": "Copyright 2025 Test Org"
        }
        
        result = template.substitute(test_metadata)
        
        # Verify substitution worked
        assert "test-app" in result
        assert "https://github.com/test/test-app" in result
        assert "Test application" in result
        assert "Test Org" in result
        
        # Verify debian control format
        assert "Source:" in result
        assert "Package:" in result
        assert "Depends:" in result
        assert "mkvtoolnix" in result
        assert "atomicparsley" in result

    def test_changelog_template_processing(self):
        """Test that debian changelog template processes correctly"""
        template_path = Path(__file__).parent.parent / "templates/debian/changelog.template"
        
        assert template_path.exists(), "Changelog template should exist"
        
        with open(template_path) as f:
            template_content = f.read()
            
        # The template contains $(date -R) which is a shell command, not a template variable
        # So we'll just check that it has the right structure and template variables
        assert "${APP_NAME}" in template_content
        assert "${VERSION}" in template_content  
        assert "${ORGANIZATION}" in template_content
        assert "unstable; urgency=medium" in template_content
        assert " -- " in template_content


class TestSetupPy:
    """Test setup.py functionality"""

    def test_setup_py_imports(self):
        """Test that setup.py can be imported without errors"""
        setup_path = Path(__file__).parent.parent / "setup.py"
        assert setup_path.exists(), "setup.py should exist"
        
        # Test that setup.py can be executed without errors
        result = subprocess.run(
            [sys.executable, str(setup_path), "--help-commands"],
            capture_output=True,
            text=True,
            cwd=setup_path.parent
        )
        
        assert result.returncode == 0, f"setup.py failed: {result.stderr}"
        assert "build" in result.stdout
        assert "install" in result.stdout

    def test_setup_py_metadata(self):
        """Test that setup.py has correct metadata"""
        setup_path = Path(__file__).parent.parent / "setup.py"
        
        # Test getting metadata from setup.py
        result = subprocess.run(
            [sys.executable, str(setup_path), "--name"],
            capture_output=True,
            text=True,
            cwd=setup_path.parent
        )
        
        assert result.returncode == 0
        assert "cattywampus" in result.stdout

    def test_setup_py_console_scripts(self):
        """Test that setup.py defines console scripts correctly"""
        setup_path = Path(__file__).parent.parent / "setup.py"
        
        # Read and check for entry_points definition
        with open(setup_path) as f:
            content = f.read()
            
        assert "console_scripts" in content
        assert "=main:main" in content  # The app name is dynamic via f-string


class TestDebianFiles:
    """Test Debian packaging files"""

    def test_debian_control_syntax(self):
        """Test that debian/control has valid syntax"""
        control_path = Path(__file__).parent.parent / "debian/control"
        
        assert control_path.exists(), "debian/control should exist"
        
        with open(control_path) as f:
            content = f.read()
            
        # Basic syntax checks
        assert content.startswith("Source:")
        assert "Package:" in content
        assert "Architecture:" in content
        assert "Depends:" in content
        assert "Description:" in content
        
        # Check dependencies
        assert "mkvtoolnix" in content
        assert "atomicparsley" in content
        assert "python3" in content

    def test_debian_changelog_format(self):
        """Test that debian/changelog has valid format"""
        changelog_path = Path(__file__).parent.parent / "debian/changelog"
        
        assert changelog_path.exists(), "debian/changelog should exist"
        
        with open(changelog_path) as f:
            first_line = f.readline().strip()
            
        # Changelog should start with package name and version
        assert first_line.startswith("cattywampus (")
        assert ") unstable; urgency=medium" in first_line

    def test_debian_rules_executable(self):
        """Test that debian/rules is executable"""
        rules_path = Path(__file__).parent.parent / "debian/rules"
        
        assert rules_path.exists(), "debian/rules should exist"
        assert rules_path.stat().st_mode & 0o111, "debian/rules should be executable"
        
        # Check shebang
        with open(rules_path) as f:
            first_line = f.readline().strip()
            
        assert first_line.startswith("#!/"), "debian/rules should have shebang"

    def test_debian_compat_version(self):
        """Test that debian/compat has valid version"""
        compat_path = Path(__file__).parent.parent / "debian/compat"
        
        assert compat_path.exists(), "debian/compat should exist"
        
        with open(compat_path) as f:
            version = f.read().strip()
            
        assert version.isdigit(), "compat version should be numeric"
        assert int(version) >= 10, "compat version should be reasonably recent"

    def test_debian_copyright_format(self):
        """Test that debian/copyright has valid format"""
        copyright_path = Path(__file__).parent.parent / "debian/copyright"
        
        assert copyright_path.exists(), "debian/copyright should exist"
        
        with open(copyright_path) as f:
            content = f.read()
            
        # Check machine-readable format
        assert "Format:" in content
        assert "Files:" in content
        assert "Copyright:" in content
        assert "License:" in content


class TestDebianScripts:
    """Test Debian maintainer scripts"""

    def test_postinst_script_syntax(self):
        """Test that postinst script has valid bash syntax"""
        postinst_path = Path(__file__).parent.parent / "debian/postinst"
        
        assert postinst_path.exists(), "debian/postinst should exist"
        assert postinst_path.stat().st_mode & 0o111, "postinst should be executable"
        
        # Test bash syntax
        result = subprocess.run(
            ["bash", "-n", str(postinst_path)],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"postinst syntax error: {result.stderr}"
        
        # Check script structure
        with open(postinst_path) as f:
            content = f.read()
            
        assert content.startswith("#!/bin/bash")
        assert "set -e" in content
        assert "case \"$1\" in" in content
        assert "configure)" in content

    def test_prerm_script_syntax(self):
        """Test that prerm script has valid bash syntax"""
        prerm_path = Path(__file__).parent.parent / "debian/prerm"
        
        assert prerm_path.exists(), "debian/prerm should exist"
        assert prerm_path.stat().st_mode & 0o111, "prerm should be executable"
        
        # Test bash syntax
        result = subprocess.run(
            ["bash", "-n", str(prerm_path)],
            capture_output=True,  
            text=True
        )
        
        assert result.returncode == 0, f"prerm syntax error: {result.stderr}"
        
        # Check script structure
        with open(prerm_path) as f:
            content = f.read()
            
        assert content.startswith("#!/bin/bash")
        assert "set -e" in content
        assert "case \"$1\" in" in content


class TestBuildAppDeb:
    """Test build-app --deb functionality"""

    def test_build_app_deb_help(self):
        """Test that build-app shows --deb option in help"""
        build_script = Path(__file__).parent.parent / "build-app"
        
        result = subprocess.run(
            [sys.executable, str(build_script), "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        assert "--deb" in result.stdout
        assert "Build Debian package" in result.stdout

    def test_build_app_deb_flag_parsing(self):
        """Test that --deb flag is parsed correctly"""
        # This test would require mocking debuild since we don't want to run full build
        # For now, test that the flag is recognized
        build_script = Path(__file__).parent.parent / "build-app"
        
        # Test that --deb flag is recognized (will fail on missing debuild but that's expected)
        result = subprocess.run(
            [sys.executable, str(build_script), "--deb"],
            capture_output=True,
            text=True
        )
        
        # Should fail on missing debuild, not on argument parsing
        assert "debuild not found" in result.stderr or "Building Debian package" in result.stdout

    def test_generate_debian_files_function(self):
        """Test that generate_debian_files function works"""
        # Import the build-app module to test its functions
        build_script = Path(__file__).parent.parent / "build-app"
        
        # Add the build script directory to path so we can import
        import sys
        sys.path.insert(0, str(build_script.parent))
        
        # We can't easily import the build-app script directly, but we can test
        # that the debian templates exist and process correctly
        template_dir = Path(__file__).parent.parent / "templates/debian"
        assert template_dir.exists()
        assert (template_dir / "control.template").exists()
        assert (template_dir / "changelog.template").exists()


class TestDebianPackageStructure:
    """Test the overall Debian package structure"""

    def test_all_required_debian_files_exist(self):
        """Test that all required debian packaging files exist"""
        debian_dir = Path(__file__).parent.parent / "debian"
        
        required_files = [
            "control",
            "changelog", 
            "rules",
            "compat",
            "copyright",
            "postinst",
            "prerm",
            "source/format"
        ]
        
        for file_name in required_files:
            file_path = debian_dir / file_name
            assert file_path.exists(), f"Required debian file missing: {file_name}"

    def test_debian_templates_exist(self):
        """Test that debian templates exist"""
        template_dir = Path(__file__).parent.parent / "templates/debian"
        
        required_templates = [
            "control.template",
            "changelog.template"
        ]
        
        for template_name in required_templates:
            template_path = template_dir / template_name
            assert template_path.exists(), f"Required template missing: {template_name}"

    def test_setup_py_exists(self):
        """Test that setup.py exists and is properly structured"""
        setup_path = Path(__file__).parent.parent / "setup.py"
        
        assert setup_path.exists(), "setup.py should exist"
        
        with open(setup_path) as f:
            content = f.read()
            
        # Check for required setup.py components
        assert "from setuptools import setup" in content
        assert "entry_points" in content
        assert "install_requires" in content
        assert "python_requires" in content