import sys
import argparse
# from dotenv import load_dotenv
# import os

# from src.SQLiteLocalStorage import SQLiteLocalStorage
from src.PostgreCloudStorage import PostgreCloudStorage
from src.installer import install_bats_to_cwd


def main() -> None:
    # Postgres central storage
    storage = PostgreCloudStorage(profile="prod")
    # or storage = SQLLiteLocalStorage(profile="prod") if you prefer local SQLite

    arg_parser = argparse.ArgumentParser(description="Track a project's working hours.")
    # Positional argument: project name
    arg_parser.add_argument(
        "projectname",
        nargs="?",  # Zero or one argument
        default=None,
        help="The name of the project is needed as the first argument.",
    )
    # Optional argument: start working on a project
    arg_parser.add_argument(
        "-start", action="store_true", help="Start a working period"
    )
    # Optional argument: stop working on a project
    arg_parser.add_argument(
        "-stop",
        nargs="*",  # Zero or more arguments for description
        default=None,
        help="Stop a working period and provide a description (optional)",
    )
    # Optional argument: print project time usage to .csv
    arg_parser.add_argument(
        "-export",
        action="store_true",
        help="Write project time usage to .csv (current working directory)",
    )
    # Optional argument: list all tracked projects
    arg_parser.add_argument(
        "-list", action="store_true", help="List all tracked projects"
    )
    # Install windows batch files to CWD, designed to be useful for each project
    arg_parser.add_argument(
        "-install",
        action="store_true",
        help="Install batch files for current working directory to start and stop a session",
    )

    args = arg_parser.parse_args()

    # Validate that project name is provided if not listing projects or installing
    if args.projectname is None and not args.list and not args.install:
        print("Please provide a project name as the first argument.")
        sys.exit(1)

    # Handle listing projects...
    if args.list:
        storage.list_projects()
    # ...or project specific tasks
    elif args.stop is not None:
        description = (
            " ".join(args.stop)
            if args.stop
            # No description of time usage was provided in command line
            else input("What did you do in this session? ")
        )
        storage.stop_working(proj_name=args.projectname, activities=description)
    elif args.start:
        storage.start_working(proj_name=args.projectname)
    elif args.export:
        storage.write_project_to_csv(proj_name=args.projectname)
    elif args.install:
        install_bats_to_cwd()
    else:
        arg_parser.print_help()  # No valid arguments, print help


if __name__ == "__main__":
    main()
