# PadForge

Build your own copy of a game port on your own Mac, from your own game disc or ROM.

PadForge is the shared Builder for the *Pad ports (KartPad, BlueWake, SunPad, StarshipPad and others). The ports publish only their own code. PadForge combines that code with the game you own, on your computer, and gives you an app for your iPhone, iPad, Mac or Android device. Nothing it builds is ever uploaded.

> **Status: planning.** The first working Builder is being developed in the BlueWake repository (`scripts/builder/`) and will move here. Nothing in this repository is usable yet.

## How it will work

1. Install PadForge on a Mac (command line first; a Mac app later).
2. Choose a game and point PadForge at your own disc image or ROM.
3. PadForge checks that it is a supported copy, then builds the game part on your Mac. For some games this takes a few hours the first time; later app updates reuse it.
4. It installs the app on a connected iPhone or iPad, or writes a personal IPA, APK or Mac app for you to sign and install yourself.

## What PadForge never does

- It never includes game code, disc images, ROMs, extracted game files, saves or console keys, in this repository or in any release.
- It never uploads anything it builds. Your personal build is for you only; don't share it.

## Two kinds of game profile

Each port plugs in a small profile describing its game.

| Kind | Where the game code comes from | Ports |
| --- | --- | --- |
| Disc translation (static recompilation) | Translated from your own disc during the build | KartPad, BlueWake, SunPad, GalaxyPad, GoldenPad, AnnePad, BearBirdPad, SnapPad, BananaPad, BarrelPad, DinoPad |
| Decompilation | Fetched from the original decompilation project at a pinned commit, with the port's own patches applied; art and sound come from your ROM or disc | HarkinianPad, SpaghettiPad, MaskPad, StarshipPad, PaperPad, F0X, BrawlerPad, BellPad, BallPad, DevilTouch, CTRPad |

## Platforms

- **Mac:** builds iPhone and iPad apps, Mac apps and Android apps.
- **Windows (later):** Android apps only. Building iPhone and iPad apps requires Apple's Xcode, which runs only on a Mac.

## Builder contract

Every profile must:

1. accept only verified game copies (disc ID and revision, or exact file hashes) and refuse everything else with a clear message;
2. pin every translator, runtime and dependency by commit or checksum;
3. check the generated game source against a recorded digest before the long compile;
4. produce a personal build containing only the app and the player's own game module and files, audited before packaging and written only to ignored paths;
5. record provenance (profile, source commit, digests) with the build for bug reports;
6. never be published: the release check must fail on any personal build. Public releases contain source and notices only.

