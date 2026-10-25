# Dungeon Delving (modpack)

A magic-focused NeoForge 1.21.1 modpack built around the [Dungeon Delving](https://github.com/Ranger3462/dungeon-delving)
mod: repeatable dungeon runs are the main way to progress, and the pack's magic mods are tuned around what you
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

The Dungeon Delving mod repository copies `kubejs/` and `config/` from this repository into its dev game folder
before the test client starts, as long as both repositories sit side by side (e.g. `GitHub/dwarven-vaults` and
`GitHub/dungeon-delving-pack`).

## License

Scripts and configuration are licensed under [LGPL-3.0](COPYING.LESSER). Art and other assets are All Rights
Reserved. See [LICENSE.md](LICENSE.md).

## Building and installing the alpha

The mod list for a release lives in `pack.json`: each mod's CurseForge project and file ids, plus the Dungeon Delving jar.
The mod repository's dev runs load the same files (CurseMaven in its `build.gradle`).

1. Build the mod: `./gradlew build` in the mod repository (the jar lands in `build/libs/`).
2. Build the pack: `python tools/export_curseforge.py`. It writes `dist/DungeonDelving-<version>-curseforge.zip`.

**To install:** in the CurseForge app, *My Modpacks > Create Custom Profile > Import*, and pick the zip. The app downloads
every mod from CurseForge and sets up NeoForge. Give the profile at least 6 GB of memory in its settings.

The tools that talk to CurseForge (`tools/curseforge.py`) go through the api.curse.tools mirror, which needs no key. To use
CurseForge's own API instead, set `CURSEFORGE_OFFICIAL=1` and a key in `CURSEFORGE_API_KEY`.

