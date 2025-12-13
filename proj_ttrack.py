import sys
import argparse

# from src.SQLiteLocalStorage import SQLiteLocalStorage
from src.PostgreCloudStorage import PostgreCloudStorage
from src.installer import install_bats_to_cwd

# TODO:
# - more tests needed?


def _add_argument_with_backward_compat(
    arg_parser: argparse.ArgumentParser, name: str, **kwargs
) -> None:
    """Helper function to add an argument with both double-hyphen and single-hyphen versions.
    
    Adds the modern double-hyphen version with full help text, and the legacy
    single-hyphen version with suppressed help for backward compatibility.
    
    Args:
        arg_parser: The ArgumentParser to add arguments to
        name: The argument name (without hyphens, e.g., 'start', 'stop')
        **kwargs: Additional keyword arguments to pass to add_argument
    """
    # Validate that name doesn't contain hyphens
    if "-" in name:
        raise ValueError(f"Argument name should not contain hyphens: {name}")
    
    # Add the modern double-hyphen version with provided kwargs
    arg_parser.add_argument(f"--{name}", **kwargs)
    
    # Add the legacy single-hyphen version with suppressed help
    arg_parser.add_argument(f"-{name}", **{**kwargs, "help": argparse.SUPPRESS})


def add_arguments(arg_parser: argparse.ArgumentParser) -> None:
    """Mutates arg_parser to have the app's different arguments.

    Args:
        arg_parser (argparse.ArgumentParser): arg_parser to be defined
    """
    # Positional argument: project name
    arg_parser.add_argument(
        "projectname",
        nargs="?",  # Zero or one argument
        default=None,
        help="The name of the project is needed as the first argument.",
    )
    # Optional argument: start working on a project
    _add_argument_with_backward_compat(
        arg_parser, "start", action="store_true", help="Start a working period"
    )
    # Optional argument: stop working on a project
    _add_argument_with_backward_compat(
        arg_parser,
        "stop",
        nargs="*",  # Zero or more arguments for description
        default=None,
        help="Stop a working period and provide a description (optional)",
    )
    # Optional argument: export project time usage to .csv
    _add_argument_with_backward_compat(
        arg_parser,
        "export",
        action="store_true",
        help="Write project time usage to .csv (current working directory)",
    )
    # Optional argument: print project time usage
    _add_argument_with_backward_compat(
        arg_parser,
        "print",
        action="store_true",
        help="Print project time usage",
    )
    # Optional argument: list all tracked projects
    _add_argument_with_backward_compat(
        arg_parser, "list", action="store_true", help="List all tracked projects"
    )
    # Install windows batch files to CWD, designed to be useful for each project
    _add_argument_with_backward_compat(
        arg_parser,
        "install",
        action="store_true",
        help="Install batch files for current working directory to start and stop a session",
    )


def handle_tasks(args: argparse.Namespace) -> None:
    """Handles all tasks defined by args; early return for those not requiring a storage
    which is not initialized

    Args:
        args (argparse.Namespace): CLI arguments
    """
    # early return not initializing storage if installing
    if args.install:
        install_bats_to_cwd()  # No storage init needed
        return

    handle_storage_tasks(args)


def handle_storage_tasks(args: argparse.Namespace) -> None:
    """Handles all tasks defined by args that require a storage which is initialized

    Args:
        args (argparse.Namespace): CLI arguments
    """
    # Postgres central storage
    storage = PostgreCloudStorage(profile="prod")
    # or storage = SQLLiteLocalStorage(profile="prod") if you prefer local SQLite

    # Check for non-project specific tasks first
    if args.list:
        storage.list_projects()
        return

    # project specific tasks
    if args.stop is not None:
        proj_to_stop = args.projectname
        # Only stop a session, if ongoing session for project exists
        if storage.ongoing_session_exists(proj_to_stop):
            description = (
                " ".join(args.stop)
                if args.stop
                # No description of time usage was provided in command line
                else input("What did you do in this session? ")
            )
            storage.stop_working(proj_name=args.projectname, activities=description)
        else:
            print(f"No ongoing session in project {proj_to_stop}, exiting..")
    elif args.start:
        storage.start_working(proj_name=args.projectname)
    elif args.print:
        storage.print_project(proj_name=args.projectname)
    elif args.export:
        storage.write_project_to_csv(proj_name=args.projectname)


def main() -> None:
    """Main program loop"""
    arg_parser = argparse.ArgumentParser(description="Track a project's working hours.")

    add_arguments(arg_parser=arg_parser)

    args = arg_parser.parse_args()

    # Check for print help condition
    if (
        args.projectname is None
        and args.stop is None
        and not args.start
        and not args.export
        and not args.print
        and not args.list
        and not args.install
    ):
        arg_parser.print_help()
        sys.exit(0)  # Exit after printing help

    # Check for missing project name when required
    if args.projectname is None and not args.list and not args.install:
        print("Please provide a project name as the first argument.")
        sys.exit(1)

    handle_tasks(args)


if __name__ == "__main__":
    main()
