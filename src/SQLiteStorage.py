"""A Centralized Sqlite3 storage for multiple projects"""

import os
import sys
from datetime import datetime

import sqlite3
from sqlalchemy import Integer, __version__, String, DateTime, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

# Base class for making ORM classes
class Base(DeclarativeBase):
    pass

# Schema for the project time tracking table
class ProjectSession(Base):
    __tablename__ = "project_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proj_name: Mapped[str] = mapped_column(String)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime|None] = mapped_column(DateTime)
    activities: Mapped[str|None] = mapped_column(Text)


class SQLiteStorage:
    """Has the functionality and storage means for tracking project's time consumption. Implemented with SQLAlchemy and SQLite3."""

    def __init__(self) -> None:
        """Constructs a Storage object: SQLite3 local file database"""
        self._db_path = os.path.join(".", "proj_ttrack.db")
        self._db_url = f"sqlite:///{self._db_path}"

        self.engine = create_engine(self._db_url, echo=True)
        
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        try:
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            print(f"Could not connect to database {self._db_path} with SQLAlchemy ({e}), exiting...")
            self.session.close()
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            self.session.close()
            sys.exit(1)


    # def initialize_database(self) -> None:
    #     """Initializes a new Sqlite3 database if no prior exists"""
    #     try:
    #         with sqlite3.connect(self._db_path) as db:
    #             # Create the table for tracking project time usage
    #             db.execute("""CREATE TABLE project_time_tracking 
    #                             (id INTEGER PRIMARY KEY, proj_name TEXT, start_time TEXT, end_time TEXT, activities TEXT)""")
    #     except Exception as e:
    #         print(f"Could not initialize database {self._db_path} ({e}), exiting...")
    #         sys.exit(1)

    def start_working(self, proj_name: str) -> None:
        """A Start time is marked in the database"""
        try:
            with sqlite3.connect(self._db_path) as db:
                # Check if there is already an ongoing session
                if db.execute(
                    "SELECT id FROM project_time_tracking WHERE end_time IS NULL AND proj_name = ?",
                    (proj_name,),
                ).fetchone():
                    print(
                        "There is already an ongoing session. Please stop the current session before starting a new one."
                    )
                    return

                # If no ongoing session, start a new one
                db.execute(
                    "INSERT INTO project_time_tracking (proj_name, start_time) VALUES (?, datetime('now'))",
                    (proj_name,),
                )
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
                ongoing_session = db.execute(
                    """    
                    SELECT id FROM project_time_tracking 
                    WHERE end_time IS NULL AND proj_name = ?
                    ORDER BY start_time DESC LIMIT 1
                    """,
                    (proj_name,),
                ).fetchone()

                if ongoing_session is None:
                    print("No ongoing session to stop. Please start a session first.")
                    return

                session_id = ongoing_session[0]

                # Update only the session with that specific ID.
                db.execute(
                    """UPDATE project_time_tracking 
                               SET end_time = datetime('now'), activities = ? 
                               WHERE id = ?""",
                    (
                        activities,
                        session_id,
                    ),
                )
        except Exception as e:
            print(f"Could not update into databse {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print(f"Stopped working on the project: {proj_name} and recorded activities.")

    def write_project_to_csv(self, proj_name: str) -> None:
        """Writes project's time usage in a .csv file"""
        try:
            with sqlite3.connect(self._db_path) as db:
                # Select all rows for the given project
                query = "SELECT * FROM project_time_tracking WHERE proj_name = ?;"
                df = pd.read_sql_query(query, db, params=(proj_name,))
        except Exception as e:
            print(f"Could not read from database {self._db_path} ({e}), exiting...")
            sys.exit(1)

        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])

        df["duration"] = df["end_time"] - df["start_time"]
        if df.shape[0] < 100:  # Don't print million rows to screen
            print(df)
        df.to_csv(f"{proj_name}_time_tracker.csv")

    def list_projects(self) -> None:
        """Lists all projects being tracked"""
        try:
            with sqlite3.connect(self._db_path) as db:
                # Get all distinct project names from the DB
                query = "SELECT DISTINCT proj_name FROM project_time_tracking;"
                table = db.execute(query).fetchall()
        except Exception as e:
            print(f"Could not read from database {self._db_path} ({e}), exiting...")
            sys.exit(1)
        print("Projects tracked:")
        for row in table:
            print(row[0])


if __name__ == "__main__":
    print(f"SQLAlchemy version:  {__version__}")