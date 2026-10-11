"""Disposable SQLite model for probing M1-A primitives.

All identities and data here are synthetic. This module has no import from the
product runtime and provides no execution authority.
"""
from __future__ import annotations

import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path
import sqlite3
import sys
import time


def canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@contextmanager
def connect(path: Path):
    db = sqlite3.connect(path, timeout=2.0, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        journal = db.execute("PRAGMA journal_mode").fetchone()[0].upper()
        db.execute("PRAGMA synchronous=" + ("FULL" if journal == "WAL" else "EXTRA"))
        yield db
    finally:
        db.close()


def initialise(path: Path, mode: str) -> None:
    if mode not in ("WAL", "DELETE"):
        raise ValueError(mode)
    with connect(path) as db:
        actual = db.execute(f"PRAGMA journal_mode={mode}").fetchone()[0].upper()
        if actual != mode:
            raise RuntimeError(f"journal mode {actual} != {mode}")
        synchronous = "FULL" if mode == "WAL" else "EXTRA"
        db.execute(f"PRAGMA synchronous={synchronous}")
        db.executescript("""
            CREATE TABLE soul_root (
                domain TEXT NOT NULL, soul TEXT NOT NULL,
                revision INTEGER NOT NULL, value BLOB NOT NULL,
                PRIMARY KEY(domain, soul)
            );
            CREATE TABLE record (
                hash TEXT PRIMARY KEY, bytes BLOB NOT NULL,
                transition_id TEXT NOT NULL, payload_hash TEXT NOT NULL
            );
            CREATE UNIQUE INDEX record_transition ON record(transition_id);
        """)


def prepare(db: sqlite3.Connection, record: dict) -> str:
    raw = canonical(record)
    record_hash = digest(raw)
    transition_id = record["transition_id"]
    payload_hash = record["payload_hash"]
    db.execute("BEGIN IMMEDIATE")
    try:
        previous = db.execute(
            "SELECT hash, bytes, payload_hash FROM record WHERE transition_id=?",
            (transition_id,),
        ).fetchone()
        if previous is not None:
            if previous["hash"] != record_hash or previous["payload_hash"] != payload_hash:
                raise ValueError("TRANSITION_PAYLOAD_CONFLICT")
        else:
            db.execute(
                "INSERT INTO record(hash,bytes,transition_id,payload_hash) VALUES(?,?,?,?)",
                (record_hash, raw, transition_id, payload_hash),
            )
        db.execute("COMMIT")
    except BaseException:
        db.execute("ROLLBACK")
        raise
    return record_hash


def root_value(db: sqlite3.Connection, domain: str = "synthetic", soul: str = "S") -> dict | None:
    row = db.execute("SELECT revision,value FROM soul_root WHERE domain=? AND soul=?", (domain, soul)).fetchone()
    if row is None:
        return None
    value = json.loads(row["value"])
    if value["revision"] != row["revision"]:
        raise ValueError("ROOT_REVISION_MISMATCH")
    return value


def _valid_record(db: sqlite3.Connection, record_hash: str) -> dict:
    row = db.execute("SELECT bytes FROM record WHERE hash=?", (record_hash,)).fetchone()
    if row is None or digest(row[0]) != record_hash:
        raise ValueError("RECORD_MISSING_OR_CORRUPT")
    return json.loads(row[0])


def cas(db: sqlite3.Connection, *, operation: str, expected_revision: int | None,
        expected_source: str | None, target: str, record_hash: str,
        domain: str = "synthetic", soul: str = "S") -> str:
    """One write transaction checks all predicates against one SoulRoot row."""
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute(
            "SELECT revision,value FROM soul_root WHERE domain=? AND soul=?", (domain, soul)
        ).fetchone()
        root = json.loads(row["value"]) if row else None
        record = _valid_record(db, record_hash)
        okay = record["operation"] == operation and record["domain"] == domain and record["soul"] == soul
        okay &= record["expected_revision"] == expected_revision
        okay &= record["target"] == target
        okay &= record["expected_source"] == expected_source
        if operation in ("CREATE", "ENROLL"):
            okay &= row is None and expected_revision is None and target == "B0"
            okay &= record["parent_kind"] == ("GENESIS" if operation == "CREATE" else "ENROLL_BASELINE")
            okay &= record["parent_hash"] is None
            if okay:
                new = {"revision": 0, "retired": False, "active": "B0",
                       "branches": {"B0": {"record": record_hash, "generation": 0,
                                            "instance": record["instance"], "data": record["data"]}}}
                db.execute("INSERT INTO soul_root VALUES(?,?,?,?)", (domain, soul, 0, canonical(new)))
        elif operation == "FORK":
            okay &= row is not None and row["revision"] == expected_revision
            okay &= root is not None and not root["retired"]
            okay &= root is not None and target not in root["branches"]
            okay &= root is not None and root["branches"]["B0"]["record"] == expected_source
            okay &= record["parent_kind"] == "FORK" and record["parent_hash"] == expected_source
            okay &= root is not None and all(
                branch["instance"] != record["instance"] for branch in root["branches"].values()
            )
            if okay:
                root["revision"] += 1
                root["branches"][target] = {"record": record_hash, "generation": 0,
                                            "instance": record["instance"], "data": record["data"]}
                db.execute("UPDATE soul_root SET revision=?,value=? WHERE domain=? AND soul=? AND revision=?",
                           (root["revision"], canonical(root), domain, soul, expected_revision))
                okay &= db.execute("SELECT changes()").fetchone()[0] == 1
        elif operation == "RETIRE":
            okay &= row is not None and row["revision"] == expected_revision
            okay &= root is not None and not root["retired"]
            if okay:
                root["revision"] += 1
                root["retired"] = True
                root["retirement_record"] = record_hash
                db.execute("UPDATE soul_root SET revision=?,value=? WHERE domain=? AND soul=? AND revision=?",
                           (root["revision"], canonical(root), domain, soul, expected_revision))
        else:
            raise ValueError(operation)
        db.execute("COMMIT" if okay else "ROLLBACK")
        return "COMMITTED" if okay else "CAS_FAIL"
    except BaseException:
        if db.in_transaction:
            db.execute("ROLLBACK")
        raise


def record(operation: str, transition_id: str, *, expected_revision: int | None = None,
           expected_source: str | None = None, target: str = "B0",
           instance: str = "I0", data: str = "D0", parent_hash: str | None = None) -> dict:
    parent_kind = {"CREATE": "GENESIS", "ENROLL": "ENROLL_BASELINE", "FORK": "FORK", "RETIRE": "RETIRE"}[operation]
    item = {"protocol": 1, "domain": "synthetic", "soul": "S", "operation": operation,
            "transition_id": transition_id, "expected_revision": expected_revision,
            "expected_source": expected_source, "target": target, "instance": instance,
            "data": data, "parent_kind": parent_kind, "parent_hash": parent_hash}
    item["payload_hash"] = digest(canonical(item))
    return item


def classify(db: sqlite3.Connection, *, target: str = "B0", registry_data: str | None = None,
             known_version: bool = True) -> tuple[str, str, str, str]:
    """Synthetic four-axis read; authority is deliberately always DENIED."""
    try:
        root = root_value(db)
    except (ValueError, KeyError, TypeError):
        return "INDETERMINATE", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"
    if root is None or target not in root["branches"]:
        return "ABSENT", "UNKNOWN", "QUARANTINED(NO_BASELINE)", "DENIED"
    branch = root["branches"][target]
    try:
        item = _valid_record(db, branch["record"])
        if not known_version or item["protocol"] != 1 or item["data"] != branch["data"]:
            raise ValueError("MISSING_EVIDENCE")
        if item["operation"] == "FORK":
            _valid_record(db, item["parent_hash"])
    except (ValueError, KeyError, TypeError):
        return "INDETERMINATE", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"
    if root["retired"]:
        return "SOUL_RETIRED", "MISMATCH", "RETIRED", "DENIED"
    verdict = "FORK" if item["operation"] == "FORK" else "CONTINUATION"
    state = "READY" if registry_data == branch["data"] else "QUARANTINED(ACTIVATION_PENDING)"
    return "COMMITTED", verdict, state, "DENIED"


def worker(path: Path, mode: str, operation: str, transition_id: str,
           start: Path, ready: Path, result: Path) -> None:
    with connect(path) as db:
        if operation == "CREATE":
            item = record("CREATE", transition_id, instance=transition_id)
            expected = None
            source = None
            target = "B0"
        else:
            root = root_value(db)
            source = root["branches"]["B0"]["record"]
            expected = root["revision"]
            target = "B1"
            item = record("FORK", transition_id, expected_revision=expected,
                          expected_source=source, target=target, instance=transition_id, data=transition_id,
                          parent_hash=source)
        prepared = prepare(db, item)
        ready.write_text(json.dumps({"expected_revision": expected,
                                     "expected_source": source,
                                     "prepared_record": prepared}), encoding="utf-8")
        deadline = time.monotonic() + 8
        while not start.exists() and time.monotonic() < deadline:
            time.sleep(0.005)
        if not start.exists():
            raise TimeoutError("start gate")
        outcome = cas(db, operation=operation, expected_revision=expected,
                      expected_source=source, target=target, record_hash=prepared)
        result.write_text(json.dumps({"transition_id": transition_id, "outcome": outcome}), encoding="utf-8")


if __name__ == "__main__":
    worker(Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], Path(sys.argv[5]),
           Path(sys.argv[6]), Path(sys.argv[7]))
