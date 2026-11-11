# tests/test_cli_functionality.py

import sys
import pytest
from unittest.mock import MagicMock, patch

# Import the main script from the root folder, relying on 'pythonpath = . src' in pytest.ini
import proj_ttrack


# --- Custom Exception to Stop Execution Flow ---


class ExitCalled(Exception):
    """
    Custom exception raised by the mocked sys.exit().
    This is essential to halt the execution flow of the tested function (proj_ttrack.main())
    without actually killing the entire test process.
    The 'code' attribute holds the exit code passed to sys.exit().
    """

    def __init__(self, code):
        self.code = code
        super().__init__(f"sys.exit({code}) called")


# --- Fixtures and Mocks ---


@pytest.fixture(autouse=True)
def mock_storage(monkeypatch):
    """
    Mocks the PostgreCloudStorage class and its resulting instance.
    This prevents the CLI logic from attempting a real database connection.
    We patch the class definition itself within the proj_ttrack module.
    """
    # CLI unit tests must never depend on local production credentials.
    monkeypatch.setenv("POSTGRES_URL", "")
    # Create a mock instance with all storage methods mocked
    mock_instance = MagicMock()

    # Patch the PostgreCloudStorage class to return our mock instance upon instantiation
    with patch("proj_ttrack.PostgreCloudStorage", return_value=mock_instance):
        yield mock_instance


@pytest.fixture(autouse=True)
def mock_sys_exit():
    """
    Mocks sys.exit() to raise the ExitCalled exception instead of terminating.
    The 'autouse=True' ensures this mock is applied to every test function.
    The 'side_effect' makes the mock raise our custom exception with the exit code,
    immediately stopping the program flow within the tested function.
    """
    def raise_exit(code=0):
        raise ExitCalled(code)

    with patch("sys.exit", side_effect=raise_exit) as mock_exit:
        yield mock_exit


# --- Helper Function ---


def run_main_with_args(args: list[str]):
    """
    Helper to set sys.argv and call proj_ttrack.main().
    sys.argv[0] must always be the script name.
    """
    with patch.object(sys, "argv", ["proj_ttrack.py"] + args):
        proj_ttrack.main()


# --- Tests ---

## ✅ Basic Behavior (Help and Missing Args)


def test_no_arguments_prints_help(capsys, mock_storage):
    """No arguments prints help and exits before initializing storage."""
    with pytest.raises(ExitCalled) as exc_info:
        run_main_with_args([])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage: proj_ttrack.py" in captured.out
    assert "options:" in captured.out
    assert "Please provide a project name" not in captured.out
    proj_ttrack.PostgreCloudStorage.assert_not_called()


def test_missing_projectname_for_required_tasks_exits(capsys, mock_storage):
    """A missing required project name exits before initializing storage."""
    with pytest.raises(ExitCalled) as exc_info:
        run_main_with_args(["--start"])

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Please provide a project name as the first argument." in captured.out
    proj_ttrack.PostgreCloudStorage.assert_not_called()
    mock_storage.start_working.assert_not_called()


def test_list_does_not_require_projectname(mock_storage):
    """--list uses mocked storage without requiring a project name."""
    run_main_with_args(["--list"])
    mock_storage.list_projects.assert_called_once()


## 🚀 Start/Stop Logic


def test_start_working_calls_storage_method(mock_storage):
    """Test --start calls storage.start_working with the correct project name."""
    run_main_with_args(["MyProj", "--start"])

    mock_storage.start_working.assert_called_once_with(proj_name="MyProj")
    mock_storage.stop_working.assert_not_called()


def test_stop_with_explicit_description(mock_storage):
    """Test --stop with a description provided via CLI."""
    # Mock the check for an ongoing session to return True
    mock_storage.ongoing_session_exists.return_value = True

    run_main_with_args(["CoolProj", "--stop", "Finished", "the", "feature"])
    mock_storage.ongoing_session_exists.assert_called_once_with("CoolProj")
    mock_storage.stop_working.assert_called_once_with(
        proj_name="CoolProj", activities="Finished the feature"
    )


def test_stop_prompts_for_description_if_none_provided(mock_storage, monkeypatch):
    """Test --stop with no CLI description prompts the user for input."""
    # Mock ongoing session check
    mock_storage.ongoing_session_exists.return_value = True

    # Mock the built-in input() function to return a predefined string
    monkeypatch.setattr("builtins.input", lambda prompt: "User typed activity")

    # Pass --stop with no following arguments (args.stop will be [] in argparse)
    run_main_with_args(["PromptProj", "--stop"])

    mock_storage.stop_working.assert_called_once_with(
        proj_name="PromptProj", activities="User typed activity"
    )


def test_stop_with_no_ongoing_session_prints_message(mock_storage, capsys):
    """Test stopping a project with no ongoing session prints a warning and does nothing."""
    # Mock the check for an ongoing session to return False
    mock_storage.ongoing_session_exists.return_value = False

    run_main_with_args(["NoSessionProj", "--stop"])

    # Check for the warning message
    captured = capsys.readouterr()
    assert "No ongoing session in project NoSessionProj, exiting.." in captured.out

    # Ensure stop_working was NOT called
    mock_storage.ongoing_session_exists.assert_called_once_with("NoSessionProj")
    mock_storage.stop_working.assert_not_called()


## 📊 Reporting and Utility Tasks


def test_list_projects_task(mock_storage):
    """Test --list calls storage.list_projects()."""
    run_main_with_args(["--list"])
    mock_storage.list_projects.assert_called_once()
    mock_storage.print_project.assert_not_called()


def test_print_task(mock_storage):
    """Test --print calls storage.print_project() with the correct name."""
    run_main_with_args(["PrintProj", "--print"])
    mock_storage.print_project.assert_called_once_with(proj_name="PrintProj")
    mock_storage.write_project_to_csv.assert_not_called()


def test_export_task(mock_storage):
    """Test --export calls storage.write_project_to_csv() with the correct name."""
    run_main_with_args(["ExportProj", "--export"])
    mock_storage.write_project_to_csv.assert_called_once_with(proj_name="ExportProj")
    mock_storage.print_project.assert_not_called()


## 🔨 Installer Task


def test_install_task_calls_installer_function(mock_storage):
    """Test --install calls install_bats_to_cwd and exits early."""
    # Patch the installer function globally within the proj_ttrack module
    with patch("proj_ttrack.install_bats_to_cwd") as mock_install:
        run_main_with_args(["--install"])

        # Installer should be called
        mock_install.assert_called_once()

        proj_ttrack.PostgreCloudStorage.assert_not_called()
