#!/usr/bin/env bash
# Shell script launcher for proj_ttrack on Unix-like systems
# This script mirrors the functionality of proj_ttrack.cmd

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add src to PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH}"

# Run the Python script using the virtual environment's Python
"${SCRIPT_DIR}/.venv/bin/python" "${SCRIPT_DIR}/proj_ttrack.py" "$@"
