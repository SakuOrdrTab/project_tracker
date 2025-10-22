import sqlite3
import os
import sys
import pandas as pd
import argparse

from src.SQLiteStorage import SQLiteStorage

if __name__ == "__main__":
    storage = SQLiteStorage()

    arg_parser = argparse.ArgumentParser(description="Track a project's working hours.")
    arg_parser.add_argument('projectname', nargs='?', default=None, help="The name of the project is needed as the first argument.")
    arg_parser.add_argument('-start', action='store_true', help='Start a working period')
    arg_parser.add_argument('-stop', nargs='*', default=None, help='Stop a working period and provide a description (optional)')
    arg_parser.add_argument('-print', action='store_true', help='Write project time usage to .csv')
    arg_parser.add_argument('-list', action='store_true', help='List all tracked projects') 

    args = arg_parser.parse_args()

    if args.projectname is None and not args.list:
        print("Please provide a project name as the first argument.")
        sys.exit(1)

    if args.list:
        storage.list_projects()
    elif args.stop is not None:
        description = " ".join(args.stop) if args.stop else input("What did you do in this session? ")
        storage.stop_working(proj_name=args.projectname, activities=description)
    elif args.start:
        storage.start_working(proj_name=args.projectname)
    elif args.print:
        storage.write_project_to_csv(proj_name=args.projectname)
    else:
        arg_parser.print_help()  # No valid arguments, print help