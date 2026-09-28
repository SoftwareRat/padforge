# PadForge status and overnight run (28–29 Sep 2026)

Resumable record for the overnight goal loop. Source of truth for decisions and
per-repo state is the Notion "Public Repo Proprietary-Content Audit" and its
tracker; this file mirrors progress so work can resume after interruption.

**Window:** until 07:00 JST, 29 Sep 2026. Handoff starts 06:30.

## Rules for this run

- Nothing public may contain translated or decompiled game code, keys, disc/ROM
  images or extracted assets. A positive gate result is a stop.
- No releases, tags, uploads, AltStore changes, visibility changes, posts or
  comments. No deleting drafts, forks, repos, branches or history.
- Game repos are changed only in worktrees under `~/.codex/worktrees`. Primary
  checkouts with other agents' uncommitted work are not touched.
- Public game-repo PRs merge only for docs/manifest/wrapper/AGENTS changes whose
  tree passes the gate and the repo's own checks. Everything else stays a PR.
- Public READMEs do not mention PadForge while it is private.
- One heavy build at a time, none while another agent's build runs, `-j8` max.
  No new full build below 50 GB free; stop below 30 GB. Nothing is deleted for space.

## Levels

| Level | Meaning |
|---|---|
| L0 | Contained: affected downloads hidden |
| L1 | Docs accurate, dead release links fixed, gate rule present, source tree passes gate |
| L2 | Validated `padforge.json`; `padforge plan` succeeds |
| L3 | Source stages run through PadForge with verified outputs |
| L4 | Personal build through PadForge; gate rejects output as personal, passes source |
| L5 | Verified on a physical device (owner) |

## Log

- 23:49 Environment: BlueWake cold trained build compiling (other agent, read-only
  for this run); 71 GB free; load ~230. Active agents: BlueWake, YomiBoy.
- 23:55 PadForge PR #1 merged to `main` (`5361f33`); 26 tests pass.
- 00:10 Decisions + feasibility in `docs/DECISIONS.md` (iPhone module links
  without Apple SDK for one real chunk; Android host-neutral is conditional).
  Core on main `70de086`: manifests, catalog, list/doctor/check-manifest/audit,
  keyless gate (byte-identical results to the private gate), automatic gate on
  every personal output.
- 00:15 Owner decision: KartPad v0.1.0 and v0.2.0-preview.1 releases are still
  public and their tag source archives contain both Wii common keys (not acted on).
- 00:20 KartPad draft PR #336: build-it-yourself docs, retired links, common-key
  note, Builder stage events, padforge.json. Source gate FAILS on existing
  fixtures; `tests/fixtures/rel_report/function.cpp` shares all 3 labels and 11
  non-trivial lines with the translated game function (owner review).
- 00:25 `c21c595`: in-app inputs (no --disc), generic IPA check, MaskPad entry.
- 00:30 GoldenPad PR #38 merged (draft padforge.json, all targets planned).
  Sweep of 23 repos; retired-link PRs merged for HarkinianPad #27, SpaghettiPad
  #17, BrawlerPad #6, BearBirdPad #13, VaultPad #3; open for SunPad #49,
  MeleePad #34, AnnePad #7, CTRPad #40, GalaxyPad #15, SnapPad #7 (see Notion).
- 00:35 MaskPad fresh build through PadForge failed at configure on Xcode 27
  (upstream caches a 10.15 deployment target; Xcode 27 minimum iOS is 15.0).
  Fixed on the MaskPad branch; rebuild running.
- 00:45 HarkinianPad fork → patches: three patches against upstream Shipwright,
  libultraship and ZAPDTR reproduce the fork trees exactly; gate PASS.
  Draft PR #28 (decompiled context lines need owner policy).
