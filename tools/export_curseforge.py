"""Builds a CurseForge app profile: dist/DungeonDelving-<version>-curseforge.zip.

Run from the pack repository root: python tools/export_curseforge.py

The CurseForge app imports this zip (Create Custom Profile > Import). It's the CurseForge modpack format (a
manifest.json and an overrides/ folder), but every mod comes inside it rather than as a CurseForge project id: the
pack's mods are pinned on Modrinth (pack.json "modrinth"), and matching them to CurseForge needs its API key. So this
is for our own installs and testers, not for publishing on CurseForge. Use tools/export_mrpack.py for Prism Launcher or
the Modrinth App.

- Every mod in pack.json's "modrinth" list is downloaded from Modrinth (cached in dist/cache/) and checked against its
  sha1.
- Mods that aren't on Modrinth (pack.json "bundled_jars": FTB Quests and its libraries) come from the mod
  repository's Gradle cache, so run a dev build there first.
- The Dungeon Delving jar (pack.json "mod_jar", built in the mod repository with ./gradlew build) and the pack's
  kubejs/ and config/ folders go in too.
"""
import glob
import hashlib
import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_mrpack import OVERRIDE_FOLDERS, ROOT, SKIP_NAMES, pack_file  # noqa: E402

CACHE = ROOT / "dist" / "cache"


def download(entry):
    """The jar for a modrinth.index.json entry, from the cache or Modrinth."""
    path = CACHE / Path(entry["path"]).name
    if not path.is_file() or hashlib.sha1(path.read_bytes()).hexdigest() != entry["hashes"]["sha1"]:
        request = urllib.request.Request(entry["downloads"][0], headers={"User-Agent": "Ranger3462/dungeon-delving-pack (export_curseforge.py)"})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
        if hashlib.sha1(data).hexdigest() != entry["hashes"]["sha1"]:
            sys.exit(f"{path.name}: the download doesn't match its sha1")
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return path


def main():
    pack = json.loads((ROOT / "pack.json").read_text(encoding="utf-8"))
    mod_jar = (ROOT / pack["mod_jar"]).resolve()
    if not mod_jar.is_file():
        sys.exit(f"Dungeon Delving jar not found at {mod_jar}; run ./gradlew build in the mod repository first")

    jars = []
    for slug, version_id in pack["modrinth"].items():
        entry, label = pack_file(slug, version_id, pack["minecraft"])
        jars.append(download(entry))
        print("  " + label)

    for pattern in pack.get("bundled_jars", []):
        found = sorted(glob.glob(os.path.expanduser(pattern)))
        if not found:
            sys.exit(f"Not found: {pattern} (run a dev build in the mod repository to fetch it)")
        jars.append(Path(found[-1]))
        print("  " + Path(found[-1]).name + " (bundled)")

    manifest = {
        "minecraft": {"version": pack["minecraft"], "modLoaders": [{"id": f"neoforge-{pack['neoforge']}", "primary": True}]},
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": pack["name"],
        "version": pack["version"],
        "author": "Ranger3462",
        "files": [],
        "overrides": "overrides",
    }

    out = ROOT / "dist" / f"{pack['name'].replace(' ', '')}-{pack['version']}-curseforge.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        archive.write(mod_jar, f"overrides/mods/{mod_jar.name}")
        for jar in jars:
            archive.write(jar, f"overrides/mods/{jar.name}")
        for folder in OVERRIDE_FOLDERS:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file() and path.name not in SKIP_NAMES:
                    archive.write(path, "overrides/" + path.relative_to(ROOT).as_posix())
    print(f"Wrote {out.relative_to(ROOT)} ({len(jars)} mods + {mod_jar.name}, {out.stat().st_size // (1024 * 1024)} MB)")


if __name__ == "__main__":
    main()
