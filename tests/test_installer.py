# tests/test_installer.py
"""
Tests for installer.py

Covers:
- validation of project names (allowed and disallowed cases)
- interactive re-prompting until a valid name is provided
- creation of start_track and stop_track scripts in the current working directory
  (.bat files on Windows, .sh files on Unix-like systems)
- correct command contents inside the script files
- behavior when proj_ttrack is run from a different directory (scripts created there)
- printed installer messages including created file paths
- platform detection and appropriate file creation
"""

import builtins
import os
import platform
from unittest.mock import patch

import installer  # pyright: ignore[reportMissingImports]


def test_validate_proj_name_valid_cases():
    valid = [
        "proj",
        "proj_1",
        "proj-1",
        "proj.name",
        "a" * 20,
        "MyProject",  # uppercase should be fine
    ]
    for name in valid:
        assert installer.validate_proj_name(name), f"Expected valid: {name}"


def test_validate_proj_name_invalid_cases():
    invalid = [
        "",  # empty
        "  ",  # whitespace only
        "proj name",  # whitespace
        "proj\tname",  # tab
        "proj\nname",  # newline
        "foo/..",  # path manipulation (normalized != original)
        "proj/name",  # forward slash invalid on all platforms
    ]
    
    # Add platform-specific invalid characters
    if platform.system() == 'Windows':
        invalid.extend([
            "proj&name",  # cmd metachar
            "proj|name",
            "proj^name",
            "proj%name",
            "proj!name",
            "proj(name)",
            "proj[name]",
            "proj<name>",
            "proj>name",
            "proj\\name",  # path sep
            "proj:name",
            "foo\\..",  # path manipulation (Windows-style)
        ])
    
    for name in invalid:
        assert not installer.validate_proj_name(name), f"Expected invalid: {name}"


def test_install_bats_to_cwd_creates_files_and_contents(tmp_path, monkeypatch, capsys):
    """
    - Runs installer in a temporary CWD
    - Supplies a valid project name
    - Asserts the two script files are created (.bat on Windows, .sh on Unix)
    - Asserts they contain the expected commands
    """
    # Work in a clean temp directory
    monkeypatch.chdir(tmp_path)

    # Provide a valid project name in one shot
    monkeypatch.setattr(builtins, "input", lambda _: "my-project")

    installer.install_bats_to_cwd()

    # Determine expected file extension based on platform
    is_windows = platform.system() == 'Windows'
    script_ext = '.bat' if is_windows else '.sh'
    
    start_path = tmp_path / f"start_track{script_ext}"
    stop_path = tmp_path / f"stop_track{script_ext}"

    assert start_path.exists(), f"start_track{script_ext} was not created"
    assert stop_path.exists(), f"stop_track{script_ext} was not created"

    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")

    # Check for platform-specific content
    if is_windows:
        # Be robust to leading newlines / indentation in the template
        assert "proj_ttrack my-project -start" in start_text
        assert "proj_ttrack my-project -stop %*" in stop_text
    else:
        assert "proj_ttrack.sh my-project --start" in start_text
        assert 'proj_ttrack.sh my-project --stop "$@"' in stop_text
        # Verify shell scripts are executable
        assert os.access(start_path, os.X_OK), "start_track.sh should be executable"
        assert os.access(stop_path, os.X_OK), "stop_track.sh should be executable"

    # Optional: check printed success message mentions the created files
    captured = capsys.readouterr().out
    assert "Installer running..." in captured
    assert str(start_path) in captured
    assert str(stop_path) in captured


