"""Tools PadForge downloads for a game: pinned, checked, kept in PadForge's own folder.

The lock (tools.lock.json, made by scripts/update-tools-lock.py) names every
download and the publisher's digest. Nothing is installed system-wide: builds
get the tools on PATH, plus the environment variables they need.
"""
import hashlib
import json
import os
import shutil
import stat
import sys
import tarfile
import urllib.request
import zipfile
from pathlib import Path

LOCK = Path(__file__).with_name("tools.lock.json")
DIGESTS = ("sha512", "sha256", "sha1")


def lock():
    return json.loads(LOCK.read_text())["tools"]


def tools_root():
    return Path(os.environ.get("PADFORGE_HOME", Path.home() / ".padforge")) / "tools"


def _folder(name, tool):
    return tools_root() / f"{name}-{tool['version']}"


def _marker(folder):
    return folder / ".padforge-installed"


def _download(entry, destination, stream):
    algo = next(key for key in DIGESTS if key in entry)
    digest = hashlib.new(algo)
    partial = destination.with_name(destination.name + ".partial")
    print(f"  downloading {entry['url']}", file=stream, flush=True)
    with urllib.request.urlopen(entry["url"]) as response, partial.open("wb") as handle:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            handle.write(chunk)
    if digest.hexdigest() != entry[algo].lower():
        partial.unlink()
        raise RuntimeError(f"{algo} mismatch for {entry['url']}; nothing was installed")
    partial.replace(destination)


def _extract_zip(archive, folder):
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            path = bundle.extract(info, folder)
            mode = info.external_attr >> 16
            if mode & 0o111 and os.name != "nt":
                os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _extract_tar(archive, folder):
    with tarfile.open(archive) as bundle:
        if sys.version_info >= (3, 12):
            bundle.extractall(folder, filter="data")
        else:
            bundle.extractall(folder)


def install(names, host, stream=None):
    """Install the named tools for this host; already-installed tools are kept."""
    stream = stream or sys.stdout
    table = lock()
    for name in names:
        tool = table[name]
        entry = tool["hosts"].get(host)
        if entry is None:
            if name == "git" and shutil.which("git"):
                print(f"ok   git (system {shutil.which('git')})", file=stream)
                continue
            raise RuntimeError(f"{name} {tool['version']} has no download for {host}")
        folder = _folder(name, tool)
        if _marker(folder).is_file():
            print(f"ok   {name} {tool['version']}", file=stream)
            continue
        staging = folder.with_name(folder.name + ".partial")
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True)
        archive = staging / "download"
        _download(entry, archive, stream)
        kind = entry["archive"]
        if kind == "zip":
            _extract_zip(archive, staging)
            archive.unlink()
        elif kind == "tar.gz":
            _extract_tar(archive, staging)
            archive.unlink()
        else:
            target = staging / entry["rename"]
            archive.replace(target)
            target.chmod(0o755)
        if folder.exists():
            shutil.rmtree(folder)
        staging.replace(folder)
        _marker(folder).write_text(json.dumps(entry) + "\n")
        print(f"got  {name} {tool['version']}", file=stream)


def environment(names, host, base=None):
    """base (default os.environ) with installed tools first on PATH."""
    env = dict(os.environ if base is None else base)
    paths = []
    table = lock()
    for name in names:
        tool = table[name]
        entry = tool["hosts"].get(host)
        folder = _folder(name, tool)
        if entry is None or not _marker(folder).is_file():
            continue
        for relative in entry.get("bin", tool.get("bin", [])):
            paths.append(str(folder / relative))
        for key, relative in tool.get("env", {}).items():
            env[key] = str(folder / relative)
    if paths:
        env["PATH"] = os.pathsep.join(paths + [env.get("PATH", "")])
    return env
