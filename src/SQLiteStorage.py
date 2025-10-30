"""A Centralized Sqlite3 storage for multiple projects"""

import os
import sys
from datetime import datetime

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
    end_time: Mapped[datetime | None] = mapped_column(DateTime)
    activities: Mapped[str | None] = mapped_column(Text)


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
            print(
                f"Could not connect to database {self._db_path} with SQLAlchemy ({e}), exiting..."
            )
            self.session.close()
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred ({e}), exiting...")
            self.session.close()
            sys.exit(1)

    def start_working(self, proj_name: str) -> None:
        """A Start time is marked in the database"""
        with self.session.begin():
            # Check if session is already running
            ongoing_session = (
                self.session.execute(
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
            else:
                new_session = ProjectSession(
                    proj_name=proj_name, start_time=datetime.now()
                )
                self.session.add(new_session)
                print(f"Started working on the project: {proj_name}.")

    def stop_working(self, proj_name: str, activities: str) -> None:
        """A Stopping time is marked in the database together with a description of spent time usage.

        Args:
            proj_name (str): project's name
            activities (str): description of time spent
        """
        with self.session.begin():
            ongoing_session = (
                self.session.execute(
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

            ongoing_session.end_time = datetime.now()
            ongoing_session.activities = activities

            print(
                f"Stopped working on the project: {proj_name} and recorded activities."
            )

    def write_project_to_csv(self, proj_name: str) -> None:
        """Writes project's time usage in a .csv file"""
        # Select all entries ORM style
        stmt = select(ProjectSession.__table__).where(
            ProjectSession.proj_name == bindparam("pname")
        )

        # Pass projectname andquery to pandas read_sql
        with self.session.connection() as conn:
            df = pd.read_sql(stmt, conn, params={"pname": proj_name})

        if df.empty:
            print(f"No sessions found for project '{proj_name}'.")
            return

        # Safe, consistent dtypes
        df["start_time"] = pd.to_datetime(df["start_time"], errors="coerce")
        df["end_time"] = pd.to_datetime(df["end_time"], errors="coerce")
        df["duration"] = df["end_time"] - df["start_time"]

        print(df)
        df.to_csv(f"{proj_name}_time_tracker.csv")

    def list_projects(self) -> None:
        """Lists all projects being tracked"""
        project_names = self.session.execute(
            select(ProjectSession.proj_name).distinct()
        ).scalars()

        print("Tracked projects: ")
        for i, project in enumerate(project_names):
            print(f"{i + 1}: {project}")


if __name__ == "__main__":
    print(f"SQLAlchemy version:  {__version__}")