def test_install_bats_reprompts_until_valid(tmp_path, monkeypatch):
    """
    - Simulate user entering invalid names, then a valid one.
    - Verify files are created only after the valid name is provided.
    """
    monkeypatch.chdir(tmp_path)

    # Sequence: invalid (has space), invalid (metachar), valid
    inputs = iter(["bad name", "bad/name", "ok-name"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    installer.install_bats_to_cwd()

    # Determine expected file extension based on platform
    is_windows = platform.system() == 'Windows'
    script_ext = '.bat' if is_windows else '.sh'
    
    start_path = tmp_path / f"start_track{script_ext}"
    stop_path = tmp_path / f"stop_track{script_ext}"

    assert start_path.exists()
    assert stop_path.exists()

    # Contents reflect the final valid name
    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")
    
    if is_windows:
        assert "proj_ttrack ok-name -start" in start_text
        assert "proj_ttrack ok-name -stop %*" in stop_text
    else:
        assert "proj_ttrack.sh ok-name --start" in start_text
        assert 'proj_ttrack.sh ok-name --stop "$@"' in stop_text


def test_bats_are_created_in_current_working_directory(tmp_path, monkeypatch):
    """
    Verify that the script files are created in the *current working directory*
    even if proj_ttrack (and src/installer.py) are located elsewhere.
    """
    # Simulate running the command from a different directory
    project_dir = tmp_path / "my_fake_project"
    project_dir.mkdir()

    # Monkeypatch cwd to simulate running from that folder
    monkeypatch.chdir(project_dir)

    # Fake user input
    monkeypatch.setattr("builtins.input", lambda _: "remote-proj")

    installer.install_bats_to_cwd()

    # Determine expected file extension based on platform
    is_windows = platform.system() == 'Windows'
    script_ext = '.bat' if is_windows else '.sh'
    
    start_path = project_dir / f"start_track{script_ext}"
    stop_path = project_dir / f"stop_track{script_ext}"

    # Assertions: both scripts exist *here*, not anywhere else
    assert start_path.exists(), f"start_track{script_ext} should exist in the cwd"
    assert stop_path.exists(), f"stop_track{script_ext} should exist in the cwd"

    # Double-check contents reference the correct project name
    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")
    
    if is_windows:
        assert "proj_ttrack remote-proj -start" in start_text
        assert "proj_ttrack remote-proj -stop %*" in stop_text
    else:
        assert "proj_ttrack.sh remote-proj --start" in start_text
        assert 'proj_ttrack.sh remote-proj --stop "$@"' in stop_text


def test_platform_specific_scripts_windows(tmp_path, monkeypatch):
    """
    Test that Windows batch files are created when platform is Windows.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(builtins, "input", lambda _: "win-project")
    
    # Mock platform.system() to return 'Windows'
    with patch('installer.platform.system', return_value='Windows'):
        installer.install_bats_to_cwd()
    
    # Should create .bat files
    start_path = tmp_path / "start_track.bat"
    stop_path = tmp_path / "stop_track.bat"
    
    assert start_path.exists(), "start_track.bat should exist on Windows"
    assert stop_path.exists(), "stop_track.bat should exist on Windows"
    
    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")
    
    assert "proj_ttrack win-project -start" in start_text
    assert "proj_ttrack win-project -stop %*" in stop_text
    assert "@echo off" in start_text


def test_platform_specific_scripts_unix(tmp_path, monkeypatch):
    """
    Test that shell scripts are created when platform is Linux/Unix.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(builtins, "input", lambda _: "unix-project")
    
    # Mock platform.system() to return 'Linux'
    with patch('installer.platform.system', return_value='Linux'):
        installer.install_bats_to_cwd()
    
    # Should create .sh files
    start_path = tmp_path / "start_track.sh"
    stop_path = tmp_path / "stop_track.sh"
    
    assert start_path.exists(), "start_track.sh should exist on Linux"
    assert stop_path.exists(), "stop_track.sh should exist on Linux"
    
    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")
    
    assert "proj_ttrack.sh unix-project --start" in start_text
    assert 'proj_ttrack.sh unix-project --stop "$@"' in stop_text
    assert "#!/usr/bin/env bash" in start_text
    
    # Verify executability
    assert os.access(start_path, os.X_OK), "start_track.sh should be executable"
    assert os.access(stop_path, os.X_OK), "stop_track.sh should be executable"
