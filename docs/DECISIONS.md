# PadForge decisions

Recorded 29 Sep 2026 during the overnight run. Evidence is from this Mac; items
marked *unverified* have not been demonstrated. Scanner results and build
feasibility are technical findings, not copyright or licensing clearance.

## D1. Command line first; the GUI is a thin layer over the same engine

- **Engine:** the Python CLI (`python3 -m padforge`). Python runs on macOS,
  Windows and Linux, needs no packages, and already implements locking,
  progress relay, cancellation and build records.
- **First GUI:** `padforge ui`, a local browser page served by Python's standard
  library on `127.0.0.1`, reading the same `progress.jsonl` events. No Electron,
  Tauri or native toolkit, so there is nothing extra to sign or notarize per OS.
- **Later:** a downloadable one-file bundle (`.dmg`/`.exe`/AppImage) once a
  complete build works through the CLI and players need a no-Python install.
- **Why:** one engine for all three operating systems; the interface cannot
  drift from what the CLI actually does; the expensive part (tool setup and
  multi-hour builds) is the same either way.
- **Implemented 29 Sep:** `python3 -m padforge ui` serves the page on
  `127.0.0.1` with a random token and a Host check, runs `doctor`/`plan` in
  process and starts builds as `python3 -m padforge build` subprocesses (one at
  a time, cancellable), showing stages from the same events. Checked in the
  in-app browser against StarshipPad: current commit, doctor Ready, plan steps.

## D4. Manifests may list existing scripts as ordered steps

A target declares either one `command` (with optional modes/options) or
`steps` (stage name + argument list). PadForge runs steps in order, emits the
stage events itself, rechecks the checkout before each step and stops at the
first failure. Most ports already have working scripts, so adding a game is a
manifest-only change rather than a new wrapper in every repository.

## D2. Games plug in through a manifest they own

- Each game repository owns `padforge.json` (schema in
  [`padforge/manifest.py`](../padforge/manifest.py)): identity, kind, accepted
  inputs, host/target matrix with per-cell status, entry commands, stages,
  output checks and publication policy.
- PadForge's catalog (`catalog/*.json`) pins each supported game to a
  repository URL and a reviewed commit. Adding a game = manifest in its repo +
  one catalog entry. Game-specific translation, patches and packaging stay in
  the game repository; PadForge does not copy them.
