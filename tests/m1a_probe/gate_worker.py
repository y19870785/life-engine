"""Synthetic cross-process shared gate held through a business transaction."""
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import time

from isolation import fixture_path


gate = fixture_path(Path(sys.argv[1]))
business = fixture_path(Path(sys.argv[2]))
ready = fixture_path(Path(sys.argv[3]))
release = fixture_path(Path(sys.argv[4]))
with closing(sqlite3.connect(gate, isolation_level=None, timeout=2)) as lock_db:
    lock_db.execute("BEGIN")
    lock_db.execute("SELECT epoch FROM gate").fetchone()  # SHARED lock in DELETE journal mode.
    with closing(sqlite3.connect(business, isolation_level=None, timeout=2)) as data_db:
        data_db.execute("BEGIN IMMEDIATE")
        data_db.execute("INSERT INTO business(value) VALUES('synthetic-write')")
        ready.write_text("held", encoding="ascii")
        deadline = time.monotonic() + 8
        while not release.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        if not release.exists():
            raise TimeoutError("release gate")
        data_db.execute("COMMIT")
    lock_db.execute("COMMIT")
