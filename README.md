# PadForge

A shared local command-line frontend for the Pad projects' existing builders.
Choose a supported game checkout and your disc image; its backend validates the
input and builds a personal app on your computer.

**Experimental, not a release-ready player workflow.** The runner has synthetic
tests; no complete game build through PadForge has been accepted yet. BlueWake
is validating local optimization training. KartPad's Mac and Android adapters
are not implemented. Public game-app distribution remains paused.

## Try the CLI

Use Python 3.9 or newer on an Apple Silicon Mac. No Python packages are needed.
Keep the game checkout clean at a commit you have reviewed and trust. PadForge
does not download repositories or install build tools. Follow that game's
dependency setup first (KartPad exposes `bootstrap` in its existing builder).

From this repository:

```sh
python3 -m padforge --help
python3 -m padforge plan bluewake --repo /path/to/bluewake \
  --revision FULL_REVIEWED_COMMIT --disc '/path/to/your disc.iso'
```

Replace `FULL_REVIEWED_COMMIT` with the actual 40-character commit. `plan`
validates paths and checkout state and prints the argument array without
building or hashing the disc. Change `plan` to `build` to execute. BlueWake
uses local `--train-pgo`; `--source-only` stops before compilation and
`--no-mods` selects its base-game path. Training performance is still unverified.

For KartPad, select `kartpad` with its checkout and supported disc instead.
The current adapter produces only an iOS IPA. `--jobs` accepts 1–8, default 2.
KartPad has no source-only or mod-selection option in its current CLI.

Builds, logs and records stay under the game's ignored `build/padforge/`.
Use `--workspace-root /path/to/game/build/separate-check` for a separate ignored
workspace; it shares the same checkout-wide lock.
Preflight and full builds share backend work, as do runs with different job counts.
Each attempt retains its own options, log and output. Changing the backend revision
(even docs-only), disc, target or mods selects a separate workspace. Old workspaces
from earlier PadForge key formats remain preserved but are not automatically reused.
Ctrl-C requests cancellation
and keeps existing work. PadForge allows one of its builds per game checkout;
do not run the backend directly in parallel. Detailed logs may contain local
paths and should not be shared without review. Nothing is installed on a device
or uploaded by PadForge. A personal IPA still needs separate signing/install.

## Status and next steps

One real BlueWake source-only integration passed at reviewed revision
`36b8488e7887e4f3ea4600c7d09790a24c241021`: extraction, translation and verified
composite-source generation completed with progress and a successful record.
This did not compile a game app, package an IPA or test a device.

[Integration notes](docs/INTEGRATION.md) describe the exact backend commands,
progress and cancellation limits, provenance gaps and remaining acceptance
checks. The first frontend is a CLI; a downloadable Mac app can come later.
Windows and additional targets require their own tested adapters. KartPad's
four-platform relaunch waits for those checks.

Game inputs, generated game code, saves, keys, personal builds and optimization
profiles do not belong in this repository. A local-build workflow and a passing
scanner do not establish copyright clearance for source, dependencies or outputs.

Run the orchestration tests:

```sh
python3 -m unittest discover -s tests -v
```
