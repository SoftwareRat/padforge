# Agent instructions

- This repository holds only the shared Builder: its pipeline, profiles, tests and docs. Never commit or upload game code (translated or decompiled), disc images, ROMs, extracted game files, saves, console keys or personal builds.
- Before any public release, every asset must pass `python3 ~/.codex/release-gate/release_gate.py <asset>` on the maintainer's machine. A failure is a stop, not a note.
- The first working pipeline is being developed in the BlueWake repository (`scripts/builder/`). Coordinate with that work before moving code here; there must be only one Builder.
- Keep it simple: a generic pipeline plus one small profile per game.

