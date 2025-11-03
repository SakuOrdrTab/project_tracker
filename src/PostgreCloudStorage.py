"""A Centralized postgre database using supabase"""

import os
from dotenv import load_dotenv

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from SQLiteLocalStorage import Base, SQLiteLocalStorage


class PostgreCloudStorage(SQLiteLocalStorage):
    """Has the functionality and storage means for tracking project's time consumption.
    The data is in supabase cloud storage; as SQLAlchemy takes care of actual database
    interactions, only the initialization process is different - all else is inherited
    from the SQLiteLocalStorage class"""

    def __init__(self, db_url: str | None = None, echo: bool = False) -> None:
        load_dotenv()
        # The db_url parameter is for testing, actual default is None, and then the cloud postgres is used
        if db_url is None:  # PRODUCTION env vars
            user = os.environ.get("POSTGRES_USER")
            pwd = os.environ.get("POSTGRES_PASSWORD")
            host = os.environ.get("POSTGRES_HOST")
            port = os.environ.get("POSTGRES_PORT")  # host part
            db = os.environ.get("POSTGRES_DBNAME")
            # Default connections to supabase require ipV6
            # However, this connection string is especially for ipV4
            db_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
        else:  # TESTING
            try:
                user = os.environ.get("TEST_POSTGRES_USER")
                pwd = os.environ.get("TEST_POSTGRES_PASSWORD")
                host = os.environ.get("TEST_POSTGRES_HOST")
                port = os.environ.get("TEST_POSTGRES_PORT")  # host part
                db = os.environ.get("TEST_POSTGRES_DBNAME")
                db_url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
            except Exception as e:
                print(
                    "Exception occured while assigning TEST environment postgre/supabase variables."
                )
                raise RuntimeError("Environment loading error") from e

        try:
            self.engine = create_engine(
                db_url,
                echo=echo,
                pool_pre_ping=True,  # validates connections before use
                poolclass=NullPool,  # avoid holding idle connections, suggested by supabase
            )
            Base.metadata.create_all(self.engine)
        except SQLAlchemyError as e:
            print(f"Could not connect to database {db_url} with SQLAlchemy ({e})")
            raise RuntimeError("Database connection error") from e
        except Exception as e:
            print(f"An unexpected error occurred ({e})")
            raise RuntimeError("Unexpected error during database initialization") from e
