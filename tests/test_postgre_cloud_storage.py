# tests/test_postgres_cloud_storage.py
"""
Integration tests against a real Postgres (Supabase) database.

Skips the entire module if required env vars are missing
or the Postgres driver isn't installed.

Covers:
- starting a session
- preventing double starts
- stopping a session (+ activities recorded)
- listing projects (deterministic order)
- exporting to CSV with a valid duration column
- messaging for 'stop without start'
"""

from __future__ import annotations
from pathlib import Path
import os
import pandas as pd
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session
import re

from PostgreCloudStorage import PostgreCloudStorage
from SQLiteLocalStorage import ProjectSession

# ---- Module-level guards: skip if Postgres isn't configured ----

from dotenv import load_dotenv

load_dotenv()  # load .env into process for the test's env checks

# You have to have a separate project in supaabase for tests!
# Otherwise the test destroy your daatabase
REQUIRED_ENVS = [
    "TEST_POSTGRES_USER",
    "TEST_POSTGRES_PASSWORD",
    "TEST_POSTGRES_HOST",
    "TEST_POSTGRES_PORT",
    "TEST_POSTGRES_DBNAME",
]

# ensure driver present (prefer psycopg v3)
try:
    import psycopg  # type: ignore  # noqa: F401

    _driver_ok = True
except Exception:
    try:
        import psycopg2  # type: ignore  # noqa: F401

        _driver_ok = True
    except Exception:
        _driver_ok = False

if not _driver_ok:
    pytest.skip(
        "No Postgres driver (psycopg or psycopg2) installed; skipping Postgres tests",
        allow_module_level=True,
    )

if not all(os.getenv(k) for k in REQUIRED_ENVS):
    pytest.skip(
        "Postgres env vars missing; set POSTGRES_* to run Postgres tests",
        allow_module_level=True,
    )


# ---- Fixtures ----


@pytest.fixture(scope="module")
def storage() -> PostgreCloudStorage:
    """
    One storage for the module. Uses env-based connection (db_url=None).
    """
    # Do not leave db_url empty: it WILL ruin your prod database
    st = PostgreCloudStorage(db_url="test", echo=False)
    return st


@pytest.fixture(autouse=True)
def _clean_table_between_tests(storage: PostgreCloudStorage):
    """
    Ensure a clean slate before and after each test.
    """
    with storage.engine.begin() as conn:
        conn.execute(text("DELETE FROM project_sessions"))
    yield
    with storage.engine.begin() as conn:
        conn.execute(text("DELETE FROM project_sessions"))


# ---- Helpers ----


def _duration_seconds(series: pd.Series) -> pd.Series:
    """
    Normalize a 'duration' column to integer seconds regardless of type:
    - int/float: return as int64
    - string/timedelta: convert via to_timedelta(...)
    """
    if pd.api.types.is_numeric_dtype(series):
        return series.astype("int64")
    td = pd.to_timedelta(series, errors="coerce")
    if td.notna().all():
        return td.dt.total_seconds().astype("int64")
    # fallback if mixed
    return pd.to_numeric(series, errors="coerce").fillna(0).astype("int64")


# ---- Tests ----


def test_start_and_stop_creates_row_and_duration_nonnegative(
    storage: PostgreCloudStorage,
):
    storage.start_working("testi")
    storage.stop_working("testi", "coding")

    # Verify row via ORM
    with Session(storage.engine) as s:
        rows = (
            s.execute(select(ProjectSession).where(ProjectSession.proj_name == "testi"))
            .scalars()
            .all()
        )

    assert len(rows) == 1
    row = rows[0]
    assert row.end_time is not None
    assert row.activities == "coding"
    assert (row.end_time - row.start_time).total_seconds() >= 0


def test_prevent_double_start(
    storage: PostgreCloudStorage, capsys: pytest.CaptureFixture[str]
):
    storage.start_working("dup")
    storage.start_working("dup")  # should warn and NOT create a 2nd open session

    out = capsys.readouterr().out
    assert "Started working on the project: dup." in out
    assert "There is already an ongoing session" in out

    # Ensure only one open session exists
    with storage.engine.connect() as conn:
        open_rows = (
            conn.execute(
                select(ProjectSession).where(
                    ProjectSession.proj_name == "dup",
                    ProjectSession.end_time.is_(None),
                )
            )
            .scalars()
            .all()
        )

    assert len(open_rows) == 1

    # Clean up by stopping
    storage.stop_working("dup", "done")
    with storage.engine.connect() as conn:
        open_after_stop = (
            conn.execute(
                select(ProjectSession).where(
                    ProjectSession.proj_name == "dup",
                    ProjectSession.end_time.is_(None),
                )
            )
            .scalars()
            .all()
        )
    assert len(open_after_stop) == 0


def test_stop_without_start_messages(
    storage: PostgreCloudStorage, capsys: pytest.CaptureFixture[str]
):
    storage.stop_working("nope", "x")
    out = capsys.readouterr().out
    assert "No ongoing session to stop" in out


def test_list_projects_sorted_unique(
    storage: PostgreCloudStorage, capsys: pytest.CaptureFixture[str]
):
    # Create two finished projects in non-sorted order
    storage.start_working("B")
    storage.stop_working("B", "done")
    storage.start_working("A")
    storage.stop_working("A", "done")

    storage.list_projects()
    out = capsys.readouterr().out

    # Simple ordering check
    assert "Tracked projects" in out
    # Normalize lines and extract the printed names after "N: "
    lines = out.splitlines()
    names = []
    for ln in lines:
        m = re.match(r"^\s*\d+:\s+(.*)$", ln)
        if m:
            names.append(m.group(1).strip())
    assert names == ["A", "B"]


def test_write_project_to_csv_creates_file_with_duration(
    storage: PostgreCloudStorage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    # Change CWD so CSV is written to tmp_path (your method writes to CWD)
    monkeypatch.chdir(tmp_path)

    storage.start_working("csvproj")
    storage.stop_working("csvproj", "export")

    storage.write_project_to_csv("csvproj")

    csv_file = tmp_path / "csvproj_time_tracker.csv"
    assert csv_file.exists()

    # Validate content
    df = pd.read_csv(csv_file, parse_dates=["start_time", "end_time"])
    assert {"proj_name", "start_time", "end_time", "activities", "duration"}.issubset(
        df.columns
    )

    secs = _duration_seconds(df["duration"])
    assert (secs >= 0).all()
    assert (df["proj_name"] == "csvproj").all()
