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

## Repo queue

1. PadForge core  2. KartPad  3. MaskPad  4. GoldenPad  5. HarkinianPad
6. StarshipPad, BrawlerPad, F0X  7. MeleePad (review only)  8. SunPad, GalaxyPad,
AnnePad, BearBirdPad, SnapPad, BananaPad, BarrelPad, DinoPad  9. SpaghettiPad,
PaperPad, BellPad, BallPad, DevilTouch  10. VaultPad, UTP  11. CTRPad (private,
PR only)  12. Clean engines  13. Supporting repos (status only)

## Owner decisions pending

- Publish a runtime-only IPA/APK (depends on feasibility results).
- Make PadForge public.
- Delete the 157 drafts; retire forks; history rewrites.