- 00:47 MaskPad complete build through PadForge: 17m28s, exit 0, 17.7 MB personal
  IPA, gate FAIL on the IPA as expected, source PASS (draft PR #9, L4 on branch).
- 00:50 PadForge: `steps` manifests, per-step env, `padforge ui` (checked live).
- 00:55 L2 merged: StarshipPad #14, BrawlerPad #7, SpaghettiPad #18,
  DevilTouch #5, BellPad #15, BearBirdPad #14, BarrelPad #13, VaultPad #4.
  Manifests on open PRs: AnnePad #7, SnapPad #7, SunPad #49.
- 01:00 KartPad bootstrap verified; StarshipPad complete build running.
- 01:08 StarshipPad complete build through PadForge from main: 13m38s, exit 0,
  6.9 MB IPA, gate FAIL as expected → L4; manifest marked experimental (#15).
- 01:10–01:27 KartPad through PadForge: fixed two Builder bugs on #336
  (interrupted-bootstrap recovery; work-root vs shared download cache), then a
  complete build: 17m25s, exit 0, 64.8 MB IPA, provenance check passed, gate
  FAIL as intended, **no Wii key in the personal IPA** (confirms #335).
- 01:30 KartPad accepts other dumps after verified extraction (ISO and RVZ
  converted from the pinned WBFS pass; Wind Waker ISO refused). On #336.
- 01:30 Xcode 27 finding: iOS deployment target 14.0 fails CMake's
  try-compile. Affects MaskPad (#9) and HarkinianPad (#30, draft); all other
  ports target iOS 15+ (remaining 14.0/13.0/11.0 values are macOS targets).
- 01:33 Build queue (scratch runner): BrawlerPad running; then HarkinianPad
  (#30 branch), SpaghettiPad, BearBirdPad, DevilTouch, BellPad, BarrelPad,
  VaultPad, BallPad, BananaPad, AnnePad (#7), SnapPad (#7), DinoPad (#7).
- 01:40 BrawlerPad complete build from main (9m47s) → L4; manifest experimental.
- 01:54 HarkinianPad complete build on #30 (13m50s) → L4 on branch; from main
  it fails on Xcode 27, so #30 is required.
- 02:00 GoldenPad L2 blocker: pinned GoldenEye64Recomp fork lacks `us.toml` and
  the TLB-free patch; maintainer builds used a local upstream checkout.
- 02:10 `padforge history --repo` added. Clean engines' public IPAs all pass
  the gate.
- 02:14 SpaghettiPad complete build from main (19m55s) → L4; manifest experimental.
- 02:26 BearBirdPad complete build from main with the owner's ROM (11m48s) → L4.
- 02:28 BellPad complete build from main (1m27s) → L4. Its personal IPA *passes*
  the gate: decompilation code has named functions. Recorded as a gate limit.
- 02:28 Early failures fixed and re-queued: DevilTouch (Xcode 27 target; draft
  #6), BarrelPad (manifest used macOS /bin/bash 3.2; #14 merged), VaultPad
  (empty submodule in worktrees; #5 merged).
- 02:33 BallPad complete build from main (5m02s) → L4 (gate PASS, decompilation).
  Manifests marked experimental: BearBirdPad #15, BellPad #16, BallPad #8.
- 02:30 KartPad build-only Mac target added to #336 (queued for a real build).
- 02:37 BananaPad failed: PaperBoat's Torch submodule repo (JeodC/Torch-LH) was
  deleted upstream; pinned commit still in JeodC/Torch. Draft PaperBoat#1
  (URL only). Blocks fresh clones of PaperPad, BananaPad, SnapPad, DinoPad.
- 02:54–03:10 Fresh-build failures, all diagnosed and fixed on PR branches:
  AnnePad release audit list stale since 5 Aug (fix on #7, verified on the
  built core); SnapPad manifest missed host tools (#7); DinoPad manifest ran its
  safety check too early (#7); BarrelPad `clone-refs.sh` breaks under macOS
  bash 3.2 — the only bash on stock macOS (draft #15); VaultPad host build uses
  macOS 10.13, Xcode 27 needs 12.0+ (draft #6). All re-queued.
- Queue chain: DevilTouch (#6) → KartPad Mac target (#336) → AnnePad (#7) →
  SunPad (#49) → BarrelPad (#15), SnapPad (#7), DinoPad (#7) → VaultPad (#6).
- 03:10 DevilTouch complete build on #6 (6m06s) → L4 on branch (gate PASS).
- 03:15 KartPad Mac target stopped on a missing macOS Dawn archive that
  bootstrap never fetched; fixed on #336 (`217aa57`, hash from the lock).
  AnnePad fix commit had landed on a detached HEAD; recovered and pushed
  (`26ccdd2`). AnnePad patches fetched deps in place (rebuild blocker; noted).
  Re-queued after VaultPad: AnnePad, KartPad Mac.

## Level snapshot (01:00)

| Level | Repos |
|---|---|
| L4 (branch) | MaskPad (#9 unmerged) |
| L2 | StarshipPad, BrawlerPad, SpaghettiPad, DevilTouch, BellPad, BearBirdPad, BarrelPad, VaultPad |
| L1 | GoldenPad, HarkinianPad, PaperPad, BallPad, BananaPad, DinoPad, UTP |
| L0, PR open | KartPad #336, SunPad #49, MeleePad #34, AnnePad #7, CTRPad #40, GalaxyPad #15, SnapPad #7 |
| L0, gate policy | KartPad, GalaxyPad, SnapPad, F0X |

## Repo queue

1. PadForge core  2. KartPad  3. MaskPad  4. GoldenPad  5. HarkinianPad
6. StarshipPad, BrawlerPad, F0X  7. MeleePad (review only)  8. SunPad, GalaxyPad,
AnnePad, BearBirdPad, SnapPad, BananaPad, BarrelPad, DinoPad  9. SpaghettiPad,
PaperPad, BellPad, BallPad, DevilTouch  10. VaultPad, UTP  11. CTRPad (private,
PR only)  12. Clean engines  13. Supporting repos (status only)

## Owner decisions pending

1. **KartPad keys in two still-public releases:** v0.1.0 and v0.2.0-preview.1
   are published; their tag source archives contain both Wii common keys.
   Drafting them is reversible; tags/history stay downloadable either way.
2. **Gate policy for references to game functions** (the gate has no exemptions):
   KartPad guard skeleton + synthetic tests + log/record markers; SnapPad test
   stub; GalaxyPad signature anchors in scripts; F0X and HarkinianPad
   (PR #28) decompiled context lines inside patches.
3. **MaskPad iOS 15 minimum** (Xcode 27 cannot target 14): merge PR #9.
4. **Runtime-only public apps:** feasible in principle (S1); BlueWake, SunPad
   and MeleePad already separate app and game module. Publishing is your call.
5. **Make PadForge public** (public READMEs cannot point to it until then).
6. Existing: delete the 157 drafts; retire forks; history rewrites.

## Merge queue (PRs that need an owner or a bootstrapped check)

KartPad #336 · MaskPad #9 · HarkinianPad #28 · SunPad #49 · MeleePad #34 ·
AnnePad #7 · SnapPad #7 · GalaxyPad #15 · CTRPad #40 · BlueWake #2
