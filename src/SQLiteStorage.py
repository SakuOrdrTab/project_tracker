'''A Centralized Sqlite3 storage for multiple projects'''

import os
import sys

import sqlite3
import pandas as pd

class SQLiteStorage():
    """Has the functionality and storage means for tracking project's time consumption. Implemented with SQLite
    """    
    def __init__(self) -> None:
        """Constructs a Storage object
        """        
        self._db_path = os.path.join('.', 'proj_ttrack.db')
        # Create a new database if needed
        if not os.path.exists(self._db_path): 
            self.initialize_database()
    
    def initialize_database(self) -> None:
        """Initializes a new Sqlite3 database if no prior exists
        """        
        try:
            with sqlite3.connect(self._db_path) as db:
                db.execute('''CREATE TABLE project_time_tracking 
                                (id INTEGER PRIMARY KEY, proj_name TEXT, start_time TEXT, end_time TEXT, activities TEXT)''')
        except Exception as e:
            print(f"Could not initialize database {self._db_path} ({e}), exiting...")
            sys.exit(1)

    def start_working(self, proj_name: str) -> None:
        """A Start time is marked in the database
        """        
        try:
            with sqlite3.connect(self._db_path) as db:
                # Check if there is already an ongoing session
                if db.execute(f"SELECT id FROM project_time_tracking WHERE end_time IS NULL AND proj_name = ?",
                               (proj_name,)).fetchone():
                    print("There is already an ongoing session. Please stop the current session before starting a new one.")
                    return
                
                # If no ongoing session, start a new one
                db.execute("INSERT INTO project_time_tracking (proj_name, start_time) VALUES (?, datetime('now'))", (proj_name,))
        except Exception as e:
            print(f"Could not insert into databse {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print(f"Started working on the project: {proj_name}.")

    def stop_working(self, proj_name: str, activities: str) -> None:
        """A Stopping time is marked in the database together with a description of spent time usage.

        Args:
            proj_name (str): project's name
            activities (str): description of time spent
        """        
        try:
            with sqlite3.connect(self._db_path) as db:

                # Check for the ID of the MOST RECENT ongoing session
                ongoing_session = db.execute("""    
                    SELECT id FROM project_time_tracking 
                    WHERE end_time IS NULL AND proj_name = ?
                    ORDER BY start_time DESC LIMIT 1
                    """, (proj_name,)).fetchone()
                    
                if ongoing_session is None:
                    print("No ongoing session to stop. Please start a session first.")
                    return
                
                session_id = ongoing_session[0]
                
                # Update only the session with that specific ID.
                db.execute('''UPDATE project_time_tracking 
                               SET end_time = datetime('now'), activities = ? 
                               WHERE id = ?''', (activities, session_id,))
        except Exception as e:
            print(f"Could not update into databse {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print(f"Stopped working on the project: {proj_name} and recorded activities.")

    def write_project_to_csv(self, proj_name: str) -> None:
        """Writes project's time usage in a .csv file
        """        
        try:
            with sqlite3.connect(self._db_path) as db:
                query = "SELECT * FROM project_time_tracking WHERE proj_name = ?;"
                df = pd.read_sql_query(query, db, params=(proj_name,))
        except Exception as e:
            print(f"Could not read from database {self._db_path} ({e}), exiting...")
            sys.exit(1)
        
        df['start_time'] = pd.to_datetime(df['start_time'])
        df['end_time'] = pd.to_datetime(df['end_time'])

        df['duration'] = df['end_time'] - df['start_time']
        if df.shape[0] < 100: # Don't print million rows to screen
            print(df) 
        df.to_csv(f"{proj_name}_time_tracker.csv")

    def list_projects(self) -> None:
        """Lists all projects being tracked
        """        
        try:
            with sqlite3.connect(self._db_path) as db:
                query = "SELECT DISTINCT proj_name FROM project_time_tracking;"
                table = db.execute(query).fetchall()
        except Exception as e:
            print(f"Could not read from database {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print('Projects tracked:')
        for row in table:
            print(row[0])