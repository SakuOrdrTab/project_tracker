from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
import dotenv

from SQLiteLocalStorage import Base, ProjectSession, SQLiteLocalStorage

class PostgreCloudStorage(SQLiteLocalStorage):

    def __init__(self, db_url: str, echo: bool = False) -> None:
        # for dev
        echo = True

        # The db_url parameter is for testing, actual default is None, and then the cloud postgres is used
        if db_url is None:
            db_url = f"postgresql+supabase://{ 'your_user' }:{ 'your_password' }@{ 'your_project_ref' }.supabase.co:5432/{ 'your_database' }"

        try:
            self.engine = create_engine(db_url, echo=echo)
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            print(f"Could not connect to database {db_url} with SQLAlchemy ({e})")
            raise RuntimeError("Database connection error") from e
        except Exception as e:
            print(f"An unexpected error occurred ({e})")
            raise RuntimeError("Unexpected error during database initialization") from e
