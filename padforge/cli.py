"""A small, Mac-only runner. Game backends retain validation and caching."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import subprocess
import sys
import time
import uuid

from . import __version__
from .package import validate_ipa

ENTRYPOINTS = {"bluewake": "scripts/builder/build.sh",
               "kartpad": "scripts/build-user-ipa.sh"}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


@contextlib.contextmanager
def workspace_lock(path):
    # Kernel releases the lock on exit/crash; do not delete the lock file.
    with path.open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("Another PadForge process is using this checkout") from None
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def check_checkout(repo, revision):
    if git(repo, "rev-parse", "HEAD") != revision:
        raise ValueError("Backend HEAD does not match --revision")
    if git(repo, "status", "--porcelain", "--untracked-files=normal"):
        raise ValueError("Backend has local changes; use a clean reviewed checkout")


def validate(args):
    repo = args.repo.expanduser().resolve()
    disc = args.disc.expanduser().resolve()
    if not disc.is_file():
        raise ValueError("Disc image must be an existing local file")
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        raise ValueError("--revision must be the full reviewed Git commit (40 lowercase hex digits)")
    if git(repo, "rev-parse", "--show-toplevel") != str(repo):
        raise ValueError("--repo must be the root of the selected backend checkout")
    check_checkout(repo, args.revision)
    if not (repo / ENTRYPOINTS[args.game]).is_file():
        raise ValueError("Selected checkout does not contain the game's entrypoint")
    if args.game == "kartpad" and (args.source_only or args.no_mods):
        raise ValueError("KartPad does not expose source-only or mod selection through its CLI")
    return repo, disc


def command(args, repo, disc, work, output):
    base = ["/bin/bash", str(repo / ENTRYPOINTS[args.game])]
    if args.game == "bluewake":
        base += [str(disc), "--out", str(work), "--jobs", str(args.jobs)]
        base += ["--source-only"] if args.source_only else ["--train-pgo", "--ipa", str(output)]
        if args.no_mods:
            base += ["--no-mods"]
    else:
        base += ["build", str(disc), "--work-root", str(work),
                 "--output", str(output), "--jobs", str(args.jobs)]
    return base


def run_process(argv, cwd, log_path, event_path, emit, before_spawn=None):
    """Relay new backend events; retain complete output in a private local log."""
    offset = event_path.stat().st_size if event_path.exists() else 0
    pending = b""

    def relay():
        nonlocal offset, pending
        if not event_path.exists():
            return
        if event_path.stat().st_size < offset:
            offset, pending = 0, b""
        with event_path.open("rb") as stream:
            stream.seek(offset)
            data = stream.read(65536)
            offset = stream.tell()
        pending += data
        while b"\n" in pending:
            line, pending = pending.split(b"\n", 1)
            try:
                event = json.loads(line)
                if isinstance(event, dict) and event.get("schema_version") == 1:
                    emit("backend_event", backend=event)
            except (ValueError, UnicodeError):
                emit("progress_warning", reason="Malformed backend event; see local log")
        if len(pending) > 1024 * 1024:
            pending = b""
            emit("progress_warning", reason="Oversized backend event skipped")
        return bool(data)

    def drain():
        # Keep live polls bounded, but read every remaining chunk after shutdown.
        while relay():
            pass

    def interrupt(_signum, _frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, interrupt)
    process = None
    try:
        with log_path.open("wb") as log:
            if before_spawn is not None:
                before_spawn()
            process = subprocess.Popen(argv, cwd=cwd, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            last_progress = time.monotonic()
            while process.poll() is None:
                relay()
                if time.monotonic() - last_progress >= 15:
                    emit("build_progress", status="running; see backend.log")
                    last_progress = time.monotonic()
                time.sleep(0.2)
            drain()
            return process.returncode, False
    except KeyboardInterrupt:
        if process is not None:
            # BlueWake's stage wrapper forwards TERM to its own child session.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + 20
            while True:
                process.poll()
                try:
                    os.killpg(process.pid, 0)
                except ProcessLookupError:
                    break
                if time.monotonic() >= deadline:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    break
                time.sleep(0.1)
            process.wait()
            drain()
        return 130, True
    finally:
        signal.signal(signal.SIGTERM, previous)


def workspace_root(args, repo):
    selected = getattr(args, "workspace_root", None)
    root = selected.expanduser().resolve() if selected else (repo / "build/padforge").resolve()
    if repo / "build" not in root.parents:
        raise ValueError("Workspace root must be below the backend's build directory")
    return root


def execute(args, repo, disc):
    # One lock per backend checkout also covers caches outside the selected work dir.
    lock_root = repo / "build/padforge"
    root = workspace_root(args, repo)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if subprocess.run(["git", "-C", str(repo), "check-ignore", "-q", str(root)]).returncode:
        raise ValueError("Backend must ignore build/padforge before running")
    lock_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with workspace_lock(lock_root / "runner.lock"):
        print("Hashing the disc for the build record…", flush=True)
        identity = {"schema_version": 1, "padforge_version": __version__,
                    "game": args.game, "revision": args.revision,
                    "disc_sha256": digest(disc), "target": "ios",
                    "mods": (not args.no_mods) if args.game == "bluewake" else "backend-default",
                    "source_only": args.source_only,
                    "jobs": args.jobs}
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        work = root / key / "backend"
        attempt = root / key / "runs" / uuid.uuid4().hex
        attempt.mkdir(parents=True, mode=0o700)
        output = attempt / "personal.ipa"
        started = time.monotonic()

        def emit(event, **fields):
            record = dict(schema_version=1, event=event,
                          build_elapsed_seconds=round(time.monotonic() - started, 2), **fields)
            with (attempt / "progress.jsonl").open("a") as stream:
                stream.write(json.dumps(record) + "\n")
            backend = fields.get("backend", {})
            counts = ""
            if "completed" in backend and "total" in backend:
                counts = f" {backend['completed']}/{backend['total']} {backend.get('unit', '')}"
            print(f"[{record['build_elapsed_seconds']}s] {event}: "
                  f"{backend.get('stage', '')} {backend.get('event', '')}{counts}".strip(), flush=True)

        record = dict(identity, status="running", publication="personal-only",
                      backend_validation="not-established-by-runner")
        atomic_json(attempt / "record.json", record)
        emit("build_started")
        print(f"Local log: {attempt / 'backend.log'}", flush=True)

        def recheck(phase):
            record["checkout_check"] = phase + "-failed"
            check_checkout(repo, args.revision)
            record["checkout_check"] = phase + "-passed"

        try:
            code, cancelled = run_process(command(args, repo, disc, work, output), repo,
                                          attempt / "backend.log", work / "logs/progress.jsonl", emit,
                                          before_spawn=lambda: recheck("before-launch"))
            recheck("after-exit")
            if code == 0 and not args.source_only:
                if not output.is_file() or output.stat().st_size == 0:
                    raise ValueError("Backend exited successfully but produced no IPA")
                record["package_validation"] = validate_ipa(output, args.game, args.revision,
                                                            identity["disc_sha256"])
                record["output_sha256"] = digest(output)
                record["output"] = "personal.ipa"
            recheck("before-record")
            status = "cancelled" if cancelled else "completed" if code == 0 else "failed"
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            code, status = 1, "failed"
            record["failure_type"] = type(error).__name__
            print(f"Build failed: {error}", file=sys.stderr)
        record.update(status=status, exit_code=code)
        atomic_json(attempt / "record.json", record)
        emit("build_" + status, exit_code=code)
        print(f"Build record: {attempt / 'record.json'}")
        return code if code >= 0 else 128 - code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["plan", "build"])
    parser.add_argument("game", choices=ENTRYPOINTS)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--revision", required=True, help="Full commit you have reviewed and trust")
    parser.add_argument("--disc", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path,
                        help="Ignored directory below backend build/ (default: build/padforge)")
    parser.add_argument("--jobs", type=int, choices=range(1, 9), default=2)
    parser.add_argument("--source-only", action="store_true", help="BlueWake: stop before compilation")
    parser.add_argument("--no-mods", action="store_true", help="BlueWake only")
    args = parser.parse_args(argv)
    try:
        repo, disc = validate(args)
        if args.action == "plan":
            root = workspace_root(args, repo)
            print(json.dumps({"experimental": True, "target": "ios", "argv": command(
                args, repo, disc, root / "CONFIG/backend",
                root / "CONFIG/runs/ATTEMPT/personal.ipa")}, indent=2))
            return 0
        if platform.system() != "Darwin" or platform.machine() != "arm64":
            raise ValueError("This experimental runner currently supports Apple Silicon Macs only")
        return execute(args, repo, disc)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"PadForge: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130
