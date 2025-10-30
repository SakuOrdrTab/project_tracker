# tests/test_sqlite_storage.py
"""
Tests for SQLiteLocalStorage

Covers:
- starting a session
- preventing double starts
- stopping a session (+ activities recorded)
- listing projects (deterministic order)
- exporting to CSV with a valid duration column
- messaging for 'stop without start'
"""

from pathlib import Path
import pandas as pd
import pytest
from sqlalchemy import select

from SQLiteLocalStorage import SQLiteLocalStorage, ProjectSession


@pytest.fixture()
def db_url(tmp_path: Path) -> str:
    """Use a file-backed temp SQLite DB so multiple connections see the same data."""
    return f"sqlite:///{tmp_path/'test.db'}"


@pytest.fixture()
def storage(db_url: str) -> SQLiteLocalStorage:
    """Fresh storage for each test."""
    return SQLiteLocalStorage(db_url=db_url, echo=False)


def test_start_and_stop_creates_row_and_duration_nonnegative(storage: SQLiteLocalStorage):
    storage.start_working("testi")
    storage.stop_working("testi", "coding")

    # Inspect DB to ensure one row with end_time set and activities recorded.
    with storage.engine.connect() as conn:
        rows = conn.execute(
            select(ProjectSession.__table__).where(ProjectSession.proj_name == "testi")
        ).mappings().all()

    assert len(rows) == 1
    row = rows[0]
    assert row["end_time"] is not None
    assert row["activities"] == "coding"
    # duration >= 0 (sanity)
    assert (row["end_time"] - row["start_time"]).total_seconds() >= 0


def test_prevent_double_start(storage: SQLiteLocalStorage, capsys: pytest.CaptureFixture[str]):
    storage.start_working("dup")
    storage.start_working("dup")  # should print a warning and NOT create a 2nd open session

    out = capsys.readouterr().out
    assert "Started working on the project: dup." in out
    assert "There is already an ongoing session" in out

    # Ensure only one open session exists
    with storage.engine.connect() as conn:
        open_rows = conn.execute(
            select(ProjectSession.__table__).where(
                ProjectSession.proj_name == "dup",
                ProjectSession.end_time.is_(None),
            )
        ).mappings().all()

    assert len(open_rows) == 1

    # Clean up by stopping; should close the only open one
    storage.stop_working("dup", "done")
    with storage.engine.connect() as conn:
        open_after_stop = conn.execute(
            select(ProjectSession.__table__).where(
                ProjectSession.proj_name == "dup",
                ProjectSession.end_time.is_(None),
            )
        ).mappings().all()
    assert len(open_after_stop) == 0


def test_stop_without_start_messages(storage: SQLiteLocalStorage, capsys: pytest.CaptureFixture[str]):
    storage.stop_working("nope", "x")
    out = capsys.readouterr().out
    assert "No ongoing session to stop" in out


def test_list_projects_sorted_unique(storage: SQLiteLocalStorage, capsys: pytest.CaptureFixture[str]):
    # Create two finished projects in non-sorted order
    storage.start_working("B")
    storage.stop_working("B", "done")
    storage.start_working("A")
    storage.stop_working("A", "done")

    storage.list_projects()
    out = capsys.readouterr().out

    # Deterministic order (A then B) as your code uses order_by(proj_name)
    assert "Tracked projects" in out
    # Loose checks for lines like "1: A" and "2: B"
    assert "\n1: A" in out or "1: A\n" in out
    assert "\n2: B" in out or "2: B\n" in out


def test_write_project_to_csv_creates_file_with_duration(storage: SQLiteLocalStorage, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Change CWD so CSV is written to tmp_path (your method writes to CWD)
    monkeypatch.chdir(tmp_path)

    storage.start_working("csvproj")
    storage.stop_working("csvproj", "export")

    storage.write_project_to_csv("csvproj")

    csv_file = tmp_path / "csvproj_time_tracker.csv"
    assert csv_file.exists()

    # Validate content
    df = pd.read_csv(csv_file, parse_dates=["start_time", "end_time"])
    assert {"proj_name", "start_time", "end_time", "activities", "duration"}.issubset(df.columns)

    # All durations should be >= 0
    # Note: if 'duration' comes in as string, convert to Timedelta
    if df["duration"].dtype == object:
        df["duration"] = pd.to_timedelta(df["duration"])

    assert (df["duration"].dt.total_seconds() >= 0).all()
    assert (df["proj_name"] == "csvproj").all()
