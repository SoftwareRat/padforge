# PadForge

Build your own copy of a supported Pad game on your own computer, from your own
disc or ROM. PadForge checks your computer, runs the game's own builder, shows
progress, and audits the result. Nothing is uploaded and no game files are
downloaded.

**Experimental.** No complete game build through PadForge has been accepted
yet. Public game-app distribution is paused. See [STATUS.md](STATUS.md) and
[docs/DECISIONS.md](docs/DECISIONS.md).

## Commands

Python 3.9 or newer; no packages needed. From this repository:

```sh
python3 -m padforge list                      # supported games and platforms
python3 -m padforge ui                        # local browser page (same commands)
python3 -m padforge doctor kartpad            # check this computer (installs nothing)
python3 -m padforge doctor bluewake --repo /path/to/bluewake
python3 -m padforge audit path/to/file-or-folder   # release gate
python3 -m padforge check-manifest /path/to/game-repo
python3 -m padforge plan bluewake --repo /path/to/bluewake \
  --revision FULL_REVIEWED_COMMIT --disc '/path/to/your disc.iso'
```

`plan` validates paths, checkout state and platform support and prints the
exact backend command without building. Change `plan` to `build` to run it.
Use `--target` to choose a platform the game declares (default `ios`),
`--source-only`/`--no-mods` where the game supports them, and `--jobs 1-8`.

Builds run on the platforms each game marks *verified* or *experimental*;
`list` shows the rest as *planned*. Today that is iPhone/iPad builds on an Apple
Silicon Mac for BlueWake and KartPad. Windows and Linux support is planned; see
the decision record for what has been tested.

## How games plug in

Each game repository declares a `padforge.json` manifest (schema in
[padforge/manifest.py](padforge/manifest.py)): accepted inputs, platforms and
their status, the backend command, stages, requirements and publication
policy. PadForge's [catalog](catalog/) pins each supported game and carries an
interim manifest for repositories that do not have one yet. Game-specific
translation, patches and packaging stay in the game repository.

## What a build does and does not do

- Keep the game checkout clean at a commit you have reviewed. PadForge does
  not download repositories or install tools; follow `doctor`'s suggestions.
- Builds, logs and records stay under the game's ignored `build/padforge/`.
  One PadForge build runs per checkout; Ctrl-C cancels and keeps finished work.
- Every personal output is checked for structure and provenance, then run
  through the release gate. The record labels it *personal build, not
  publishable* regardless of the gate result.
- Nothing is installed on a device or uploaded. A personal IPA still needs
  your own signing (AltStore, SideStore, Sideloadly or Xcode).

## The release gate

`padforge audit` scans files, folders and ZIP-based packages for console keys,
address-named translated game functions, embedded original program sections
and provenance declaring translated game code. It fails closed on archives it
cannot inspect. Keys are identified by a short prefix and a SHA-256 hash; this
repository contains no keys. A PASS is a heuristic result, not copyright or
licensing clearance.

Game inputs, generated game code, saves, keys, personal builds and optimization
profiles never belong in this repository.

## Tests

```sh
python3 -m unittest discover -s tests -v
```