- Kinds: `disc-translation` (static recompilation), `emulator-shell`,
  `decomp-patches` (fetch upstream decompilation, apply own patches),
  `upstream-engine` (fetch other projects' engines), `clean-engine`.

## D3. PadForge is the home of the compliance gate

- `padforge audit <path>` runs the release gate (copied from the private
  `~/.codex/release-gate/release_gate.py`, which remains the reference until the
  owner retires it). Every PadForge package step runs it automatically and
  records the result: personal builds must be labeled *personal, not
  publishable*; source archives must pass.
- A gate failure on anything intended for publication is a stop.
- **Limit found 29 Sep:** the gate recognizes translated code by address-named
  symbols, keys, section markers and provenance. Decompilation ports compile
  named functions, so their personal apps can PASS (BellPad: 0 symbols). For
  those ports, `publication.public_binaries: false` in the manifest is the
  safeguard; a gate PASS is never permission to publish a decompilation build.

## D5. One release formula for every game (owner decision, 29 Sep 2026)

Nothing containing game code, disc data or keys is published. Everything else
is, in the same shape for every repo and every update: one version (the repo's
`version.json`), assets named `<Game>-vX.Y.Z-...`, and `SHA256SUMS`.

| Kind | Published | Player uses PadForge to |
|---|---|---|
| No game code (clean engines) | Full APK/IPA | Nothing |
| Translated code (KartPad, BlueWake, SunPad...) | Empty app + recipe | Build the game pack from their own disc |
| Decompilation (HarkinianPad, MaskPad...) | Recipe only | Build the whole app from public source + their ROM |

Why: the translated or decompiled game code is the only part that cannot be
shared; splitting it out keeps everything else a normal download with normal
in-place updates. On Android the empty app keeps the owner's signing key and
loads the pack from its own storage, so updates and saves are unaffected.
Translated ports share three recipes (WiiCompiled, Dolphin/DolRecomp,
N64Recomp+RT64) instead of one per repo. PadForge is one app for every game,
released on its own schedule.

## D6. The player's computer builds only the game pack (29 Sep 2026)

With D5, a player's Windows, Mac or Linux computer never builds the app itself.
For a translated-code game it extracts the disc, translates it, and compiles
one library against the published app's runtime:

- Android: the Android NDK's compiler, CMake and Ninja. No Gradle, Java or
  Android SDK. The player copies the pack to the phone and picks it in the app;
  it loads from the app's own storage.
- iPhone: the pack is a dylib that PadForge puts inside the empty IPA
  (`Frameworks/`); the player's sideloading tool signs the IPA as usual.

Why: it is the smallest toolset that works on all three systems, and the
published app, its signing and its updates stay the owner's.

Rule for every game pack (learned on KartPad): runtime state that lives in
headers (C++ `inline` variables, including `thread_local` ones and statics
inside inline functions) must exist once, in the app. A pack compiled with its
own copies runs, but reads state the app never sets (KartPad's first pack
aborted with "CurrentCpuContext is NULL"). The runtime declares such variables
`extern` when `MKW_GAME_PACK_MODULE` is set, and the app references each one
so it is always exported. Check for regressions by listing data symbols that
both the pack and the app define; the answer must be none (a pure lookup cache
is the only allowed exception).

## S1. iPhone/iPad module without Xcode or Apple's SDK: plausible, partly verified

Test (BlueWake, private scratch, nothing committed): one real translated chunk
(1.47 MB C source) plus all eight runtime/export sources of the game module were
compiled with Homebrew's open-source clang 22 for `arm64-apple-ios17.0` using
`-nostdlibinc` and a 5-file header shim of standard C prototypes written for
the test. Only 11 C-library symbols are needed from the system. `ld64.lld`
linked them against a hand-written 13-symbol `libSystem.tbd` stub into an iOS
Mach-O dylib: platform iOS, min 17.0, only `/usr/lib/libSystem.B.dylib`
loaded (same as the Xcode-built module), exporting `staticrecomp_get_module`
and `staticrecomp_get_rel_data`. Ad-hoc signing and `codesign --verify --strict`
passed. The chunk took 244 s at -O2 under load ~230.

What this means: BlueWake's iOS app already loads the game from
`Frameworks/gGZLE01_recomp.dylib` at runtime. A runtime-only app (the gate
passes BlueWake's app without that file) plus a module built on the player's
computer with LLVM (available for Windows, Linux and macOS), inserted before
signing with Sideloadly/AltStore/SideStore or `zsign`, would let Windows and
Linux users make iPhone builds without Xcode.

Unverified: a complete 808-unit module linked this way; loading it on a device;
whether the translator (DolRecomp) and training host build on Windows/Linux;
local optimization training off macOS. KartPad does **not** have this split
today: its translated C++ is linked statically into the app
(`add_library(kartpad_g7_translated STATIC)`), so it needs a module refactor
first. Publishing a runtime-only IPA/APK is an owner decision.

Later the same night: SunPad already works this way in development. Its app
loads `gGMSE01_recomp.dylib` from the app container, generated locally by
`scripts/ios-build-core-device.sh` and provisioned separately from the app
(`docs/BUILDING.md`). So two of the static-recompilation ports (BlueWake,
SunPad) already separate the game module from the app. For sideloading, the
module would ship inside the IPA's `Frameworks/` so the signing tool re-signs
it with the app.

MeleePad goes further: its retired Preview 7 shipped an unsigned *module-free*
IPA shell, with the game module generated locally from the player's disc
(`docs/FAQ.md`). The audit recorded that shell as publishable once Dolphin's
common keys are removed. So three ports (BlueWake, SunPad, MeleePad) already
separate the app from the game module, which is the design a runtime-only
public app would need.

## S2. Android builds from Linux/Windows: conditional yes

KartPad's Android build reuses the same translation output as iOS and uses
cross-platform tools (Gradle, NDK, CMake, .NET 8 translator, Python). It is
deliberately locked to Apple Silicon macOS by `scripts/check-android-host.sh`
(`uname` check), plus Mac-specific paths: JDK `Contents/Home`, NDK
`prebuilt/darwin-x86_64`, Homebrew `dotnet@8`. The host check also requires the
emulator and system images, which a build does not need. Estimated work:
host-neutral paths and a build-only host check; Windows via WSL2 for the bash
scripts. Not built on Linux/Windows tonight (Docker daemon not running; the Mac
was under another agent's build).

Concrete plan (surveyed 29 Sep, not implemented): the Mac assumptions sit in
about 15 `scripts/*android*.sh` files and follow four patterns. Add one sourced
helper, `scripts/android-host.sh`, that sets per host: `JAVA_HOME`
(`.android-bootstrap/jdk-*/Contents/Home` on macOS, `jdk-*` on Linux), the
default SDK root (`~/Library/Android/sdk` vs `~/Android/Sdk`), the NDK prebuilt
directory (`darwin-x86_64` vs `linux-x86_64`) and a `sha256` function
(`shasum -a 256` vs `sha256sum`). Pin a second Temurin JDK archive and
SHA-256 for linux-x64 in `android-toolchain-versions.sh` and select it in
`bootstrap-android-host.sh`. Split `check-android-host.sh` into build
requirements (SDK platform, build-tools, NDK, CMake, JDK) and device/emulator
extras, and accept `Linux x86_64` for builds. Verify first on a Linux x86_64
machine or container, then Windows through WSL2.

## S3. Runtime-only APK plus player module

**Verified 29 Sep 2026 (emulator, Android 16 / API 36, targetSdk 36):** an app
copied a native library into its private `files/` directory and loaded it with
`System.load`. That library depended on a library shipped in the APK, its static
registrar called into the host library at load time, and JNI calls in both
directions worked (`PACKPROBE OK ... registered=42 value=70`). This is the
KartPad game-pack pattern, so the empty APK can keep the owner's signing key and
normal in-place updates. The re-signing route below is no longer needed for
Android.

Android 10+ restricts executing code from an app's writable data directory for
apps targeting API 29+; whether `dlopen` from app storage is reliable is
*unverified* and not relied on. Preferred route mirrors iPhone: insert the
player's module into the runtime APK's `lib/arm64-v8a/` on the computer, then
zipalign and sign with a key generated on that machine (`apksigner`,
cross-platform). Requires the same module split as S1.

## Resulting direction

1. Now: Mac builds everything (iPhone/iPad, Mac, Android) through PadForge.
2. Next: host-neutral Android builds (Linux, then Windows via WSL2).
3. Then, owner decision: runtime-only public apps plus player-built modules,
   starting with BlueWake (already split), then KartPad after a module refactor.
