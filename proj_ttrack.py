import sqlite3
import os
import sys
import pandas as pd
import argparse

class Storage():
    def __init__(self, project_name):
        self.project_name = project_name
        self._db_path = f'.\{project_name}_time_tracker.db'
        if not os.path.exists(self._db_path): 
            self.initialize_database()
    
    def initialize_database(self):
        try:
            with sqlite3.connect(self._db_path) as db:
                db.execute('''CREATE TABLE project_time_tracking 
                                (id INTEGER PRIMARY KEY, start_time TEXT, end_time TEXT, activities TEXT)''')
        except Exception as e:
            print(f"Could not initialize database {self._db_path} ({e}), exiting...")
            sys.exit(1)

    def start_working(self):
        try:
            with sqlite3.connect(self._db_path) as db:
                # Check if there is already an ongoing session
                if db.execute("SELECT id FROM project_time_tracking WHERE end_time IS NULL").fetchone():
                    print("There is already an ongoing session. Please stop the current session before starting a new one.")
                    return
                
                # If no ongoing session, start a new one
                db.execute("INSERT INTO project_time_tracking (start_time) VALUES (datetime('now'))")
        except Exception as e:
            print(f"Could not insert into databse {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print(f"Started working on the project: {self.project_name}.")

    def stop_working(self, activities):
        try:
            with sqlite3.connect(self._db_path) as db:

                # Check if there is an ongoing session
                ongoing_session = db.execute("SELECT id FROM project_time_tracking WHERE end_time IS NULL").fetchone()
                if ongoing_session is None:
                    print("No ongoing session to stop. Please start a session first.")
                    return
                
                # If there is an ongoing session, update it
                db.execute('''UPDATE project_time_tracking 
                                SET end_time = datetime('now'), activities = ? 
                                WHERE id = ?''', (activities, ongoing_session[0],))
        except Exception as e:
            print(f"Could not update into databse {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print(f"Stopped working on the project: {self.project_name} and recorded activities.")

    def write_project_to_csv(self) -> None:
        try:
            with sqlite3.connect(self._db_path) as db:
                # Query to list all tables
                query = "SELECT * FROM project_time_tracking;"
                df = pd.read_sql_query(query, db)
        except Exception as e:
            print(f"Could not read from database {self._db_path} ({e}), exiting...")
            sys.exit(1)
        
        # Convert string timestamps to datetime objects
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])

        df['duration'] = df['end_time'] - df['start_time']
        if df.shape[0] < 100: # Don't print million rows to screen
            print(df) 
        df.to_csv(f"{self.project_name}_time_tracker.csv")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Track a project's working hours.")
    arg_parser.add_argument('projectname', help="The name of the project is needed as the first argument.")
    arg_parser.add_argument('-start', action='store_true', help='Start a working period')
    arg_parser.add_argument('-stop', nargs='*', default=None, help='Stop a working period and provide a description (optional)')
    arg_parser.add_argument('-print', action='store_true', help='Write project time usage to .csv')

    args = arg_parser.parse_args()

    # If '-stop' was used, whether or not it has additional arguments
    if args.stop is not None:
        description = " ".join(args.stop) if args.stop else input("What did you do in this session? ")
        Storage(args.projectname).stop_working(description)
    elif args.start:
        Storage(args.projectname).start_working()
    elif args.print:
        Storage(args.projectname).write_project_to_csv()
    else:
        arg_parser.print_help()  # No valid arguments, print help