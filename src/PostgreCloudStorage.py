"""A Centralized postgre database using supabase"""

import os
from dotenv import load_dotenv
from typing import Literal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from SQLiteLocalStorage import Base, SQLiteLocalStorage


class PostgreCloudStorage(SQLiteLocalStorage):
    """Has the functionality and storage means for tracking project's time consumption.
    The data is in supabase cloud storage; as SQLAlchemy takes care of actual database
    interactions, only the initialization process is different - all else is inherited
    from the SQLiteLocalStorage class"""

    def __init__(
        self, profile: Literal["prod", "test"] = "test", echo: bool = False
    ) -> None:
        load_dotenv()
        env_key = "POSTGRES_URL" if profile == "prod" else "TEST_POSTGRES_URL"
        db_url = os.getenv(env_key, "").strip()

        if not db_url:
            raise RuntimeError(
                f"{env_key} is empty or missing. "
                f"Set it to your full Supabase URL, e.g. "
                f"postgresql+psycopg://user:pass@pooler-host:6543/db?sslmode=require"
            )

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
