"""A Centralized Sqlite3 storage for multiple projects"""

import os
# UTC Timezone is used globally for this module
from datetime import datetime, timezone

# import sqlite3
from sqlalchemy import (
    Integer,
    __version__,
    String,
    DateTime,
    Text,
    create_engine,
    select,
    bindparam,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd


# Base class for making ORM classes
class Base(DeclarativeBase):
    pass


# Schema for the project time tracking table
class ProjectSession(Base):
    __tablename__ = "project_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proj_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    activities: Mapped[str | None] = mapped_column(Text)


class SQLiteStorage:
    """Has the functionality and storage means for tracking project's time consumption. Implemented with SQLAlchemy and SQLite3."""

    def __init__(self) -> None:
        """Constructs a Storage object: SQLite3 local file database"""
        self._db_path = os.path.join(".", "proj_ttrack.db")
        self._db_url = f"sqlite:///{self._db_path}"

        self.engine = create_engine(self._db_url, echo=True)

        try:
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            print(
                f"Could not connect to database {self._db_path} with SQLAlchemy ({e}), exiting..."
            )
            raise RuntimeError('Database connection error') from e
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            raise RuntimeError('Unexpected error during database initialization') from e

    def start_working(self, proj_name: str) -> None:
        """A Start time is marked in the database"""
        try:
            with Session(self.engine) as db_session, db_session.begin():
                # Check if session is already running
                ongoing_session = (
                    db_session.execute(
                        select(ProjectSession)
                        .where(ProjectSession.proj_name == proj_name)
                        .where(ProjectSession.end_time.is_(None))
                    )
                    .scalars()
                    .first()
                )
                if ongoing_session:
                    print(
                        "There is already an ongoing session. Please stop the current session before starting a new one."
                    )
                    return
                
                new_session = ProjectSession(
                    proj_name=proj_name, start_time=datetime.now(timezone.utc)
                )
                db_session.add(new_session)
                print(f"Started working on the project: {proj_name}.")
        except SQLAlchemyError as e:
            print(f"Encountered DB error: {e}")
            raise RuntimeError('Database error starting project session') from e
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            raise RuntimeError('Unexpected error starting project session') from e

    def stop_working(self, proj_name: str, activities: str) -> None:
        """A Stopping time is marked in the database together with a description of spent time usage.

        Args:
            proj_name (str): project's name
            activities (str): description of time spent
        """
        try:
            with Session(self.engine) as db_session, db_session.begin():
                ongoing_session = (
                    db_session.execute(
                        select(ProjectSession)
                        .where(ProjectSession.proj_name == proj_name)
                        .where(ProjectSession.end_time.is_(None))
                        .order_by(ProjectSession.start_time.desc())
                    )
                    .scalars()
                    .first()
                )

                if ongoing_session is None:
                    print("No ongoing session to stop. Please start a session first.")
                    return

                ongoing_session.end_time = datetime.now(timezone.utc)
                ongoing_session.activities = activities

                print(
                    f"Stopped working on the project: {proj_name} and recorded activities."
                )
        except SQLAlchemyError as e:
            print(f"Encountered DB error: {e}")
            raise RuntimeError('Database error stopping project session') from e
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            raise RuntimeError('Unexpected error stopping project session') from e

    def write_project_to_csv(self, proj_name: str) -> None:
        """Writes project's time usage in a .csv file"""
        try: 
            # Select all entries ORM style
            stmt = select(ProjectSession.__table__).where(
                ProjectSession.proj_name == bindparam("pname")
            )

            # Pass projectname andquery to pandas read_sql
            with self.engine.connect() as conn:
                df = pd.read_sql(stmt, conn, params={"pname": proj_name})
        except SQLAlchemyError as e:
            print(f"Encountered DB error: {e}")
            raise RuntimeError('Database error writing project to CSV') from e
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            raise RuntimeError('Unexpected error writing project to CSV') from e

        if df.empty:
            print(f"No sessions found for project '{proj_name}'.")
            return

        # Safe, consistent dtypes
        df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
        df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")
        df["duration"] = df["end_time"] - df["start_time"]

        print(df)
        try:
            df.to_csv(f"{proj_name}_time_tracker.csv", index=False)
        except Exception as e:
            print(f"Could not write to .csv file ({e}), exiting...")
            raise RuntimeError('Error writing CSV file') from e

    def list_projects(self) -> None:
        """Lists all projects being tracked"""
        try:
            with Session(self.engine) as db_session, db_session.begin():
                project_names = db_session.execute(
                    select(ProjectSession.proj_name).distinct().order_by(ProjectSession.proj_name)
                ).scalars()
        except SQLAlchemyError as e:
            print(f"Encountered DB error: {e}")
            raise RuntimeError('Database error listing projects') from e
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            raise RuntimeError('Unexpected error listing projects') from e

        print("Tracked projects: ")
        for i, project in enumerate(project_names):
            print(f"{i + 1}: {project}")


if __name__ == "__main__":
    print(f"SQLAlchemy version:  {__version__}")
