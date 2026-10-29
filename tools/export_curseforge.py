"""Builds the installable modpack: dist/DungeonDelving-<version>-curseforge.zip (the CurseForge modpack format).

Run from the pack repository root: python tools/export_curseforge.py

- Every mod in pack.json's "curseforge" list is in manifest.json by its CurseForge project and file id: the CurseForge
  app downloads them itself, so the zip only carries what's ours.
- Our own mods' jars (pack.json "mod_jars": Dungeon Delving, Professions and Skills, Kingdom Sim and Deep Mines, each
  built in its own repository next to this one with ./gradlew build) and the pack's kubejs/ and config/ folders go in as overrides.
- Each mod's file is checked against CurseForge first (it must exist, and be that mod's file), through the API in
  tools/curseforge.py.

Import it in the CurseForge app: My Modpacks > Create Custom Profile > Import.
"""
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import curseforge  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OVERRIDE_FOLDERS = ["kubejs", "config"]
SKIP_NAMES = {"README.md", ".gitkeep"}


def check(mods):
    """Every pinned file exists on CurseForge and belongs to its project."""
    files = curseforge.call("/mods/files", {"fileIds": [entry["file"] for entry in mods.values()]})["data"]
    found = {f["id"]: f for f in files}
    for slug, entry in mods.items():
        file = found.get(entry["file"])
        if file is None or file["modId"] != entry["project"]:
            sys.exit(f"{slug}: file {entry['file']} isn't project {entry['project']}'s on CurseForge")
        print(f"  {slug} {file['fileName']}")


def main():
    pack = json.loads((ROOT / "pack.json").read_text(encoding="utf-8"))
    mod_jars = [(ROOT / jar).resolve() for jar in pack["mod_jars"]]
    for jar in mod_jars:
        if not jar.is_file():
            sys.exit(f"{jar} not found; run ./gradlew build in its project first")
    mods = pack["curseforge"]
    check(mods)

    manifest = {
        "minecraft": {"version": pack["minecraft"], "modLoaders": [{"id": f"neoforge-{pack['neoforge']}", "primary": True}]},
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": pack["name"],
        "version": pack["version"],
        "author": "Ranger3462",
        "files": [{"projectID": entry["project"], "fileID": entry["file"], "required": True} for entry in mods.values()],
        "overrides": "overrides",
    }

    out = ROOT / "dist" / f"{pack['name'].replace(' ', '')}-{pack['version']}-curseforge.zip"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        for jar in mod_jars:
            archive.write(jar, f"overrides/mods/{jar.name}")
        for folder in OVERRIDE_FOLDERS:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file() and path.name not in SKIP_NAMES:
                    archive.write(path, "overrides/" + path.relative_to(ROOT).as_posix())
    ours = ", ".join(jar.name for jar in mod_jars)
    print(f"Wrote {out.relative_to(ROOT)} ({len(mods)} CurseForge mods + {ours}, {out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
