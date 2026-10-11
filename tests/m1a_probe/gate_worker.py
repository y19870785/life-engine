"""Synthetic cross-process shared gate held through a business transaction."""
from pathlib import Path
from contextlib import closing
import sqlite3
import sys
import time

from isolation import fixture_path
from primitive import connect, root_value


gate = fixture_path(Path(sys.argv[1]))
continuity = fixture_path(Path(sys.argv[2]))
business = fixture_path(Path(sys.argv[3]))
ready = fixture_path(Path(sys.argv[4]))
release = fixture_path(Path(sys.argv[5]))
with closing(sqlite3.connect(gate, isolation_level=None, timeout=2)) as lock_db:
    lock_db.execute("BEGIN")
    lock_db.execute("SELECT epoch FROM gate").fetchone()  # SHARED lock in DELETE journal mode.
    with connect(continuity) as authority:
        root = root_value(authority)
        if root is None or root["revision"] != 0 or root["retired"]:
            raise RuntimeError("BUSINESS_ROOT_RECHECK_DENIED")
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
