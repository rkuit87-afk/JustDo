"""
Shared fixtures for the JustDo test suite.

Uses an in-memory SQLite database so tests are fast and isolated.
"""

import os
import sys
import sqlite3
import pytest

# Ensure the project root is on sys.path so imports work
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def _use_tmp_db(tmp_path, monkeypatch):
    """Point every test at a fresh temporary database file."""
    db_path = str(tmp_path / "test_mill.db")
    monkeypatch.setenv("MILL_DB_FILE", db_path)
    # Also patch the module-level constant so get_db() picks it up
    import database
    monkeypatch.setattr(database, "DB_FILE", db_path)
    yield db_path


@pytest.fixture
def db_conn(_use_tmp_db):
    """Return a connection to the temporary test database."""
    import database
    database.init_db()
    return database.get_db()


@pytest.fixture
def seeded_db(db_conn):
    """Return a database connection that has been seeded with initial data."""
    import database
    database.seed_data()
    return db_conn
