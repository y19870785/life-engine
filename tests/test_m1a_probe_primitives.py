"""E0 checks for the disposable M1-A SQLite candidate, not product semantics."""
import hashlib
import json
import os
from contextlib import closing
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

PROBE = Path(__file__).parent / "m1a_probe"
sys.path.insert(0, str(PROBE))
from primitive import cas, classify, connect, initialise, prepare, record, root_value  # noqa: E402
from isolation import evidence_sink, fixture_path, register_fixture  # noqa: E402


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="m1a-synthetic-"))
        self.assertTrue(self.root.is_absolute())
        self.assertFalse(self.root.is_symlink())
        self.assertFalse(self.root.is_junction() if hasattr(self.root, "is_junction") else False)
        self.assertEqual(self.root.resolve(), self.root.absolute())
        self.assertNotIn(str(Path(__file__).resolve().parents[1]).lower(), str(self.root.resolve()).lower())
        register_fixture(self.root)
        requested_sink = os.environ.get("M1A_PROBE_EVIDENCE_ROOT")
        if requested_sink:
            self.evidence_root = evidence_sink(Path(requested_sink))
            self.evidence_grade = "COLLECTOR_REVIEWABLE"
        else:
            self.evidence_root = Path(tempfile.mkdtemp(prefix="m1a-evidence-transient-"))
            self.evidence_grade = "TRANSIENT_REGRESSION_ONLY"
            self.assertEqual(self.evidence_root.resolve(), self.evidence_root.absolute())
        self.paths = []
        self.observations = []

    def tearDown(self):
        if self.evidence_root:
            destination = self.evidence_root / self._testMethodName
            destination.mkdir(parents=True, exist_ok=True)
            manifest = {"test": self._testMethodName, "scratch_root": str(self.root),
                        "evidence_grade": self.evidence_grade,
                        "observation": self.observations, "files": []}
            for source in self.root.rglob("*"):
                if source.is_file():
                    relative = source.relative_to(self.root)
                    target = destination / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    manifest["files"].append({"path": str(relative).replace("\\", "/"),
                                              "sha256": hashlib.sha256(target.read_bytes()).hexdigest()})
            (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        shutil.rmtree(self.root)

    def db(self, mode="WAL", name="db"):
        path = self.root / name
        path.mkdir()
        database = path / "continuity.sqlite"
        initialise(database, mode)
        self.paths.append(database)
        return database

    def genesis(self, path, transition="genesis"):
        with connect(path) as db:
            h = prepare(db, record("CREATE", transition))
            self.assertEqual(cas(db, operation="CREATE", expected_revision=None,
                                 expected_source=None, target="B0", record_hash=h), "COMMITTED")
            return h

    def fresh(self, path):
        code = "import sqlite3,json,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute('SELECT revision,value FROM soul_root').fetchone(); print(json.dumps({'revision':r[0],'value':json.loads(r[1])} if r else None)); c.close()"
        result = subprocess.run([sys.executable, "-X", "utf8", "-c", code, str(path)],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def crash_snapshot(self, path):
        """Copy the quiescent file set before any recovery connection opens."""
        destination = path.parent / "crash-raw-before-reopen"
        destination.mkdir()
        copied = []
        for source in sorted(path.parent.glob(path.name + "*")):
            if source.is_file():
                shutil.copy2(source, destination / source.name)
                copied.append(source.name)
        self.assertIn(path.name, copied)
        return copied

    def race(self, path, mode, operation, index, second_operation=None):
        start = path.parent / "start"
        ready = [path.parent / f"ready-{i}.json" for i in range(2)]
        output = [path.parent / f"result-{i}.json" for i in range(2)]
        operations = [operation, second_operation or operation]
        processes = []
        started = []
        for i in range(2):
            started.append(time.monotonic())
            processes.append(subprocess.Popen([sys.executable, "-X", "utf8", str(PROBE / "primitive.py"),
                                               str(path), mode, operations[i], f"{operations[i]}-{index}-{i}",
                                               str(start), str(ready[i]), str(output[i])], stdout=subprocess.PIPE,
                                              stderr=subprocess.PIPE, text=True))
        try:
            deadline = min(started) + 8
            while not all(item.exists() for item in ready) and time.monotonic() < deadline:
                time.sleep(0.005)
            self.assertTrue(all(item.exists() for item in ready), "both workers must be prepared")
            prepared = [json.loads(item.read_text(encoding="utf-8")) for item in ready]
            self.assertEqual(prepared[0]["expected_revision"], prepared[1]["expected_revision"])
            if operations[0] == operations[1]:
                self.assertEqual(prepared[0]["expected_source"], prepared[1]["expected_source"])
            start.write_text("start", encoding="ascii")
            for i, process in enumerate(processes):
                stdout, stderr = process.communicate(timeout=max(0.1, started[i] + 10 - time.monotonic()))
                self.assertEqual(process.returncode, 0, (stdout, stderr))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=2)
        results = [json.loads(item.read_text(encoding="utf-8")) for item in output]
        self.assertEqual(sorted(r["outcome"] for r in results), ["CAS_FAIL", "COMMITTED"])
        self.observations.append({"mode": mode, "operations": operations, "trial": index, "results": results,
                                  "prepared": prepared, "fresh": self.fresh(path)})

    def test_p02_fork_races_source_advance_and_retirement(self):
        for mode in ("WAL", "DELETE"):
            for opponent in ("ADVANCE", "RETIRE"):
                for repeat in range(3):
                    path = self.db(mode, f"{mode}-{opponent}-{repeat}")
                    self.genesis(path)
                    self.race(path, mode, "FORK", repeat, opponent)
                    with connect(path) as db:
                        root = root_value(db)
                        self.assertEqual(root["revision"], 1)
                        if opponent == "ADVANCE":
                            self.assertNotEqual("B1" in root["branches"],
                                                root["branches"]["B0"]["generation"] == 1)
                        else:
                            self.assertNotEqual("B1" in root["branches"], root["retired"])

    def test_p01_p02_multiprocess_single_winner(self):
        for mode in ("WAL", "DELETE"):
            for index in range(10):
                path = self.db(mode, f"{mode}-{index}-create")
                self.race(path, mode, "CREATE", index)
                with connect(path) as db:
                    root = root_value(db)
                    self.assertEqual(root["revision"], 0)
                    self.assertEqual(list(root["branches"]), ["B0"])
                fork_path = self.db(mode, f"{mode}-{index}-fork")
                self.genesis(fork_path)
                self.race(fork_path, mode, "FORK", index)
                with connect(fork_path) as db:
                    root = root_value(db)
                    self.assertEqual(root["revision"], 1)
                    self.assertEqual(root["active"], "B0")
                    self.assertEqual(set(root["branches"]), {"B0", "B1"})
                    self.assertEqual(root["branches"]["B0"]["data"], "D0")
                    self.assertNotEqual(root["branches"]["B0"]["instance"], root["branches"]["B1"]["instance"])

    def test_p01_p02_each_cas_condition_rejects(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            source = self.genesis(path)
            with connect(path) as db:
                before = root_value(db)
                cases = [
                    ("revision", 7, source, "B1"),
                    ("source", 0, "wrong-source", "B1"),
                    ("target", 0, source, "B0"),
                ]
                for label, revision, head, target in cases:
                    item = record("FORK", label + mode, expected_revision=revision,
                                  expected_source=head, target=target, instance=label,
                                  parent_hash=head)
                    h = prepare(db, item)
                    self.assertEqual(cas(db, operation="FORK", expected_revision=revision,
                                         expected_source=head, target=target, record_hash=h), "CAS_FAIL")
                    self.assertEqual(root_value(db), before)
                retirement = record("RETIRE", "retire" + mode, expected_revision=0)
                rh = prepare(db, retirement)
                self.assertEqual(cas(db, operation="RETIRE", expected_revision=0,
                                     expected_source=None, target="B0", record_hash=rh), "COMMITTED")
                item = record("FORK", "after-retire" + mode, expected_revision=1,
                              expected_source=source, target="B1", instance="new", parent_hash=source)
                h = prepare(db, item)
                retired = root_value(db)
                self.assertEqual(cas(db, operation="FORK", expected_revision=1,
                                     expected_source=source, target="B1", record_hash=h), "CAS_FAIL")
                self.assertEqual(root_value(db), retired)
                self.observations.append({"mode": mode, "condition_rejections": [x[0] for x in cases] + ["retired"]})
            self.fresh(path)

    def test_p01_enroll_has_separate_baseline(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            with connect(path) as db:
                item = record("ENROLL", "enroll-legacy", data="legacy-candidate")
                h = prepare(db, item)
                self.assertEqual(cas(db, operation="ENROLL", expected_revision=None,
                                     expected_source=None, target="B0", record_hash=h), "COMMITTED")
                self.assertEqual(item["parent_kind"], "ENROLL_BASELINE")
                self.assertEqual(classify(db),
                                 ("COMMITTED", "CONTINUATION", "QUARANTINED(ACTIVATION_PENDING)", "DENIED"))
                self.observations.append({"mode": mode, "enroll_parent": item["parent_kind"],
                                          "historical_verdict": "UNKNOWN", "fresh": self.fresh(path)})

    def test_p03_fault_hooks_and_no_gc(self):
        for mode in ("WAL", "DELETE"):
            for hook in ("record_mid", "prepared", "before_commit", "anchor_pending"):
                for repeat in range(3):
                    path = self.db(mode, f"{mode}-{hook}-{repeat}")
                    process = subprocess.run([sys.executable, "-X", "utf8", str(PROBE / "fault_worker.py"),
                                              str(path), hook], capture_output=True, text=True, timeout=10)
                    self.assertEqual(process.returncode, 42, process.stderr)
                    raw_files = self.crash_snapshot(path)
                    with connect(path) as db:
                        root = root_value(db)
                        count = db.execute("SELECT count(*) FROM record").fetchone()[0]
                    expected = {"record_mid": (None, 0), "prepared": (None, 1),
                                "before_commit": (None, 1), "anchor_pending": (True, 1)}[hook]
                    self.assertEqual((bool(root) if root else None, count), expected)
                    self.observations.append({"mode": mode, "hook": hook, "repeat": repeat,
                                              "exit": process.returncode, "record_count": count,
                                              "raw_before_reopen": raw_files, "root": root,
                                              "fresh": self.fresh(path)})

    def test_p04_real_busy_and_lost_ack(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            with connect(path) as holder, connect(path) as contender:
                holder.execute("BEGIN IMMEDIATE")
                contender.execute("PRAGMA busy_timeout=20")
                with self.assertRaises(sqlite3.OperationalError) as raised:
                    contender.execute("BEGIN IMMEDIATE")
                self.assertIn("locked", str(raised.exception).lower())
                holder.execute("ROLLBACK")
                item = record("CREATE", "lost-ack")
                h = prepare(contender, item)
                self.assertEqual(cas(contender, operation="CREATE", expected_revision=None,
                                     expected_source=None, target="B0", record_hash=h), "COMMITTED")
                self.assertEqual(cas(contender, operation="CREATE", expected_revision=None,
                                     expected_source=None, target="B0", record_hash=h), "CAS_FAIL")
                with self.assertRaisesRegex(ValueError, "TRANSITION_PAYLOAD_CONFLICT"):
                    prepare(contender, record("CREATE", "lost-ack", data="different"))
                self.observations.append({"mode": mode, "begin_busy": str(raised.exception),
                                          "lost_ack_root": root_value(contender), "fresh": self.fresh(path)})

    def test_p04_delete_commit_busy_gate_stays_closed(self):
        path = self.db("DELETE", "delete-commit-busy")
        with connect(path) as reader, connect(path) as writer:
            reader.execute("BEGIN")
            self.assertEqual(reader.execute("SELECT count(*) FROM soul_root").fetchone()[0], 0)
            writer.execute("PRAGMA busy_timeout=20")
            writer.execute("BEGIN IMMEDIATE")
            writer.execute("INSERT INTO soul_root VALUES(?,?,?,?)", ("synthetic", "S", 0, b"{}"))
            with self.assertRaises(sqlite3.OperationalError) as raised:
                writer.execute("COMMIT")
            self.assertIn("locked", str(raised.exception).lower())
            self.assertTrue(writer.in_transaction)
            gate = "DENIED_PENDING_TRANSACTION" if writer.in_transaction else "UNKNOWN"
            self.assertEqual(gate, "DENIED_PENDING_TRANSACTION")
            reader.execute("ROLLBACK")
            writer.execute("COMMIT")
            self.assertFalse(writer.in_transaction)
            self.observations.append({"mode": "DELETE", "commit_busy": str(raised.exception),
                                      "pending_gate": gate, "after_writer_drain": self.fresh(path)})

    def test_p04_real_sqlite_interrupt(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            with connect(path) as db:
                db.set_progress_handler(lambda: 1, 1)
                with self.assertRaises(sqlite3.OperationalError) as raised:
                    db.execute("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<1000) SELECT sum(x) FROM n").fetchone()
                db.set_progress_handler(None, 0)
                self.assertIn("interrupt", str(raised.exception).lower())
                self.assertIsNone(root_value(db))
                self.observations.append({"mode": mode, "sqlite_interrupt": str(raised.exception),
                                          "fresh": self.fresh(path)})

    def test_p04_lost_ack_fresh_process_exact_query(self):
        for mode in ("WAL", "DELETE"):
            for repeat in range(3):
                path = self.db(mode, f"{mode}-{repeat}")
                process = subprocess.run([sys.executable, "-X", "utf8", str(PROBE / "fault_worker.py"),
                                          str(path), "ack_lost"], capture_output=True, text=True, timeout=10)
                self.assertEqual(process.returncode, 42, process.stderr)
                raw_files = self.crash_snapshot(path)
                query = subprocess.run([sys.executable, "-X", "utf8", str(PROBE / "query_worker.py"),
                                        str(path), "lost-ack-fresh"], capture_output=True, text=True, timeout=10)
                self.assertEqual(query.returncode, 0, query.stderr)
                answer = json.loads(query.stdout)
                self.assertEqual(answer["outcome"], "COMMITTED")
                self.assertEqual(answer["root_revision"], 0)
                self.assertEqual(answer["record_count"], 1)
                with connect(path) as db:
                    self.assertEqual(prepare(db, record("CREATE", "lost-ack-fresh")), answer["record_hash"])
                    self.assertEqual(db.execute("SELECT count(*) FROM record").fetchone()[0], 1)
                    self.assertEqual(root_value(db)["revision"], 0)
                self.observations.append({"mode": mode, "repeat": repeat, "hook": "ack_lost",
                                          "raw_before_reopen": raw_files, "fresh_query": answer})

    def test_p02_corrupt_root_or_source_rejects_before_cas(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            source = self.genesis(path)
            with connect(path) as db:
                item = record("FORK", "fork-corrupt", expected_revision=0,
                              expected_source=source, target="B1", instance="I1", parent_hash=source)
                h = prepare(db, item)
                original = db.execute("SELECT value FROM soul_root").fetchone()[0]
                for label, changed in (
                    ("revision", dict(json.loads(original), revision=99)),
                    ("protocol", dict(json.loads(original), protocol=999)),
                ):
                    db.execute("UPDATE soul_root SET value=?", (json.dumps(changed).encode(),))
                    before = db.execute("SELECT revision,value FROM soul_root").fetchone()
                    with self.assertRaises((ValueError, KeyError)):
                        cas(db, operation="FORK", expected_revision=0,
                            expected_source=source, target="B1", record_hash=h)
                    self.assertEqual(tuple(db.execute("SELECT revision,value FROM soul_root").fetchone()), tuple(before))
                    self.assertEqual(classify(db),
                                     ("INDETERMINATE", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
                    db.execute("UPDATE soul_root SET value=?", (original,))
                db.execute("DELETE FROM record WHERE hash=?", (source,))
                before = db.execute("SELECT revision,value FROM soul_root").fetchone()
                with self.assertRaises(ValueError):
                    cas(db, operation="FORK", expected_revision=0,
                        expected_source=source, target="B1", record_hash=h)
                self.assertEqual(tuple(db.execute("SELECT revision,value FROM soul_root").fetchone()), tuple(before))
                self.observations.append({"mode": mode, "rejected": ["revision", "protocol", "missing_source"],
                                          "fresh": self.fresh(path)})

    def test_p05_synthetic_admission_bypass_is_detected(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            self.genesis(path)
            with connect(path) as db:
                before = root_value(db)
                admitted = classify(db, registry_data="D0")
                self.assertEqual(admitted, ("COMMITTED", "CONTINUATION", "READY", "DENIED"))
                # A process holding the same OS credentials can bypass a purely
                # in-process broker and update this disposable file directly.
                db.execute("UPDATE soul_root SET revision=99 WHERE domain='synthetic' AND soul='S'")
                after = db.execute("SELECT revision FROM soul_root").fetchone()[0]
                self.assertEqual(after, 99)
                self.assertEqual(classify(db),
                                 ("INDETERMINATE", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
                self.observations.append({"mode": mode, "synthetic_broker": admitted,
                                          "direct_write_bypass": True, "old_root": before,
                                          "new_revision": after, "after_bypass": classify(db),
                                          "action": "DENY_REAL_ADMISSION"})
            self.fresh(path)

    def test_p05_cross_process_gate_wait_and_owner_death(self):
        fixture = self.root / "gate-fixture"
        fixture.mkdir()
        gate = fixture / "gate.sqlite"
        business = fixture / "business.sqlite"
        with closing(sqlite3.connect(gate)) as db:
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("CREATE TABLE gate(epoch INTEGER NOT NULL)")
            db.execute("INSERT INTO gate VALUES(0)")
            db.commit()
        with closing(sqlite3.connect(business)) as db:
            db.execute("CREATE TABLE business(value TEXT)")

        for index, action in enumerate(("release", "kill")):
            ready = fixture / f"ready-{index}"
            release = fixture / f"release-{index}"
            worker = subprocess.Popen([sys.executable, "-X", "utf8", str(PROBE / "gate_worker.py"),
                                       str(gate), str(business), str(ready), str(release)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            worker_deadline = time.monotonic() + 10
            try:
                deadline = worker_deadline - 2
                while not ready.exists() and time.monotonic() < deadline:
                    time.sleep(0.005)
                self.assertTrue(ready.exists(), "business writer must hold shared gate")
                with closing(sqlite3.connect(gate, isolation_level=None, timeout=0.03)) as transition:
                    transition.execute("PRAGMA busy_timeout=30")
                    with self.assertRaises(sqlite3.OperationalError) as raised:
                        transition.execute("BEGIN EXCLUSIVE")
                    self.assertIn("locked", str(raised.exception).lower())
                if action == "release":
                    release.write_text("done", encoding="ascii")
                else:
                    worker.kill()
                stdout, stderr = worker.communicate(timeout=max(0.1, worker_deadline - time.monotonic()))
                if action == "release":
                    self.assertEqual(worker.returncode, 0, (stdout, stderr))
                else:
                    self.assertNotEqual(worker.returncode, 0)
                with closing(sqlite3.connect(gate, isolation_level=None, timeout=1)) as transition:
                    transition.execute("BEGIN EXCLUSIVE")
                    transition.execute("UPDATE gate SET epoch=epoch+1")
                    transition.execute("COMMIT")
                with closing(sqlite3.connect(business)) as data:
                    count = data.execute("SELECT count(*) FROM business").fetchone()[0]
                self.assertEqual(count, 1)  # Killed writer's second insert rolled back.
                self.observations.append({"gate_case": action, "exclusive_after_drain": True,
                                          "business_committed_rows": count,
                                          "worker_exit": worker.returncode})
            finally:
                if worker.poll() is None:
                    worker.kill()
                    worker.communicate(timeout=2)

    def test_p06_business_restore_cannot_establish_nonrollback(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            self.genesis(path)
            business = path.parent / "business.json"
            business.write_text('{"data":"D0"}', encoding="utf-8")
            backup = path.parent / "business-backup.json"
            shutil.copy2(business, backup)
            business.write_text('{"data":"D1"}', encoding="utf-8")
            shutil.copy2(backup, business)
            with connect(path) as db:
                self.assertEqual(root_value(db)["revision"], 0)
                self.assertEqual(classify(db, registry_data="D1"),
                                 ("COMMITTED", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
            with connect(path) as db:
                if mode == "WAL":
                    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            old_copy = path.parent / "old-continuity.sqlite"
            shutil.copy2(path, old_copy)
            with connect(path) as db:
                db.execute("UPDATE soul_root SET revision=7 WHERE domain='synthetic' AND soul='S'")
                if mode == "WAL":
                    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            self.assertEqual(json.loads(self.fresh(path))["revision"], 7)
            shutil.copy2(old_copy, path)
            with connect(path) as db:
                reverted = db.execute("SELECT revision FROM soul_root").fetchone()[0]
                self.assertEqual(reverted, 0)
            # Same-principal overwrite succeeds in the fixture. Production
            # nonrollback therefore needs an external management boundary.
            self.observations.append({"mode": mode, "business_restore": business.read_text(encoding="utf-8"),
                                      "continuity_unchanged": self.fresh(path),
                                      "same_principal_old_file_restore_revision": reverted,
                                      "e3": "NOT_PROVEN"})

    def test_p07_four_axes_and_corruption(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            self.genesis(path)
            with connect(path) as db:
                self.assertEqual(classify(db), ("COMMITTED", "CONTINUATION",
                                                 "QUARANTINED(ACTIVATION_PENDING)", "DENIED"))
                self.assertEqual(classify(db, registry_data="D0"),
                                 ("COMMITTED", "CONTINUATION", "READY", "DENIED"))
                self.assertEqual(classify(db, registry_data="unexpected"),
                                 ("COMMITTED", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
                self.assertEqual(classify(db, known_version=False),
                                 ("COMMITTED", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
                root = root_value(db)
                with closing(sqlite3.connect(path.parent / "before-corruption.sqlite")) as snapshot:
                    db.backup(snapshot)
                db.execute("UPDATE record SET bytes=? WHERE hash=?", (b"damaged", root["branches"]["B0"]["record"]))
                with closing(sqlite3.connect(path.parent / "after-corruption.sqlite")) as snapshot:
                    db.backup(snapshot)
                self.assertEqual(classify(db),
                                 ("COMMITTED", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
                self.observations.append({"mode": mode, "corrupt": classify(db), "fresh": self.fresh(path)})

    def test_isolation_denies_unregistered_paths(self):
        unregistered = self.root.parent / "unregistered-m1a" / "continuity.sqlite"
        with self.assertRaises(ValueError):
            with connect(unregistered):
                pass
        with self.assertRaises(ValueError):
            evidence_sink(self.root / "run-outside")
        with self.assertRaises(ValueError):
            fixture_path(self.root.parent / "not-owned" / "result")
        self.observations.append({"path_guards": "UNREGISTERED_OR_OUTSIDE_DENIED"})

    def test_p07_fork_target_pending_and_parent_loss(self):
        for mode in ("WAL", "DELETE"):
            path = self.db(mode, mode)
            source = self.genesis(path)
            with connect(path) as db:
                item = record("FORK", "fork-target", expected_revision=0, expected_source=source,
                              target="B1", instance="I1", data="D1", parent_hash=source)
                h = prepare(db, item)
                self.assertEqual(cas(db, operation="FORK", expected_revision=0,
                                     expected_source=source, target="B1", record_hash=h), "COMMITTED")
                self.assertEqual(classify(db, target="B1"),
                                 ("COMMITTED", "FORK", "QUARANTINED(ACTIVATION_PENDING)", "DENIED"))
                self.assertEqual(classify(db, target="B1", registry_data="D1"),
                                 ("COMMITTED", "FORK", "READY", "DENIED"))
                with closing(sqlite3.connect(path.parent / "before-parent-loss.sqlite")) as snapshot:
                    db.backup(snapshot)
                db.execute("DELETE FROM record WHERE hash=?", (source,))
                with closing(sqlite3.connect(path.parent / "after-parent-loss.sqlite")) as snapshot:
                    db.backup(snapshot)
                self.assertEqual(classify(db, target="B1"),
                                 ("COMMITTED", "UNKNOWN", "QUARANTINED(EVIDENCE_CONFLICT)", "DENIED"))
                self.observations.append({"mode": mode, "target_parent_missing": classify(db, target="B1"),
                                          "fresh": self.fresh(path)})


if __name__ == "__main__":
    unittest.main()
