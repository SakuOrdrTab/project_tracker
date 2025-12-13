"""Installer for platform-specific script files. Installer adds to current working directory two
script files (start_track and stop_track) that don't need any arguments and allow quick session
management in each project. Creates .bat files on Windows and .sh files on Unix-like systems."""

import os
import platform
from os import path, getcwd

# Illegal filename chars for different platforms
# Windows is more restrictive, so we use those as the base
ILLEGAL_CHARS_WINDOWS = set('<>:"/\\|?*&|^%!()[]{};=,~`')
# Unix/Linux mainly prohibits / and null
ILLEGAL_CHARS_UNIX = set('/\0')


def get_illegal_chars() -> set:
    """Get platform-specific illegal characters for filenames."""
    if platform.system() == 'Windows':
        return ILLEGAL_CHARS_WINDOWS
    else:
        return ILLEGAL_CHARS_UNIX


def validate_proj_name(name: str) -> bool:
    # Check for empty string and path manipulation attempts
    if not name or path.normpath(name) != name:
        return False

    if any(c.isspace() for c in name):
        return False

    illegal_chars = get_illegal_chars()
    if any(char in name for char in illegal_chars):
        return False

    return True


def install_bats_to_cwd() -> None:
    print("Installer running...")

    # Detect platform
    is_windows = platform.system() == 'Windows'
    script_ext = '.bat' if is_windows else '.sh'
    
    # Make sure that it is the CWD
    cwd = getcwd()
    start_path = path.join(cwd, f"start_track{script_ext}")
    stop_path = path.join(cwd, f"stop_track{script_ext}")

    proj_name = input("What is the name of your project: ")
    while True:
        if validate_proj_name(proj_name):
            break
        if is_windows:
            print("""Project name has to be compatible with Windows filenames in order to use batch files for
running the sessions. No whitespaces or certain special characters.
for 'my funny project' you can use 'my-funny-project' for example""")
        else:
            print("""Project name has to be compatible with filenames. No whitespaces or certain special characters.
for 'my funny project' you can use 'my-funny-project' for example""")
        proj_name = input("Please give a new name: ")

    if is_windows:
        # Create Windows batch files
        start_script = f"""@echo off
proj_ttrack {proj_name} -start
"""

        stop_script = f"""@echo off
proj_ttrack {proj_name} -stop %*
"""
    else:
        # Create Unix shell scripts
        start_script = f"""#!/usr/bin/env bash
proj_ttrack.sh {proj_name} --start
"""

        stop_script = f"""#!/usr/bin/env bash
proj_ttrack.sh {proj_name} --stop "$@"
"""

    with open(start_path, "w", encoding="utf-8") as file:
        file.write(start_script)

    with open(stop_path, "w", encoding="utf-8") as file:
        file.write(stop_script)

    # Make shell scripts executable on Unix-like systems
    if not is_windows:
        os.chmod(start_path, 0o755)
        os.chmod(stop_path, 0o755)

    print(f"Created {start_path} and {stop_path}.")

    return None
