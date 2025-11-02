from pathlib import Path
import os
from dotenv import load_dotenv

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


from SQLiteLocalStorage import Base, ProjectSession, SQLiteLocalStorage

class PostgreCloudStorage(SQLiteLocalStorage):

    def __init__(self, db_url: str | None = None, echo: bool = False) -> None:
        # for dev
        echo = True

        # The db_url parameter is for testing, actual default is None, and then the cloud postgres is used
        if db_url is None:
            load_dotenv()
            user = os.environ.get("POSTGRES_USERNAME")
            pwd  = os.environ.get("POSTGRES_PASSWORD")
            ref  = os.environ.get("POSTGRES_REF")  # host part or project ref
            db   = os.environ.get("POSTGRES_DB")
            # Supabase works with standard Postgres; use psycopg v3 driver
            # Add sslmode=require for hosted instances
            db_url = f"postgresql+psycopg://{user}:{pwd}@{ref}.supabase.co:5432/{db}?sslmode=require"

        try:
            self.engine = create_engine(
                self.db_url,
                echo=echo,
                pool_pre_ping=True,   # validates connections before use
                poolclass=NullPool,   # avoid holding idle connections (good for serverless)
            )
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            print(f"Could not connect to database {db_url} with SQLAlchemy ({e})")
            raise RuntimeError("Database connection error") from e
        except Exception as e:
            print(f"An unexpected error occurred ({e})")
            raise RuntimeError("Unexpected error during database initialization") from e
