# Dungeon Delving (modpack)

A magic-focused NeoForge 1.21.1 modpack built around the [Dungeon Delving](https://github.com/Dunedain-Ranger-Dev/dungeon-delving)
mod and its sister mods, [Professions and Skills](https://github.com/Dunedain-Ranger-Dev/professions-and-skills),
[Kingdom Sim](https://github.com/Dunedain-Ranger-Dev/kingdom-sim) and [Deep Mines](https://github.com/Dunedain-Ranger-Dev/deep-mines): repeatable dungeon runs are the main way to progress, and the pack's magic mods are tuned around what you
bring back.

This repository holds the pack's own content, not the mods themselves:

| Folder | What's in it |
|---|---|
| `kubejs/server_scripts/` | Recipe changes, e.g. dungeon ores in magic mod recipes |
| `kubejs/data/` | Data overrides loaded as a data pack, e.g. loot and world generation changes |
| `config/` | Config overrides for the pack's mods |
| `tools/` | Scripts that generate the `kubejs/data/` files, e.g. `dungeon_only_resources.py` |
| [MODS.md](MODS.md) | The mod list, with the exact versions used |

## Testing in development

`dev/` is a small Gradle project that plays the whole pack: our four mods built from source (their repositories checked
out next to this one, e.g. `GitHub/dungeon-delving`, `GitHub/professions-and-skills`, `GitHub/kingdom-sim` and
`GitHub/deep-mines`), every other mod at its `pack.json` version, and this repository's `kubejs/` and `config/`, copied
into the dev game folder `dev/run/` before it starts. From `dev/`: `./gradlew runClient` to play,
`./gradlew runGameTestServer` to run every mod's game tests with the full pack. Each mod's own repository can also run
on its own, with just the mods it works with.

## License

Scripts and configuration are licensed under [LGPL-3.0](COPYING.LESSER). Art and other assets are All Rights
Reserved. See [LICENSE.md](LICENSE.md).

## Building and installing the alpha

The mod list for a release lives in `pack.json`: each mod's CurseForge project and file ids, plus our own mods' jars
(Dungeon Delving, Professions and Skills, Kingdom Sim and Deep Mines, each built in its own repository next to this one).
The dev project loads the same files (CurseMaven in `dev/build.gradle`).

1. Build our mods: `./gradlew build` in each of our four mod repositories (each jar lands in its `build/libs/`).
2. Build the pack: `python tools/export_curseforge.py`. It writes `dist/DungeonDelving-<version>-curseforge.zip`.

**To install:** in the CurseForge app, *My Modpacks > Create Custom Profile > Import*, and pick the zip. The app downloads
every mod from CurseForge and sets up NeoForge. Give the profile at least 6 GB of memory in its settings.

The tools that talk to CurseForge (`tools/curseforge.py`) go through the api.curse.tools mirror, which needs no key. To use
CurseForge's own API instead, set `CURSEFORGE_OFFICIAL=1` and a key in `CURSEFORGE_API_KEY`.

