import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import unittest

from padforge.cli import command, execute, run_process, validate, workspace_lock


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="padforge test ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "backend"
        self.repo.mkdir()
        self.disc = self.root / "own disc $(do not execute).iso"
        self.disc.write_bytes(b"synthetic input, not game data")
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        (self.repo / ".gitignore").write_text("build/\n")
        script = self.repo / "scripts/build-user-ipa.sh"
        script.parent.mkdir()
        script.write_text('''#!/bin/bash
while [ $# -gt 0 ]; do
  if [ "$1" = "--output" ]; then printf 'synthetic test artifact' > "$2"; exit 0; fi
  shift
done
exit 2
''')
        self.git("add", ".")
        self.git("commit", "-qm", "Synthetic test backend")
        self.args = argparse.Namespace(game="kartpad", repo=self.repo, disc=self.disc,
            revision=self.git("rev-parse", "HEAD"), source_only=False, no_mods=False, jobs=2)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def test_explicit_pin_and_clean_checkout(self):
        self.assertEqual(validate(self.args), (self.repo, self.disc))
        self.args.revision = "0" * 40
        with self.assertRaisesRegex(ValueError, "HEAD"):
            validate(self.args)
        self.args.revision = self.git("rev-parse", "HEAD")
        (self.repo / "extra.py").write_text("unreviewed")
        with self.assertRaisesRegex(ValueError, "local changes"):
            validate(self.args)

    def test_argument_paths_are_not_shell_strings(self):
        argv = command(self.args, self.repo, self.disc, self.root, self.root / "test.ipa")
        self.assertEqual(argv[3], str(self.disc))
        self.assertIn("--work-root", argv)

    def test_bluewake_requires_local_training(self):
        self.args.game = "bluewake"
        argv = command(self.args, self.repo, self.disc, self.root, self.root / "test.ipa")
        self.assertIn("--train-pgo", argv)
        self.assertNotIn("--install", argv)
        self.args.source_only = True
        argv = command(self.args, self.repo, self.disc, self.root, self.root / "test.ipa")
        self.assertIn("--source-only", argv)
        self.assertNotIn("--ipa", argv)

    def test_kartpad_rejects_unsupported_options(self):
        self.args.no_mods = True
        with self.assertRaisesRegex(ValueError, "mod selection"):
            validate(self.args)

    def test_lock_rejects_second_writer_and_releases(self):
        path = self.root / "lock"
        with workspace_lock(path):
            with self.assertRaisesRegex(ValueError, "Another"):
                with workspace_lock(path):
                    self.fail("second writer acquired lock")
        with workspace_lock(path):
            pass

    def test_execute_records_hash_and_reuses_configuration(self):
        for _ in range(2):
            self.assertEqual(execute(self.args, self.repo, self.disc), 0)
        root = self.repo / "build/padforge"
        self.assertEqual(len(list(root.glob("*/backend"))), 0)  # fake backend needs no cache
        records = list(root.glob("*/runs/*/record.json"))
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].parents[2], records[1].parents[2])
        for path in records:
            data = json.loads(path.read_text())
            self.assertEqual(data["status"], "completed")
            self.assertEqual(len(data["output_sha256"]), 64)
            self.assertNotIn(str(self.root), path.read_text())

    def test_success_without_output_fails(self):
        (self.repo / "scripts/build-user-ipa.sh").write_text("exit 0\n")
        self.assertEqual(execute(self.args, self.repo, self.disc), 1)
        record = next((self.repo / "build/padforge").glob("*/runs/*/record.json"))
        self.assertEqual(json.loads(record.read_text())["status"], "failed")

    def test_events_skip_old_and_survive_partial_lines(self):
        events = self.root / "progress.jsonl"
        events.write_text('{"schema_version":1,"stage":"old"}\n')
        script = "import sys,time; f=open(sys.argv[1],'a'); f.write('{\"schema_version\":1,'); f.flush(); time.sleep(.3); f.write('\"stage\":\"new\"}\\ninvalid\\n'); f.close()"
        seen = []
        code, cancelled = run_process([sys.executable, "-c", script, str(events)], self.root,
                                      self.root / "out.log", events,
                                      lambda event, **kw: seen.append((event, kw)))
        self.assertEqual((code, cancelled), (0, False))
        self.assertEqual(seen[0][1]["backend"]["stage"], "new")
        self.assertEqual(seen[1][0], "progress_warning")

    def test_failed_backend_exit_preserved(self):
        result = run_process([sys.executable, "-c", "raise SystemExit(7)"], self.root,
                             self.root / "out.log", self.root / "events",
                             lambda *a, **kw: None)
        self.assertEqual(result, (7, False))

    def test_cancel_reaches_child(self):
        marker = self.root / "cancelled"
        ready = self.root / "ready"
        script = "import signal,time,pathlib,sys; signal.signal(signal.SIGTERM, lambda *a: (pathlib.Path(sys.argv[1]).write_text('stopped'),sys.exit(0))); pathlib.Path(sys.argv[2]).touch(); time.sleep(30)"
        def cancel():
            import time
            for _ in range(100):
                if ready.exists():
                    os.kill(os.getpid(), signal.SIGINT)
                    return
                time.sleep(.02)
        thread = threading.Thread(target=cancel)
        thread.start()
        result = run_process([sys.executable, "-c", script, str(marker), str(ready)], self.root,
                             self.root / "out.log", self.root / "events",
                             lambda *a, **kw: None)
        thread.join()
        self.assertEqual(result, (130, True))
        self.assertEqual(marker.read_text(), "stopped")


if __name__ == "__main__":
    unittest.main()
