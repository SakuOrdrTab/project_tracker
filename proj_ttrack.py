import sqlite3
import os
import sys
import pandas as pd
import argparse

def initialize_database(db_path):
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute('''CREATE TABLE project_time_tracking 
                        (id INTEGER PRIMARY KEY, start_time TEXT, end_time TEXT, activities TEXT)''')
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Could not initialize databse {db_path} ({e}), exiting...")
        sys.exit(1)

def start_working(project_name):
    db_path = f'.\{project_name}_time_tracker.db'
    if not os.path.exists(db_path): 
        initialize_database(db_path)
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO project_time_tracking (start_time) VALUES (datetime('now'))")
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Could not insert into databse {db_path} ({e}), exiting...")
        sys.exit(1)
    print(f"Started working on the project: {project_name}.")

def stop_working(project_name, activities):
    db_path = f'.\{project_name}_time_tracker.db'
    try: 
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        cursor.execute('''UPDATE project_time_tracking 
                        SET end_time = datetime('now'), activities = ? 
                        WHERE id = (SELECT MAX(id) FROM project_time_tracking)''', (activities,))
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Could not update into databse {db_path} ({e}), exiting...")
        sys.exit(1)
    print(f"Stopped working on the project: {project_name} and recorded activities.")

def write_project_to_csv(project_name : str) -> None:
    db_path = f'.\{project_name}_time_tracker.db'
    try:
        db = sqlite3.connect(db_path)

        # Query to list all tables
        query = "SELECT * FROM project_time_tracking;"
        df = pd.read_sql_query(query, db)
    except Exception as e:
        print(f"Could not read from database {db_path} ({e}), exiting...")
        sys.exit(1)
    
    # Convert string timestamps to datetime objects
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])

    df['duration'] = df['end_time'] - df['start_time']
    print(df)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Track project's working hours.")
    arg_parser.add_argument('projectname', help="The name of the project is needed as the first argument.")
    arg_parser.add_argument('-start', action='store_true', help='Start a working period')
    arg_parser.add_argument('-stop', nargs='*', help='Stop a working period and provide a description (optional)')
    arg_parser.add_argument('-print', action='store_true', help='Write project time usage to .csv')

    args = arg_parser.parse_args()

    if args.stop:
        if not args.stop:  # no description provided
            description = input("What did you do in this session? ")
        else:
            description = " ".join(args.stop)
        stop_working(args.projectname, description)
    else:  
        if args.start:
            start_working(args.projectname)
        elif args.print:
            write_project_to_csv(args.projectname)
        else:  
            arg_parser.print_help() # no valid args, print help