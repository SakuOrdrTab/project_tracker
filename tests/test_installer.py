# tests/test_installer.py
"""
Tests for installer.py

Covers:
- validation of project names (allowed and disallowed cases)
- interactive re-prompting until a valid name is provided
- creation of start_track.bat and stop_track.bat in the current working directory
- correct command contents inside the .bat files
- behavior when proj_ttrack is run from a different directory (bats created there)
- printed installer messages including created file paths
"""

import builtins

import installer


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
        "proj/name",
        "proj:name",
        "foo/..",  # path manipulation (normalized != original)
        "foo\\..",  # path manipulation (Windows-style)
    ]
    for name in invalid:
        assert not installer.validate_proj_name(name), f"Expected invalid: {name}"


def test_install_bats_to_cwd_creates_files_and_contents(tmp_path, monkeypatch, capsys):
    """
    - Runs installer in a temporary CWD
    - Supplies a valid project name
    - Asserts the two .bat files are created
    - Asserts they contain the expected commands
    """
    # Work in a clean temp directory
    monkeypatch.chdir(tmp_path)

    # Provide a valid project name in one shot
    monkeypatch.setattr(builtins, "input", lambda _: "my-project")

    installer.install_bats_to_cwd()

    start_path = tmp_path / "start_track.bat"
    stop_path = tmp_path / "stop_track.bat"

    assert start_path.exists(), "start_track.bat was not created"
    assert stop_path.exists(), "stop_track.bat was not created"

    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")

    # Be robust to leading newlines / indentation in the template
    assert "proj_ttrack my-project -start" in start_text
    assert "proj_ttrack my-project -stop %*" in stop_text

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
    inputs = iter(["bad name", "bad&name", "ok-name"])
    monkeypatch.setattr(builtins, "input", lambda _: next(inputs))

    installer.install_bats_to_cwd()

    start_path = tmp_path / "start_track.bat"
    stop_path = tmp_path / "stop_track.bat"

    assert start_path.exists()
    assert stop_path.exists()

    # Contents reflect the final valid name
    assert "proj_ttrack ok-name -start" in start_path.read_text(encoding="utf-8")
    assert "proj_ttrack ok-name -stop %*" in stop_path.read_text(encoding="utf-8")


def test_bats_are_created_in_current_working_directory(tmp_path, monkeypatch):
    """
    Verify that the .bat files are created in the *current working directory*
    even if proj_ttrack (and src/installer.py) are located elsewhere.
    """
    # Simulate running the command from a different directory
    project_dir = tmp_path / "my_fake_project"
    project_dir.mkdir()

    # Monkeypatch cwd to simulate running from that folder
    monkeypatch.chdir(project_dir)

    # Fake user input
    monkeypatch.setattr("builtins.input", lambda _: "remote-proj")

    # Run the installer — it should write to the current working dir
    from installer import install_bats_to_cwd

    install_bats_to_cwd()

    start_path = project_dir / "start_track.bat"
    stop_path = project_dir / "stop_track.bat"

    # Assertions: both BATs exist *here*, not anywhere else
    assert start_path.exists(), "start_track.bat should exist in the cwd"
    assert stop_path.exists(), "stop_track.bat should exist in the cwd"

    # Double-check contents reference the correct project name
    start_text = start_path.read_text(encoding="utf-8")
    stop_text = stop_path.read_text(encoding="utf-8")
    assert "proj_ttrack remote-proj -start" in start_text
    assert "proj_ttrack remote-proj -stop %*" in stop_text
